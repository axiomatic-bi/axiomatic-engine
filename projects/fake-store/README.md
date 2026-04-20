# Fake Store Data Pipeline (Axiomatic Project)

This project is a reference implementation of the **Axiomatic Engine**, designed to ingest retail data from the [Fake Store API](https://fakestoreapi.com/) and transform it into an AI-ready Star Schema.

## 🏗 Architecture: Medallion Flow

The pipeline follows a **Medallion Architecture**, ensuring data integrity and traceability from source to analytics.

* **Bronze (Raw):** Ingested JSON records landed directly from the REST API via the `Axiomatic Engine` bridge.
* **Silver (Staging):** Cleaned and typed versions of the raw data. This layer handles null-handling, type casting (e.g., prices to decimals), and schema standardisation.
* **Gold (Analytics):** A Star Schema featuring consolidated Dimensions and Facts.
* **AI/BI Layer:** Denormalised, "wide" views designed for LLM consumption and business intelligence.

---

## 📂 Project Structure

```text
projects/fake_store/
├── sql/
│   ├── silver/        # Staging models (Cleaning/Casting)
│   ├── gold/          # Star Schema (Dimensions/Facts)
│   └── analytics/     # Denormalised "AI-Ready" views
├── src/
│   ├── definitions.py # RestApiResourceDefinitions for the engine
│   └── normalisers.py # Project-specific ResourceNormaliser hooks
├── .env               # Local secrets (API keys, DB paths)
├── .env.example       # Template for environment variables
└── run_pipeline.py    # Main entry point and orchestrator
```

---

## 🛠 Integration Details

### The Engine Bridge
This project utilises the `Axiomatic Engine` as its core library. It implements the following engine contracts:
* **`AuthHookProtocol`**: Handles request signing and token injection.
* **`ResourceNormaliserProtocol`**: Manages payload flattening and project-specific attribute mapping before records enter the warehouse.
* **`PaginationStrategyProtocol`**: Defines traversal logic for the retail endpoints.

### Parameter Provenance
In alignment with engine standards, all API-specific parameters (URLs, credentials) are discovered at the project level (via `.env`) and injected into the engine constructors at runtime. The engine remains agnostic of the Fake Store domain.

---

## 🚀 Usage

1.  **Environment Setup**: Copy `.env.example` to `.env` and fill in the required variables.
2.  **Execution**: Run the main pipeline conductor:
    ```bash
    python run_pipeline.py
    ```

---

## 📝 Development Notes
* **Naming Conventions**: Always use British English (e.g., `normaliser`, `standardising`) in code comments and user-facing documentation.
* **SQL Standards**: All transformation logic is stored in the `sql/` directory and executed via the engine's transformation runner (pending implementation).

---

### Why this README helps you right now
1.  **Cursor Context:** By having this in the root of the project folder, Cursor will stop suggesting you put API keys in the engine and will start looking in `normalisers.py` when you ask to change how data is shaped.
2.  **Portability:** It clearly identifies the project as a **Consumer** of the engine, making it easy to separate later if you decide to go multi-repo.
3.  **Documentation Alignement:** It satisfies your saved instruction to keep naming aligned between Python modules and documentation.

**How does that look for a starting point?** If it feels right, you can save this as `projects/fake_store/README.md` and we can move on to drafting those first **Silver** transformation scripts.