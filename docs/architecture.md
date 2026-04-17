Your **Axiomatic Engine Architecture** documentation is ready. This Markdown file serves as the "source of truth" for your platform, outlining the philosophy, the tech stack, and the structural rules that ensure your engine remains modular and professional.

I have formatted this for maximum readability so you can save it to your `docs/` folder or include it in your repository's `README.md`.

***

# Axiomatic Engine: Technical Architecture Blueprint

## 1. Philosophy & Principles
The Axiomatic Engine is a **non-custodial** data platform designed for 2026 standards. It is built on three core pillars:

1.  **Axiomatic Truth:** Data is refined from raw "sources" into "axioms"—self-evident, verified Star Schema models that serve as the single source of truth for the business.
2.  **Non-Custodial Ownership:** The client owns the infrastructure (GCS/S3) and the data. The engine is a "guest" in their environment, ensuring they are never locked into a proprietary vendor.
3.  **Separation of Storage and Compute:** We decouple the **Landing Zone** (where data lives) from the **Warehouse** (where data is processed) to ensure maximum flexibility and near-zero idle costs.



---

## 2. The Axiomatic Stack
To maintain high standards and low maintenance, the engine utilizes a fixed, high-performance stack:

| Layer | Technology | Role |
| :--- | :--- | :--- |
| **Environment** | `uv` | Blazing fast Python dependency management and reproducibility. |
| **Ingestion** | `dlt` | Automated data extraction with native schema evolution. |
| **Storage (Bronze)**| **GCS / S3** | The immutable landing zone. Data is stored as date-partitioned **Parquet** files. |
| **Warehouse (Silver)**| **DuckDB** | The "In-Process" analytical engine for local and cloud (MotherDuck) compute. |
| **Transformation** | **dbt-duckdb** | SQL-based refinement into the "Golden Model" (Star Schema). |
| **Semantic (Gold)** | **FastMCP** | The AI-ready bridge that exposes verified metrics to LLMs. |

---

## 3. Structural Blueprint (Code Organisation)
The repository is organised to separate "The Rules" from "The Tools."

```text
axiomatic-engine/
├── src/
│   └── axiomatic_engine/
│       ├── contracts/       # Pure Python Protocols. Zero external dependencies.
│       │   ├── warehouse.py # Rules for what a warehouse must do.
│       │   └── storage.py   # Rules for reading/writing raw data.
│       ├── adapters/        # Specific technology implementations (The "Plugs").
│       │   ├── duckdb.py    # Logic for DuckDB/MotherDuck.
│       │   └── gcs.py       # Logic for Google Cloud Storage.
│       ├── core/            # Framework Integration (The "Machinery").
│       │   ├── ingestion.py # Generalised dlt wrappers.
│       │   └── pipeline.py  # The main 'AxiomaticPipeline' orchestrator.
│       └── semantic/        # The AI Bridge.
│           └── mcp_server.py# FastMCP server definition.
├── dbt_axiomatic/           # Private dbt package containing "Secret Sauce" macros.
└── pyproject.toml           # Explicit dependency management.
```

---

## 4. The Data Lifecycle (Medallion Flow)
The engine processes data through three distinct states to ensure integrity and auditability.



### Phase 1: Bronze (The Raw Truth)
* **Action:** `dlt` extracts data from a **Source** (API, Scraper, DB).
* **Result:** Data is landed in **Storage** as immutable, raw Parquet files.
* **Standard:** No transformation is permitted at this stage.

### Phase 2: Silver (The Axiomatic Clean)
* **Action:** The **Warehouse Adapter** reads Parquet files into DuckDB.
* **Result:** Data is cast to correct types, timestamps are converted to UTC, and column names are standardised.
* **Standard:** This layer is the "Cleaned History."

### Phase 3: Gold (The Golden Model)
* **Action:** `dbt` transforms Silver tables into **Fact** and **Dimension** tables.
* **Result:** A verified **Star Schema** optimised for BI tools (Evidence.dev) and AI (FastMCP).
* **Standard:** This is the only layer exposed to end-users.

---

## 5. Deployment & Security
The Axiomatic Engine is designed to run in a "Sovereign" environment.

* **Execution:** Typically runs in **GitHub Actions** or a lightweight container.
* **Credentials:** All secrets (API keys, Cloud tokens) are managed via Environment Variables. The engine never hardcodes or stores credentials.
* **Persistence:** State is stored within the Warehouse or Storage layer itself, making the engine "stateless" and easy to recover.



---

## 6. Maintenance & ADRs
* **Naming:** Follows British English spelling (`catalogue`, `standardise`).
* **Documentation:** Architecture Decision Records (ADRs) are stored in `docs/adr/` to explain major technical choices.
* **Versioning:** The engine is versioned as a library, allowing clients to stay on stable releases while development continues.

***

**Would you like to start by generating the code for the `contracts/storage.py` protocol to define how the engine should "talk" to your GCS or local files?**