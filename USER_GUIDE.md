# X-Minute City Analysis Toolbox — User Guide

**Version 1.0**  
**Last updated:** March 2026

This document provides a complete guide to using the **X-Minute City Analysis** tool.

## 1. Tool Overview

The **X-Minute City Analysis** tool performs a two-phase workflow:
1. **Phase 1**: Service Area Analysis (isochrones) from hexagon centroids using Network Analyst.
2. **Phase 2**: Calculation of the X-Minute City Index (XMCI) based on POI accessibility and diversity within each isochrone.

**Output**:
- `XMCI` feature class (hexagons with all calculated fields)
- `XMCI for City.txt` (final city-wide index value)

## 2. Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| **Network Dataset** | GPNetworkDatasetLayer | Network dataset for routing (must have walking/driving time) | Yes |
| **Travel Mode** | String | Automatically populated from network (e.g., "Walking Time") | Yes |
| **Cutoffs (minutes)** | String | Travel time threshold (default: 15) | Yes |
| **Hexagon Grid Layer** | Feature Layer (Polygon) | Hexagonal grid representing urban analysis units | Yes |
| **Points of Interest (POIs)** | Feature Layer (Point) | POI points (e.g., shops, schools, clinics, parks) | Yes |
| **POI Category Field** | Field | Field in POI layer containing category names | Yes |
| **Population Field (in Hexagon Layer)** | Field | Field containing population count per hexagon | Yes |
| **POI Category Fields (Select categories for analysis)** | Multi-value String | Choose which POI categories to include in XMCI | Yes |
| **Accessibility Weight** | Double | Weight for Accessibility component (default: 0.5) | Yes |
| **Diversity Weight** | Double | Weight for Diversity component (default: 0.5) | Yes |
| **Output Feature Dataset** | Feature Dataset | Location to save intermediate and final feature classes | Yes |
| **Output Geodatabase** | Workspace | Geodatabase for tables and temporary data | Yes |
| **Output Folder (for temporary files)** | Folder | Folder for `PivotTable.dbf` and final `XMCI for City.txt` | Yes |

## 3. How to Run the Tool

1. Add the toolbox (`XMinuteCityIndex.pyt`) to ArcGIS Pro.
2. Double-click **X-Minute City Analysis** in the Toolbox.
3. Fill in all parameters (see table above).
4. Click **Run**.

The tool will display detailed progress messages in the Geoprocessing pane.

## 4. Output Fields (in XMCI feature class)

- `Accessibility` → Number of POI categories reachable
- `Diversity` → Shannon entropy of POI categories
- `ZAccessibility` / `ZDiversity` → Min-max normalized values
- `XMCI` → Combined X-Minute City Index (geometric weighted mean)
- `XMCIpop` → Population-weighted XMCI value (log-transformed)
- Final city index is written to `XMCI for City.txt`

## 5. Important Notes & Troubleshooting

- **Network Analyst extension** must be available and licensed.
- The tool automatically disables `addOutputsToMap` to prevent memory issues.
- Large datasets: use 64-bit ArcGIS Pro and sufficient RAM (≥32 GB recommended).
- All temporary files are saved in the specified Output Folder/Geodatabase.
- The tool has been optimized to prevent cursor locks and memory leaks.

## 6. Example Data
A small example dataset will be provided in the `example_data/` folder of this repository.

## 7. Citation & Reproducibility

This toolbox accompanies the manuscript submitted to *Nature Communications*.  
Please cite both the paper and the Zenodo DOI when using the tool in published research.
