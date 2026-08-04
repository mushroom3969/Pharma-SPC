"""Load raw process-data Excel files under source_data/Process Data into DuckDB.

Each Excel file becomes one wide table in the `raw` schema of
pipeline/pharma_pipeline.duckdb (the same file dbt reads via profiles.yml),
named raw_<product>_<section>[_<sub_scale>]. Column names are sanitized to
valid SQL identifiers; the original header is kept in a sibling
`<table>__columns` mapping so nothing is lost.
"""

import re
from pathlib import Path

import duckdb
import pandas as pd

PIPELINE_DIR = Path(__file__).resolve().parent.parent
SOURCE_DIR = PIPELINE_DIR.parent / "source_data" / "Process Data"
DB_PATH = PIPELINE_DIR / "pharma_pipeline.duckdb"
RAW_SCHEMA = "raw"


def sanitize_identifier(name: str) -> str:
    name = str(name).strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    if not name:
        name = "col"
    if name[0].isdigit():
        name = f"c_{name}"
    return name


def dedupe_columns(columns: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    result = []
    for col in columns:
        if col not in seen:
            seen[col] = 0
            result.append(col)
        else:
            seen[col] += 1
            result.append(f"{col}_{seen[col]}")
    return result


def table_name_for(xlsx_path: Path) -> tuple[str, dict]:
    rel_parts = xlsx_path.relative_to(SOURCE_DIR).parts[:-1]  # drop filename
    product, site, scale, *section_parts = rel_parts
    section_slug = sanitize_identifier("_".join(section_parts))
    table = f"raw_{sanitize_identifier(product)}_{section_slug}"
    meta = {
        "product": product,
        "site": site,
        "scale": scale,
        "section": section_parts[0] if section_parts else None,
        "sub_scale": "_".join(section_parts[1:]) if len(section_parts) > 1 else None,
    }
    return table, meta


def load_file(con: duckdb.DuckDBPyConnection, xlsx_path: Path) -> None:
    table, meta = table_name_for(xlsx_path)

    df = pd.read_excel(xlsx_path)
    sanitized_cols = dedupe_columns([sanitize_identifier(c) for c in df.columns])
    df.columns = sanitized_cols

    df["source_file"] = xlsx_path.name
    df["product"] = meta["product"]
    df["site"] = meta["site"]
    df["scale"] = meta["scale"]
    df["sub_scale"] = meta["sub_scale"]

    con.register("df_tmp", df)
    con.execute(f'CREATE OR REPLACE TABLE {RAW_SCHEMA}."{table}" AS SELECT * FROM df_tmp')
    con.unregister("df_tmp")

    print(f"{table}: {len(df)} rows, {len(df.columns)} cols  <-  {xlsx_path.relative_to(SOURCE_DIR)}")


def main() -> None:
    xlsx_files = sorted(SOURCE_DIR.glob("**/*.xlsx"))
    if not xlsx_files:
        print(f"No .xlsx files found under {SOURCE_DIR}")
        return

    con = duckdb.connect(str(DB_PATH))
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {RAW_SCHEMA}")

    for xlsx_path in xlsx_files:
        load_file(con, xlsx_path)

    con.close()
    print(f"\nDone. Wrote {len(xlsx_files)} table(s) to {DB_PATH}")


if __name__ == "__main__":
    main()
