# -*- coding: utf-8 -*-
"""
X-Minute City Index - Integrated Toolbox (Stable Version)
Combines Service Area Analysis + XMCI Calculation
Fixes: Memory Leaks, Cursor Locks, Extension Management
"""

import arcpy
import math
import os
import gc  # Added for Garbage Collection

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the .pyt file)."""
        self.label = "X-Minute City Index Toolbox"
        self.alias = "XMinuteCityIndex"
        self.tools = [XMinuteCityAnalysis]

class XMinuteCityAnalysis(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "X-Minute City Analysis"
        self.description = "Integrated tool for calculating X-Minute City Index combining Service Area analysis and XMCI metrics"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        
        # Parameter 0: Network Dataset
        param0 = arcpy.Parameter(
            displayName="Network Dataset",
            name="network_data",
            datatype="GPNetworkDatasetLayer",
            parameterType="Required",
            direction="Input")
        
        # Parameter 1: Travel Mode (Dynamic list from Network Dataset)
        param1 = arcpy.Parameter(
            displayName="Travel Mode",
            name="travel_mode",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param1.filter.type = "ValueList"
        param1.filter.list = []
        
        # Parameter 2: Cutoffs (minutes)
        param2 = arcpy.Parameter(
            displayName="Cutoffs (minutes)",
            name="cutoffs",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param2.value = "15"
        
        # Parameter 3: Hexagon Layer
        param3 = arcpy.Parameter(
            displayName="Hexagon Grid Layer",
            name="hexagon_layer",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param3.filter.list = ["Polygon"]
        
        # Parameter 4: POIs Layer
        param4 = arcpy.Parameter(
            displayName="Points of Interest (POIs)",
            name="pois_layer",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param4.filter.list = ["Point"]
        
        # Parameter 5: POI Category Field
        param5 = arcpy.Parameter(
            displayName="POI Category Field",
            name="category_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param5.parameterDependencies = [param4.name]
        
        # Parameter 6: Population Field
        param6 = arcpy.Parameter(
            displayName="Population Field (in Hexagon Layer)",
            name="pop_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param6.parameterDependencies = [param3.name]
        
        # Parameter 7: POI Fields for Analysis (MultiValue) - Dynamic from Category Field
        param7 = arcpy.Parameter(
            displayName="POI Category Fields (Select categories for analysis)",
            name="selected_fields",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            multiValue=True)
        
        # Parameter 8: Accessibility Weight
        param8 = arcpy.Parameter(
            displayName="Accessibility Weight",
            name="weight_access",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param8.value = 0.5
        
        # Parameter 9: Diversity Weight
        param9 = arcpy.Parameter(
            displayName="Diversity Weight",
            name="weight_div",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param9.value = 0.5
        
        # Parameter 10: Output Feature Dataset (for intermediate feature classes)
        param10 = arcpy.Parameter(
            displayName="Output Feature Dataset",
            name="feature_dataset",
            datatype="DEFeatureDataset",
            parameterType="Required",
            direction="Input")
        
        # Parameter 11: Output Geodatabase (for tables)
        param11 = arcpy.Parameter(
            displayName="Output Geodatabase",
            name="output_geodatabase",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")
        
        # Parameter 12: Output Folder (for DBF and text file)
        param12 = arcpy.Parameter(
            displayName="Output Folder (for temporary files)",
            name="output_folder",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        
        params = [param0, param1, param2, param3, param4, param5, param6, 
                  param7, param8, param9, param10, param11, param12]
        
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return arcpy.CheckExtension("network") == "Available"

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal validation is performed."""
        
        # Populate Travel Modes dynamically from Network Dataset
        if parameters[0].altered and parameters[0].value:
            try:
                network_dataset = parameters[0].valueAsText
                try:
                    import arcpy.nax as nax
                    travel_modes = nax.GetTravelModes(network_dataset)
                    travel_mode_names = list(travel_modes.keys())
                except:
                    nd_desc = arcpy.Describe(network_dataset)
                    travel_mode_names = []
                    if hasattr(nd_desc, 'travelModes'):
                        for tm in nd_desc.travelModes:
                            travel_mode_names.append(tm.name)
                
                if not travel_mode_names:
                    travel_mode_names = ["Walking Time", "Driving Time", "Trucking Time"]
                
                parameters[1].filter.list = travel_mode_names
                if not parameters[1].value and travel_mode_names:
                    parameters[1].value = travel_mode_names[0]
                    
            except Exception:
                pass # Silent fail in validation to avoid annoyance
        
        # Populate POI Category Fields dynamically
        if parameters[4].altered and parameters[5].altered and parameters[4].value and parameters[5].value:
            try:
                pois_layer = parameters[4].valueAsText
                category_field = parameters[5].valueAsText
                unique_categories = set()
                
                # Use a try-except block specifically for the cursor in validation
                try:
                    with arcpy.da.SearchCursor(pois_layer, [category_field]) as cursor:
                        for row in cursor:
                            if row[0] is not None:
                                category_value = str(row[0]).strip()
                                if category_value:
                                    unique_categories.add(category_value)
                    # Explicit cleanup
                    del cursor
                except:
                    pass

                category_list = sorted(list(unique_categories))
                if category_list:
                    parameters[7].filter.type = "ValueList"
                    parameters[7].filter.list = category_list
                    if not parameters[7].altered:
                        parameters[7].values = category_list
            except Exception:
                pass
        return

    def updateMessages(self, parameters):
        if parameters[8].value and parameters[9].value:
            weight_access = float(parameters[8].value)
            weight_div = float(parameters[9].value)
            if weight_access <= 0 or weight_div <= 0:
                parameters[8].setErrorMessage("Weights must be greater than 0")
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        
        # Get parameters
        network_data = parameters[0].valueAsText
        travel_mode = parameters[1].valueAsText
        cutoffs = parameters[2].valueAsText
        hexagon_layer = parameters[3].valueAsText
        pois_layer = parameters[4].valueAsText
        category_field = parameters[5].valueAsText
        pop_field = parameters[6].valueAsText
        selected_fields = parameters[7].valueAsText.split(';')
        weight_access = float(parameters[8].value)
        weight_div = float(parameters[9].value)
        feature_dataset = parameters[10].valueAsText
        output_geodatabase = parameters[11].valueAsText
        output_folder = parameters[12].valueAsText
        
        output_fc = os.path.join(feature_dataset, "XMCI")
        output_txt = os.path.join(output_folder, "XMCI for City.txt")
        
        # Set environment
        arcpy.env.overwriteOutput = True
        arcpy.env.scratchWorkspace = output_geodatabase
        arcpy.env.workspace = output_geodatabase
        
        # Disable auto-adding to map to prevent rendering crash during processing
        # Users can add layers manually later
        arcpy.env.addOutputsToMap = False 
        
        arcpy.AddMessage("="*60)
        arcpy.AddMessage("X-MINUTE CITY INDEX ANALYSIS")
        arcpy.AddMessage("="*60)

        try:
            if arcpy.CheckExtension("network") == "Available":
                arcpy.CheckOutExtension("network")
            else:
                arcpy.AddError("Network Analyst extension is not available")
                return
            
            # ========== PHASE 1: SERVICE AREA ANALYSIS ==========
            arcpy.AddMessage("\n### PHASE 1: Service Area Analysis ###")
            
            arcpy.AddMessage("Step 1.1: Creating Service Area layer...")
            sa_layer_obj = arcpy.na.MakeServiceAreaAnalysisLayer(
                network_data_source=network_data,
                travel_mode=travel_mode,
                cutoffs=cutoffs,
                travel_direction="FROM_FACILITIES"
            )
            sa_layer = sa_layer_obj[0]
            
            arcpy.AddMessage("Step 1.2: Creating hexagon centroids...")
            centers_fc = os.path.join(feature_dataset, "Hexagon_Centroid")
            arcpy.management.FeatureToPoint(
                in_features=hexagon_layer,
                out_feature_class=centers_fc,
                point_location="INSIDE"
            )
            
            arcpy.AddMessage("Step 1.3: Adding facilities...")
            arcpy.na.AddLocations(
                in_network_analysis_layer=sa_layer,
                sub_layer="Facilities",
                in_table=centers_fc,
                field_mappings="Name OBJECTID #",
                search_tolerance="500 Meters"
            )
            
            arcpy.AddMessage("Step 1.4: Solving Service Area...")
            arcpy.na.Solve(sa_layer)
            
            arcpy.AddMessage("Step 1.5: Extracting isochrone polygons...")
            sa_isochrone = os.path.join(feature_dataset, "SA_Isochrone")
            
            desc = arcpy.Describe(sa_layer)
            layer_name = desc.nameString
            polygons_layer = layer_name + "\\Polygons"
            arcpy.management.CopyFeatures(polygons_layer, sa_isochrone)
            
            # Explicitly clear the NA layer to free memory
            del sa_layer
            del sa_layer_obj
            gc.collect()

            arcpy.AddMessage("Step 1.6: Intersecting isochrones with POIs...")
            sa_intersect = os.path.join(feature_dataset, "SA_Iso_Intersect")
            arcpy.analysis.PairwiseIntersect(
                in_features=[sa_isochrone, pois_layer],
                out_feature_class=sa_intersect
            )
            
            arcpy.AddMessage("Step 1.7: Calculating summary statistics...")
            sa_statistics = os.path.join(output_geodatabase, "SA_Iso_Statistics")
            arcpy.analysis.Statistics(
                in_table=sa_intersect,
                out_table=sa_statistics,
                statistics_fields=[["OBJECTID", "COUNT"]],
                case_field=["FacilityID", category_field]
            )
            
            arcpy.AddMessage("Step 1.8: Creating pivot table...")
            pivot_table_dbf = os.path.join(output_folder, "PivotTable.dbf")
            arcpy.management.PivotTable(
                in_table=sa_statistics,
                fields=["FacilityID"],
                pivot_field=category_field,
                value_field="FREQUENCY",
                out_table=pivot_table_dbf
            )
            
            # Force cleanup before Join
            gc.collect()

            arcpy.AddMessage("Step 1.9: Joining pivot table to hexagon layer...")
            pivot_fields = [f.name for f in arcpy.ListFields(pivot_table_dbf) 
                           if f.type in ['SmallInteger', 'Integer', 'Single', 'Double'] 
                           and f.name.upper() not in ['OBJECTID', 'OID', 'FID', 'FACILITYID']]
            
            hexagon_temp = os.path.join(feature_dataset, "Hexagon_Temp")
            arcpy.management.CopyFeatures(hexagon_layer, hexagon_temp)
            
            arcpy.management.JoinField(
                in_data=hexagon_temp,
                in_field="OBJECTID",
                join_table=pivot_table_dbf,
                join_field="FacilityID",
                fields=pivot_fields
            )
            
            # ========== PHASE 2: XMCI CALCULATION ==========
            arcpy.AddMessage("\n### PHASE 2: XMCI Calculation ###")
            
            arcpy.management.CopyFeatures(hexagon_temp, output_fc)
            
            # Verify fields
            output_fields = [f.name for f in arcpy.ListFields(output_fc)]
            valid_selected_fields = []
            for field in selected_fields:
                field_clean = field.strip()
                if field_clean in output_fields:
                    valid_selected_fields.append(field_clean)
            
            if not valid_selected_fields:
                arcpy.AddError("No valid POI category fields found.")
                return

            # --- Calculation with Explicit Memory Management ---
            
            arcpy.AddMessage("Step 2.1: Processing NULL values...")
            with arcpy.da.UpdateCursor(output_fc, valid_selected_fields) as cursor:
                for row in cursor:
                    new_row = [0 if val is None else val for val in row]
                    if new_row != list(row):
                        cursor.updateRow(new_row)
            del cursor # Explicit delete
            
            arcpy.AddMessage("Step 2.2: Calculating Accessibility...")
            arcpy.management.AddField(output_fc, "Accessibility", "LONG")
            with arcpy.da.UpdateCursor(output_fc, ["Accessibility"] + valid_selected_fields) as cursor:
                for row in cursor:
                    count = sum(1 for i in range(1, len(row)) if row[i] > 0)
                    row[0] = count
                    cursor.updateRow(row)
            del cursor # Explicit delete
            
            arcpy.AddMessage("Step 2.3: Calculating Diversity...")
            arcpy.management.AddField(output_fc, "Diversity", "DOUBLE")
            with arcpy.da.UpdateCursor(output_fc, ["Diversity"] + valid_selected_fields) as cursor:
                for row in cursor:
                    counts = [row[i] for i in range(1, len(row))]
                    total = sum(counts)
                    if total == 0:
                        entropy = 0
                    else:
                        probs = [c / total for c in counts if c > 0]
                        entropy = -sum(p * math.log(p, 2) for p in probs) if probs else 0
                    row[0] = entropy
                    cursor.updateRow(row)
            del cursor # Explicit delete
            
            # Step 2.4: Normalization (Search + Update)
            arcpy.AddMessage("Step 2.4: Normalizing...")
            
            data_access = []
            data_div = []
            
            with arcpy.da.SearchCursor(output_fc, ["Accessibility", "Diversity"]) as cursor:
                for row in cursor:
                    data_access.append(row[0])
                    data_div.append(row[1])
            del cursor # Explicit delete
            
            min_access = min(data_access) if data_access else 0
            max_access = max(data_access) if data_access else 0
            min_div = min(data_div) if data_div else 0
            max_div = max(data_div) if data_div else 0
            
            # Clear lists to free memory
            del data_access
            del data_div
            gc.collect()

            arcpy.management.AddFields(output_fc, [["ZAccessibility", "DOUBLE"], ["ZDiversity", "DOUBLE"]])
            
            with arcpy.da.UpdateCursor(output_fc, ["ZAccessibility", "ZDiversity", "Accessibility", "Diversity"]) as cursor:
                for row in cursor:
                    if max_access > min_access:
                        row[0] = (row[2] - min_access) / (max_access - min_access)
                    else:
                        row[0] = 0
                    
                    if max_div > min_div:
                        row[1] = (row[3] - min_div) / (max_div - min_div)
                    else:
                        row[1] = 0
                    cursor.updateRow(row)
            del cursor # Explicit delete

            # Step 2.5: XMCI
            arcpy.AddMessage("Step 2.5: Calculating XMCI...")
            arcpy.management.AddField(output_fc, "XMCI", "DOUBLE")
            total_weight = weight_access + weight_div
            
            with arcpy.da.UpdateCursor(output_fc, ["XMCI", "ZAccessibility", "ZDiversity"]) as cursor:
                for row in cursor:
                    z_access = max(row[1], 0)
                    z_div = max(row[2], 0)
                    try:
                        row[0] = math.pow(z_access ** weight_access * z_div ** weight_div, 1 / total_weight)
                    except:
                        row[0] = 0
                    cursor.updateRow(row)
            del cursor # Explicit delete

            # Step 2.6: XMCIpop
            arcpy.AddMessage("Step 2.6: Calculating XMCIpop...")
            arcpy.management.AddField(output_fc, "XMCIpop", "DOUBLE")
            
            with arcpy.da.UpdateCursor(output_fc, ["XMCIpop", "XMCI", pop_field]) as cursor:
                for row in cursor:
                    xmci = max(row[1], 0.0001)
                    pop = row[2] if row[2] is not None else 0
                    row[0] = math.log(xmci) * pop
                    cursor.updateRow(row)
            del cursor # Explicit delete
            
            # Step 2.7: Final Index
            arcpy.AddMessage("Step 2.7: Calculating city-wide index...")
            sum_xmci_pop = 0
            sum_pop = 0
            hexagons_with_pop = 0
            
            with arcpy.da.SearchCursor(output_fc, ["XMCIpop", pop_field]) as cursor:
                for row in cursor:
                    pop = row[1] if row[1] is not None else 0
                    if pop > 0:
                        sum_xmci_pop += row[0]
                        sum_pop += pop
                        hexagons_with_pop += 1
            del cursor # Explicit delete
            
            if sum_pop == 0:
                city_index = 0
            else:
                city_index = math.exp(sum_xmci_pop / sum_pop)
            
            with open(output_txt, 'w', encoding='utf-8') as f:
                f.write(str(city_index))
            
            arcpy.AddMessage("="*60)
            arcpy.AddMessage("✓ ANALYSIS COMPLETED SUCCESSFULLY!")
            arcpy.AddMessage(f"✓ Output stored in: {output_fc}")
            
            # Force parameter update so Pro knows what happened (optional but good)
            # arcpy.SetParameterAsText(13, output_fc) 

        except arcpy.ExecuteError:
            arcpy.AddError(arcpy.GetMessages(2))
        except Exception as e:
            arcpy.AddError(f"Error: {str(e)}")
            import traceback
            arcpy.AddError(traceback.format_exc())
        finally:
            # CLEANUP:
            # 1. Do NOT CheckInExtension here (Pro handles it).
            # 2. Force Garbage Collection to clear memory before passing control back to Pro UI.
            if 'cursor' in locals(): del cursor
            if 'row' in locals(): del row
            gc.collect()
            arcpy.ClearWorkspaceCache_management()
        
        return