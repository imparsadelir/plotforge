from pathlib import Path
import pandas as pd
def read_data_file(file_path):
    """Reads a data file (CSV or Excel) and returns a pandas DataFrame."""
    
    suffix = Path(file_path).suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(file_path)
    elif suffix in [".xlsx", ".xls"]:
        return pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format. Please provide a CSV or Excel file.")
    
if __name__ == "__main__":
    print(read_data_file("test_data.xlsx"))
