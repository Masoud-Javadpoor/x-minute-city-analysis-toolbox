# X-Minute City Analysis Toolbox

**An open-source ArcGIS Pro toolbox for calculating the X-Minute City Index (XMCI)**

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXXX)  
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This toolbox integrates **Service Area Analysis** (Network Analyst) with the full calculation of the **X-Minute City Index (XMCI)**, including Accessibility, Diversity (Shannon entropy), normalized indices, population-weighted XMCI, and the final city-wide index.

It has been specifically optimized for stability (memory leak fixes, cursor management, and proper extension handling).

### Features
- Fully automated Service Area (isochrone) analysis using user-defined travel mode and cutoffs
- Dynamic POI category selection and entropy-based diversity calculation
- Computation of Accessibility, Diversity, Z-scores, XMCI, XMCIpop, and city-wide XMCI
- Clean output: feature class + plain-text city index file
- Designed for reproducible urban accessibility research

### Screenshots
**Toolbox structure**  
![Toolbox Folder](/toolbox-folder.jpg)

**Tool interface in ArcGIS Pro**  
![X-Minute City Analysis Tool](/tool-interface.jpg)

### Installation
1. Download the latest release from [Releases](https://github.com/YOURUSERNAME/X-Minute-City-Index-Toolbox/releases).
2. Open **ArcGIS Pro**.
3. In the **Catalog** pane → **Toolboxes** → right-click → **Add Toolbox**.
4. Select `XMinuteCityIndex.pyt`.

### Quick Start
See the full **[User Guide](/USER_GUIDE.md)** for detailed instructions.

### Requirements
- ArcGIS Pro 3.0 or higher
- **Network Analyst** extension (required)
- A network dataset (e.g., OpenStreetMap-based or official)
- Hexagon grid layer + POI point layer with population field

### Citation
If you use this toolbox in your research, please cite both the paper and the software:

> [Your Full Name], [Year]. X-Minute City Index: An integrated ArcGIS Pro toolbox for measuring 15-minute city accessibility. *Nature Communications* [in press].  
> DOI: [Your Paper DOI]

**Software citation (Zenodo):**  
[Your Name] (2026). X-Minute City Index Toolbox (v1.0). Zenodo. https://doi.org/10.5281/zenodo.XXXXXXXX

### License
MIT License — feel free to use, modify, and distribute with proper attribution.

### Data Availability
Example datasets and full documentation are available in the `example_data/` folder.
