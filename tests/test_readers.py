"""Tests for the file reader.

These run without opening a window, because nothing in core/ depends on
the interface. Each test writes a small file, reads it back, and checks
that the reader understood its structure.
"""

import pandas as pd
import pytest

from core.io.readers import read_data_file


def write_csv(folder, name, text):
    """Create a text file and return its path."""
    path = folder / name
    path.write_text(text, encoding="utf-8")
    return path


def test_reads_a_plain_csv(tmp_path):
    """The simplest case: header on the first line."""
    path = write_csv(tmp_path, "plain.csv", "time,value\n0,10\n1,20\n2,30\n")

    frame = read_data_file(path)

    assert list(frame.columns) == ["time", "value"]
    assert len(frame) == 3
    assert frame["value"].tolist() == [10, 20, 30]


def test_finds_a_header_below_title_rows(tmp_path):
    """Instrument exports often put a title above the real header."""
    path = write_csv(
        tmp_path,
        "titled.csv",
        "Sample 1133\n\n\ntime,value\n0,10\n1,20\n",
    )

    frame = read_data_file(path)

    assert list(frame.columns) == ["time", "value"]
    assert len(frame) == 2


def test_detects_a_tab_separator(tmp_path):
    """The delimiter is worked out from the file, not assumed."""
    path = write_csv(tmp_path, "tabs.txt", "x\ty\n1\t10\n2\t20\n")

    frame = read_data_file(path)

    assert list(frame.columns) == ["x", "y"]
    assert frame["y"].tolist() == [10, 20]


def test_columns_are_numeric(tmp_path):
    """Values must arrive as numbers, otherwise they cannot be plotted."""
    path = write_csv(tmp_path, "numbers.csv", "a,b\n1,2.5\n2,3.5\n")

    frame = read_data_file(path)

    assert pd.api.types.is_numeric_dtype(frame["a"])
    assert pd.api.types.is_numeric_dtype(frame["b"])


def test_duplicate_column_names_are_made_unique(tmp_path):
    """Two columns with the same name would otherwise overwrite each other."""
    path = write_csv(tmp_path, "dup.csv", "time,value,value\n0,1,2\n1,3,4\n")

    frame = read_data_file(path)

    assert len(frame.columns) == 3
    assert len(set(frame.columns)) == 3


def test_unnamed_text_column_is_dropped(tmp_path):
    """Instruments add annotation columns that are not data."""
    path = write_csv(
        tmp_path,
        "annotated.csv",
        "time,value,\n0,10,@note one\n1,20,\n2,30,\n",
    )

    frame = read_data_file(path)

    assert list(frame.columns) == ["time", "value"]


def test_unsupported_format_is_rejected(tmp_path):
    """An unknown extension should fail clearly, not silently."""
    path = write_csv(tmp_path, "data.docx", "not a table")

    with pytest.raises(ValueError):
        read_data_file(path)


def test_excel_file_round_trip(tmp_path):
    """Excel files go through a different branch of the reader."""
    path = tmp_path / "sheet.xlsx"
    pd.DataFrame({"time": [0, 1, 2], "value": [5, 6, 7]}).to_excel(
        path, index=False
    )

    frame = read_data_file(path)

    assert list(frame.columns) == ["time", "value"]
    assert frame["value"].tolist() == [5, 6, 7]
