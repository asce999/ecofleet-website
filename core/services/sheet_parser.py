from pathlib import Path

def get_sheet_names(file_path: str) -> list:
    """Returns a list of sheet names from an Excel file, or an empty list if it cannot be read."""
    if file_path and Path(file_path).exists():
        try:
            import openpyxl
            wb = openpyxl.load_workbook(file_path, read_only=True)
            return wb.sheetnames
        except Exception:
            pass
    return []
