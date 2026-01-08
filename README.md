# UNDP Energy Moonshot Tracker — Data Pipeline (README)

This repository contains the **Moonshot Tracker Pipeline** that ingests CO validation workbooks and supporting reference datasets, enriches them with UNDP portfolio metadata, computes key summary statistics (including beneficiary conversions), and exports the consolidated results to an Excel “final results” file. A separate notebook generates **regional auto-summaries**.


---
# Energy-Moonshot-Tracker

To run the pipeline, download the newest version of the CO Validation Folder and copy all country files to "01_Input/00_CO Validation". Then, open the "Moonshot Tracker Pipeline.ipynb" file and run the entire notebook. The final results will be exported to "02_Output/00_Final Results/Moonshot Tracker Results - Auto.xlsx".

- [ ] Download SharePoint folder “07. CO validation”
- [ ] Place into `01_Input/` as `00_CO Validation`
- [ ] Run `Moonshot Tracker Pipeline.ipynb` end-to-end
- [ ] Fix any errors in source data and update SharePoint copies
- [ ] Run `Region Auto Summaries.ipynb`
- [ ] Open and validate `02_Output/00_Final Results/Moonshot Tracker Results - Auto.xlsx`

---

## What this pipeline produces

Primary deliverable:

- **Final consolidated Excel output**
  - `02_Output/00_Final Results/Moonshot Tracker Results - Auto.xlsx`
  - Tabs include (at minimum): **Summary**, **Outputs**, **Projects**, **Countries**

Secondary deliverables (depending on which cells you run / options enabled):

- Portfolio enrichments from UNDP APIs
- PIMS/Atlas metadata merges
- Gender marker mapping
- Charts/analysis outputs (in-notebook)
- Optional JSON export (for dashboard use)
- Optional AI-generated output descriptions (requires OpenAI credentials)

---

## Repository structure (key folders)

The pipeline assumes a consistent relative folder structure:

- `01_Input/`
  - `00_CO Validation/`  ← **your CO validation workbooks go here**
  - `01_Methodology/`    ← conversion factors (direct + indirect)
  - `02_Energy Data/`    ← reference energy datasets (e.g., access, clean cooking, population, RISE)
  - `03_Country Meta/`   ← country metadata inputs (ISO, household data, tracker metadata)
  - `05_PIMS/`           ← PIMS extract (e.g., `pims-2-16.xlsx`)
  - `06_Gender/`         ← gender marker mapping file (e.g., `gen-markers-mar25.xlsx`)
  - `07_Outputs/`        ← manual output descriptions file (CSV)

- `02_Output/`
  - `00_Final Results/`  ← **final Excel output is written here**

---

## Required inputs

### 1) CO validation folder (from SharePoint)
The pipeline expects CO validation workbooks in:

- `01_Input/00_CO Validation/`

These workbooks provide the project/output records the pipeline ingests and standardizes.

### 2) Methodology files (conversion factors)
- `01_Input/01_Methodology/Direct Conversion Factors.csv`
- `01_Input/01_Methodology/Indirect Conversion Factors.csv`

Used to convert outputs into comparable beneficiary estimates (direct/indirect).

### 3) Reference datasets
The pipeline reads several reference files under `01_Input/` for:
- country metadata and ISO mapping,
- energy access / clean cooking / renewables / population reference series,
- RISE scores,
- household data inputs.

### 4) Optional enrichments
- `01_Input/05_PIMS/pims-2-16.xlsx` (or equivalent)
- `01_Input/06_Gender/gen-markers-*.xlsx`
- `01_Input/07_Outputs/Output Descriptions Manual.csv`

---

## Execution workflow (the standard run)

### Step 1 — Pull CO validation from SharePoint
1. Download the folder **“07. CO validation”** from SharePoint.
2. Place it into `01_Input/` and rename it to:
   - `00_CO Validation`

Final expected path:
- `01_Input/00_CO Validation/`

### Step 2 — Run the main pipeline notebook
Run the **Moonshot Tracker Pipeline** notebook end-to-end:

- `Moonshot Tracker Pipeline.ipynb`

If any errors arise:
- Fix the underlying issue **in the source data files** (most often within the CO validation workbooks).
- Ensure the corrected version is also **updated back on SharePoint** so SharePoint remains the source of truth.

### Step 3 — Run the regional auto-summaries notebook
Run the **Region Auto Summaries** notebook to generate regional summary outputs.

- `Region Auto Summaries.ipynb` (name may vary; use the notebook referenced internally by the team)

This step uses the consolidated pipeline data and produces region-level narrative summaries / summary tables used for reporting.

### Step 4 — Access final results
Open the final consolidated file:

- `02_Output/00_Final Results/Moonshot Tracker Results - Auto.xlsx`

(If your working convention is `03_Output/...`, confirm the notebook export path matches your folder structure.)

---

## What the main pipeline does (logical stages)

The main notebook is organized into these stages:

1. **Prepare data**
   - Loads country metadata and tracker reference tables
   - Ingests CO validation workbooks and constructs the core **Projects** and **Outputs** dataframes
   - Pulls in manual output description mappings as needed

2. **Process / clean dataframes**
   - Standardizes columns and formats
   - Cleans output records and normalizes key fields used downstream

3. **Beneficiaries conversion**
   - Computes beneficiary estimates using:
     - **Direct conversion factors**
     - **Indirect conversion factors**
   - Includes household conversion logic where applicable

4. **Additional derived indicators**
   - Adds/derives additional output metrics (e.g., energy efficiency-related fields; some GHG logic may be included depending on configuration)

5. **Enrichment from UNDP systems**
   - Downloads/merges portfolio data via API
   - Adds Atlas/PIMS metadata to the project dataframe
   - Applies **gender marker** mapping where available
   - Updates donor and country metadata tables (where enabled)

6. **Analysis + export**
   - Generates summary statistics and supporting analyses
   - (Optional) generates AI descriptions for outputs if enabled
   - Exports the consolidated Excel workbook
   - (Optional) exports JSON for dashboard integration


---

## Environment & dependencies

Typical Python dependencies used by the notebook include:
- `pandas`, `numpy`, `xlsxwriter`
- `tqdm`
- `python-dotenv`
- `matplotlib` (and some optional plotting)
- `openai` (only if using AI description generation)
- a country name mapping helper (e.g., `countrynames`)

If using AI description generation:
- Ensure your OpenAI credentials are available via environment variables (commonly loaded via a `.env` file in the working environment).

---


