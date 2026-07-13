from pathlib import Path
import re
import sys

import duckdb
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_FOLDER = PROJECT_ROOT / "Database"
DATABASE_PATH = PROJECT_ROOT / "ask_data.duckdb"


def clean_sql_name(value: str) -> str:
    """
    Convert a filename or Excel sheet name into a safe SQL table name.
    Example: 'Sales Data' becomes 'sales_data'.
    """
    cleaned = value.strip().lower()
    cleaned = re.sub(r"[^a-z0-9]+", "_", cleaned)
    cleaned = cleaned.strip("_")

    if not cleaned:
        cleaned = "unnamed"

    if cleaned[0].isdigit():
        cleaned = f"table_{cleaned}"

    return cleaned


def get_excel_files(folder: Path) -> list[Path]:
    """Return all supported Excel files in the Database folder."""
    files = []

    for pattern in ("*.xlsx", "*.xlsm", "*.xls"):
        files.extend(folder.glob(pattern))

    return sorted(files)


def load_excel_files() -> None:
    if not EXCEL_FOLDER.exists():
        print(f"Database folder does not exist: {EXCEL_FOLDER}")
        sys.exit(1)

    excel_files = get_excel_files(EXCEL_FOLDER)

    if not excel_files:
        print(f"No Excel files were found in: {EXCEL_FOLDER}")
        sys.exit(1)

    print(f"Excel folder: {EXCEL_FOLDER}")
    print(f"DuckDB database: {DATABASE_PATH}")
    print(f"Found {len(excel_files)} Excel file(s).\n")

    connection = duckdb.connect(str(DATABASE_PATH))

    loaded_tables = []
    failed_sheets = []

    try:
        for excel_file in excel_files:
            print(f"Processing file: {excel_file.name}")

            try:
                workbook = pd.ExcelFile(excel_file)
            except Exception as error:
                print(f"  Could not open file: {error}")
                failed_sheets.append((excel_file.name, "Entire workbook", str(error)))
                continue

            for sheet_name in workbook.sheet_names:
                file_part = clean_sql_name(excel_file.stem)
                sheet_part = clean_sql_name(sheet_name)
                table_name = f"{file_part}_{sheet_part}"

                try:
                    dataframe = pd.read_excel(
                        excel_file,
                        sheet_name=sheet_name,
                    )

                    # Remove completely empty rows and columns.
                    dataframe = dataframe.dropna(axis=0, how="all")
                    dataframe = dataframe.dropna(axis=1, how="all")

                    # Convert column names to strings and make duplicates unique.
                    original_columns = [str(column) for column in dataframe.columns]
                    cleaned_columns = []
                    used_columns = {}

                    for column in original_columns:
                        cleaned_column = clean_sql_name(column)

                        if cleaned_column in used_columns:
                            used_columns[cleaned_column] += 1
                            cleaned_column = (
                                f"{cleaned_column}_{used_columns[cleaned_column]}"
                            )
                        else:
                            used_columns[cleaned_column] = 1

                        cleaned_columns.append(cleaned_column)

                    dataframe.columns = cleaned_columns

                    connection.register("excel_dataframe", dataframe)

                    connection.execute(
                        f"""
                        CREATE OR REPLACE TABLE "{table_name}" AS
                        SELECT *
                        FROM excel_dataframe
                        """
                    )

                    connection.unregister("excel_dataframe")

                    row_count = connection.execute(
                        f'SELECT COUNT(*) FROM "{table_name}"'
                    ).fetchone()[0]

                    column_count = len(dataframe.columns)

                    loaded_tables.append(
                        {
                            "table_name": table_name,
                            "source_file": excel_file.name,
                            "source_sheet": sheet_name,
                            "row_count": row_count,
                            "column_count": column_count,
                        }
                    )

                    print(
                        f"  Loaded sheet '{sheet_name}' "
                        f"as table '{table_name}' "
                        f"({row_count} rows, {column_count} columns)"
                    )

                except Exception as error:
                    try:
                        connection.unregister("excel_dataframe")
                    except Exception:
                        pass

                    failed_sheets.append(
                        (excel_file.name, sheet_name, str(error))
                    )

                    print(
                        f"  Failed to load sheet '{sheet_name}': {error}"
                    )

            print()

        if loaded_tables:
            metadata_dataframe = pd.DataFrame(loaded_tables)

            connection.register(
                "metadata_dataframe",
                metadata_dataframe,
            )

            connection.execute(
                """
                CREATE OR REPLACE TABLE _load_metadata AS
                SELECT
                    table_name,
                    source_file,
                    source_sheet,
                    row_count,
                    column_count,
                    CURRENT_TIMESTAMP AS loaded_at
                FROM metadata_dataframe
                """
            )

            connection.unregister("metadata_dataframe")

        print("Load completed.")
        print(f"Database created at: {DATABASE_PATH}")

        if loaded_tables:
            print("\nCreated tables:")

            for table in loaded_tables:
                print(
                    f"  - {table['table_name']}: "
                    f"{table['row_count']} rows"
                )

        if failed_sheets:
            print("\nSome sheets could not be loaded:")

            for file_name, sheet_name, error in failed_sheets:
                print(f"  - {file_name} / {sheet_name}: {error}")

    finally:
        connection.close()


if __name__ == "__main__":
    load_excel_files()
