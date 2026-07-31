import csv
import io
from pathlib import Path

import pandas as pd

MAX_HEADER_SCAN = 40
SEPARATORS = [",", "\t", ";", "|", None]  # None means "any whitespace"
TEXT_SUFFIXES = [".csv", ".txt", ".dat", ".tsv"]
EXCEL_SUFFIXES = [".xlsx", ".xls", ".xlsm"]


# ---------------------------------------------------------------- text files

def _split_rows(text, separator):
    """Split raw text into a list of rows using the given separator."""
    if separator is None:
        return [line.split() for line in text.splitlines()]

    reader = csv.reader(io.StringIO(text), delimiter=separator)
    return [row for row in reader]


def _rows_to_frame(rows):
    """Turn a ragged list of rows into a rectangular DataFrame."""
    rows = [row for row in rows if row]
    if not rows:
        return pd.DataFrame()

    width = max(len(row) for row in rows)
    padded = [row + [""] * (width - len(row)) for row in rows]

    frame = pd.DataFrame(padded)
    return frame.replace(r"^\s*$", pd.NA, regex=True)


def _score_frame(frame):
    """Higher is better: wide tables with numeric columns win."""
    if frame.empty or frame.shape[1] < 2:
        return 0

    numeric_columns = sum(
        pd.to_numeric(frame[column], errors="coerce").notna().sum() > 0
        for column in frame.columns
    )
    return frame.shape[1] + numeric_columns


def _read_text_table(file_path):
    """Read a delimited text file, detecting its separator automatically."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as handle:
        text = handle.read()

    best_frame = pd.DataFrame()
    best_score = 0

    for separator in SEPARATORS:
        frame = _rows_to_frame(_split_rows(text, separator))
        score = _score_frame(frame)

        if score > best_score:
            best_score = score
            best_frame = frame

    if best_frame.empty:
        best_frame = _rows_to_frame(_split_rows(text, ","))

    return best_frame


# ------------------------------------------------------------- header lookup

def _numeric_count(row):
    """How many cells in this row can be read as numbers."""
    return pd.to_numeric(row, errors="coerce").notna().sum()


def _find_header_row(raw):
    """Return the index of the row holding the column names, or None."""
    limit = min(MAX_HEADER_SCAN, len(raw) - 1)

    for index in range(limit):
        row = raw.iloc[index]
        filled = row.dropna()

        if filled.empty:
            continue

        numeric_here = _numeric_count(row)
        numeric_below = _numeric_count(raw.iloc[index + 1])

        # A header is mostly text and sits directly above numbers.
        if numeric_here >= len(filled):
            continue
        if numeric_below < 1:
            continue
        if len(filled) < numeric_below:
            continue

        return index

    return None


def _build_names(header_values, width):
    """Turn a header row into clean, unique column names."""
    names = []
    for position in range(width):
        value = header_values[position] if position < len(header_values) else None
        names.append("" if pd.isna(value) else str(value).strip())

    seen = {}
    unique = []
    for name in names:
        if name and name in seen:
            seen[name] += 1
            unique.append(f"{name} ({seen[name]})")
        else:
            if name:
                seen[name] = 1
            unique.append(name)

    return unique


# ------------------------------------------------------------------ cleaning

def _clean(frame):
    """Drop junk rows and columns, and convert text numbers to real numbers."""
    frame = frame.dropna(axis=0, how="all")
    frame = frame.dropna(axis=1, how="all")

    columns = {}
    unnamed_index = 1

    for column in frame.columns:
        series = frame[column]
        converted = pd.to_numeric(series, errors="coerce")
        is_numeric = converted.notna().sum() > 0

        name = str(column).strip()

        if not name:
            # An unnamed column is kept only when it really holds numbers.
            if not is_numeric:
                continue
            name = f"Column {unnamed_index}"
            unnamed_index += 1

        columns[name] = converted if is_numeric else series

    result = pd.DataFrame(columns)
    result = result.dropna(axis=0, how="all")
    return result.reset_index(drop=True)


# -------------------------------------------------------------- public entry

def read_data_file(file_path, sheet_name=0):
    """Read a CSV or Excel file and return a cleaned DataFrame.

    The header row is detected automatically, so files that begin with
    title rows, blank rows or instrument metadata are handled correctly.
    """
    suffix = Path(file_path).suffix.lower()

    if suffix in TEXT_SUFFIXES:
        raw = _read_text_table(file_path)
    elif suffix in EXCEL_SUFFIXES:
        raw = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
    else:
        raise ValueError(
            f"Unsupported file format: {suffix or 'unknown'}. "
            "Supported formats are xlsx, xls, csv, txt and dat."
        )

    if raw.empty:
        raise ValueError("The selected file contains no data.")

    header_row = _find_header_row(raw)

    if header_row is None:
        data = raw.copy()
        data.columns = [f"Column {i + 1}" for i in range(raw.shape[1])]
    else:
        data = raw.iloc[header_row + 1:].copy()
        data.columns = _build_names(list(raw.iloc[header_row]), raw.shape[1])

    cleaned = _clean(data)

    if cleaned.empty:
        raise ValueError("No usable data was found in the selected file.")

    return cleaned


def list_sheets(file_path):
    """Return the sheet names of an Excel file (empty list for other types)."""
    if Path(file_path).suffix.lower() not in EXCEL_SUFFIXES:
        return []
    return pd.ExcelFile(file_path).sheet_names


if __name__ == "__main__":
    import sys

    for path in sys.argv[1:]:
        print("=" * 60)
        print("FILE:", Path(path).name)
        print("sheets:", list_sheets(path))
        frame = read_data_file(path)
        print("columns:", list(frame.columns))
        print("rows:", len(frame))
        print(frame.head(3))
        print(frame.dtypes.to_string())