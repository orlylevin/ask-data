from pathlib import Path
import re
import sys

import duckdb
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSV_FOLDER = PROJECT_ROOT / "Database"
DATABASE_PATH = PROJECT_ROOT / "ask_data.duckdb"


def clean_sql_name(value: str) -> str:
    cleaned = value.strip().lower()
    cleaned = re.sub(r"[^a-z0-9]+", "_", cleaned)
    cleaned = cleaned.strip("_")

    if not cleaned:
        cleaned = "unnamed"

    if cleaned[0].isdigit():
        cleaned = f"table_{cleaned}"

    return cleaned


def load_csv_files() -> None:
    if not CSV_FOLDER.exists():
        print(f"Database folder does not exist: {CSV_FOLDER}")
        sys.exit(1)

    csv_files = sorted(CSV_FOLDER.glob("*.csv"))

    if not csv_files:
        print(f"No CSV files were found in: {CSV_FOLDER}")
        sys.exit(1)

    print(f"CSV folder: {CSV_FOLDER}")
    print(f"DuckDB database: {DATABASE_PATH}")
    print(f"Found {len(csv_files)} CSV file(s).\n")

    connection = duckdb.connect(str(DATABASE_PATH))
    loaded_tables = []

    try:
        for csv_file in csv_files:
            table_name = clean_sql_name(csv_file.stem)

            try:
                dataframe = pd.read_csv(csv_file)

                dataframe = dataframe.dropna(axis=0, how="all")
                dataframe = dataframe.dropna(axis=1, how="all")

                cleaned_columns = []
                used_columns = {}

                for column in dataframe.columns:
                    cleaned_column = clean_sql_name(str(column))

                    if cleaned_column in used_columns:
                        used_columns[cleaned_column] += 1
                        cleaned_column = (
                            f"{cleaned_column}_{used_columns[cleaned_column]}"
                        )
                    else:
                        used_columns[cleaned_column] = 1

                    cleaned_columns.append(cleaned_column)

                dataframe.columns = cleaned_columns

                connection.register("csv_dataframe", dataframe)

                connection.execute(
                    f"""
                    CREATE OR REPLACE TABLE "{table_name}" AS
                    SELECT *
                    FROM csv_dataframe
                    """
                )

                connection.unregister("csv_dataframe")

                row_count = connection.execute(
                    f'SELECT COUNT(*) FROM "{table_name}"'
                ).fetchone()[0]

                loaded_tables.append(table_name)

                print(
                    f"Loaded {csv_file.name} as {table_name} "
                    f"({row_count} rows)"
                )

            except Exception as error:
                try:
                    connection.unregister("csv_dataframe")
                except Exception:
                    pass

                print(f"Failed to load {csv_file.name}: {error}")

        print("\nLoad completed.")
        print(f"Database created at: {DATABASE_PATH}")

        if loaded_tables:
            print("\nCreated tables:")
            for table_name in loaded_tables:
                print(f"  - {table_name}")

    finally:
        connection.close()


if __name__ == "__main__":
    load_csv_files()
