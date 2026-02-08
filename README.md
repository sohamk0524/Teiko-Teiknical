# Clinical Trial Analysis — Loblaw Bio

Analysis of immune cell populations across clinical trial samples, built for Bob Loblaw at Loblaw Bio.

## Setup & Running (GitHub Codespaces)

```bash
# 1. Create a virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Initialize the database and load data from cell-count.csv
python database.py

# 3. Run individual analyses (the dashboard includes all of these)
python analysis.py               # Part 2: frequency table
python statistical_analysis.py   # Part 3: stats + boxplot
python subset_analysis.py        # Part 4: subset breakdowns

# 4. Launch the interactive dashboard
streamlit run dashboard.py
```

The dashboard will be available at `http://localhost:8501`. In Codespaces, the port will be forwarded automatically and a link will appear in the Ports tab.

## Clarifications

For the question, "Considering Melanoma males, what is the average number of B cells for responders at time=0? Use two decimals (XXX.XX)." the following assumptions were made when reaching the value of **10,206.15**.

- All treatment types were considered (miraclib, phauximab)
- All sample types were considered (PBMC, WB)

In other words, the exact specifics that were highlighted in part 4, subset analysis were not applied, because the question did not explicitly indicate that I should restrict treatment types or sample types when calculating average number of B cells.

## Database Schema

The CSV data is normalized into three tables in SQLite:

```
subjects          samples                        cell_counts
┌─────────────┐   ┌──────────────────────────┐   ┌─────────────────┐
│ subject_id PK│◄──│ subject_id FK            │   │ id PK           │
│ condition    │   │ sample_id PK             │◄──│ sample_id FK    │
│ age          │   │ project                  │   │ population      │
│ sex          │   │ treatment                │   │ count           │
└─────────────┘   │ response                 │   └─────────────────┘
                   │ sample_type              │
                   │ time_from_treatment_start│
                   └──────────────────────────┘
```

**`subjects`** — One row per patient. Stores demographics (condition, age, sex) that are constant across all of a subject's samples.

**`samples`** — One row per sample. Stores sample-level metadata (project, treatment, response, sample type, timepoint) with a foreign key to `subjects`.

**`cell_counts`** — One row per cell population per sample (long format). Each sample has 5 rows (b_cell, cd8_t_cell, cd4_t_cell, nk_cell, monocyte) with a foreign key to `samples`.

### Design rationale and scalability

- **Normalized structure** avoids duplicating subject demographics across every sample row and avoids duplicating sample metadata across every cell count row. With hundreds of projects and thousands of samples, this significantly reduces storage and ensures updates propagate from a single source of truth.
- **Long-format cell counts** (rows, not columns) means adding new cell populations never requires a schema change — just new rows in `cell_counts`. This is critical when the number of measured populations grows over time.
- **Foreign keys** enforce referential integrity so orphaned records cannot exist.
- **The schema naturally supports new analytics** — any query can join the three tables to filter/aggregate by subject demographics, sample metadata, and cell counts in any combination without denormalization.

## Code Structure

| File | Purpose |
|---|---|
| `database.py` | **Part 1** — Schema definition, DB initialization, CSV loading |
| `analysis.py` | **Part 2** — Frequency table: relative percentage of each cell population per sample |
| `statistical_analysis.py` | **Part 3** — Mann-Whitney U tests and boxplots comparing responders vs non-responders (melanoma, miraclib, PBMC) |
| `subset_analysis.py` | **Part 4** — Queries for baseline melanoma/miraclib/PBMC samples with project, response, and sex breakdowns |
| `dashboard.py` | **Dashboard** — Streamlit app that ties all parts together with interactive tables and Plotly charts |
| `requirements.txt` | Python dependencies |
| `cell-count.csv` | Input data |

Each analysis module defines reusable query functions that return pandas DataFrames. The dashboard imports and calls these functions directly, so there is no duplicated logic — every number in the dashboard is computed by the same code that produces the CLI output. This makes it easy to add new analyses: write a query function in a module, then display its result in the dashboard.

## Dashboard

After launching with `streamlit run dashboard.py`, the dashboard provides:

- **Part 2** — Searchable, sortable frequency table with population filters
- **Part 3** — Interactive Plotly boxplots and a statistical results table with significance highlighting
- **Part 4** — Summary metrics, bar/pie charts for project, response, and sex breakdowns, plus a raw data explorer
