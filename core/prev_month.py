"""
Previous Month Update logic.
Updates only "In Transit" shipments in 2W/CV masters using Delhivery daily CSV dumps.
Matching is done strictly by LR Number. No new rows are added.
"""
import io
import datetime
import pandas as pd
from .morning import normalize_lr, find_lr_col, MASTER_COLUMNS, save_master, ReportError

def _today():
    return pd.Timestamp(datetime.datetime.today().date())

def clean_delhivery_prev(file):
    """Clean one Delhivery CSV without current-month date filtering."""
    try:
        df = pd.read_csv(file, dtype={"LRN": str, "Pin code": str})
    except Exception as e:
        raise ReportError(f"Couldn't read a Delhivery CSV ({e}).")
    df.columns = df.columns.str.strip()
    if "LRN" not in df.columns or "Client Location/warehouse" not in df.columns:
        raise ReportError(
            "A Delhivery CSV is missing expected columns (LRN / Client Location/warehouse).")

    df["LRN"] = normalize_lr(df["LRN"])
    df["Pin code"] = df["Pin code"].astype(str).str.strip()

    df["No of boxes"] = pd.to_numeric(df["No of boxes"], errors="coerce").fillna(0).astype(int) - 1
    df["No of boxes"] = df["No of boxes"].clip(lower=0)

    df["Consignee name"] = df["Consignee name"].astype(str).str.split(",").str[0].str.strip()

    df["Status_mapped"] = df["Current Status"].apply(
        lambda x: "Delivered" if str(x).strip().lower() == "delivered" else "In Transit")

    df["Expected Date"]  = pd.to_datetime(df["Expected Date"],  errors="coerce").dt.normalize()
    df["Delivered Date"] = pd.to_datetime(df["Delivered Date"], errors="coerce").dt.normalize()
    df["Pickup Date"]    = pd.to_datetime(df["Pickup Date"],    errors="coerce").dt.normalize()

    # NOTE: NO filtering of Pickup Date to current month. We preserve previous months' data.

    df["vehicle_type"] = df["Client Location/warehouse"].astype(str).apply(
        lambda x: "2W" if "2 wheeler" in x.lower() else "CV")

    df["_status_rank"] = df["Status_mapped"].apply(lambda x: 0 if x == "Delivered" else 1)
    df = (df.sort_values("_status_rank")
            .drop_duplicates(subset="LRN", keep="first")
            .drop(columns="_status_rank"))
    return df

def load_master_prev(master_bytes, vehicle_type):
    """Load Master Excel sheet without filtering by current month."""
    sheet = "2W Report" if vehicle_type == "2W" else "CV Report"
    try:
        df = pd.read_excel(io.BytesIO(master_bytes), sheet_name=sheet, dtype=object)
    except ValueError:
        raise ReportError(
            f'The {vehicle_type} master has no "{sheet}" sheet — is it the right file?')

    lr_col_actual = find_lr_col(df)
    if lr_col_actual != "Lr No. ":
        df = df.rename(columns={lr_col_actual: "Lr No. "})
    df["Lr No. "] = normalize_lr(df["Lr No. "])

    if "Consignor Name" in df.columns and "Account of Customer - Consignor Name" not in df.columns:
        df = df.rename(columns={"Consignor Name": "Account of Customer - Consignor Name"})
    if "ETD" in df.columns and "Estimated Date of Delivery ( Based upon Agreed TAT)" not in df.columns:
        df = df.rename(columns={"ETD": "Estimated Date of Delivery ( Based upon Agreed TAT)"})

    for _dc in ["Date of Shipping",
                "Estimated Date of Delivery ( Based upon Agreed TAT)",
                "Date", "Actual Delivery Date"]:
        if _dc in df.columns:
            df[_dc] = pd.to_datetime(df[_dc], errors="coerce").dt.normalize()

    # NOTE: No current month shipping date filtering is done here. All rows are preserved.

    df = df.drop_duplicates(subset="Lr No. ", keep="first")
    for col in MASTER_COLUMNS:
        if col not in df.columns:
            df[col] = None
    return df[MASTER_COLUMNS]

def update_existing_rows_prev(master_df, report_df):
    """Updates only existing 'In Transit' shipments matching by LR Number.
    Does not append new rows or columns.
    """
    today = _today()
    etd_col = "Estimated Date of Delivery ( Based upon Agreed TAT)"
    report_lookup = report_df.set_index("LRN")

    updated = 0
    delivered = 0
    in_transit = 0

    for idx, row in master_df.iterrows():
        # Only check/update rows in the master that are currently "In Transit"
        current_status = str(row.get("Status") or "").strip().lower()
        if current_status != "in transit":
            continue

        lr = str(row["Lr No. "]).strip()
        if lr not in report_lookup.index:
            continue

        rep = report_lookup.loc[lr]
        if isinstance(rep, pd.DataFrame):
            rep = rep.iloc[0]

        status = rep["Status_mapped"]
        master_df.at[idx, "Status"] = status
        updated += 1

        if status == "Delivered":
            delivery_date = rep.get("Delivered Date", pd.NaT)
            master_df.at[idx, "Actual Delivery Date"] = delivery_date if pd.notna(delivery_date) else pd.NaT
            master_df.at[idx, "Date"] = pd.NaT
            master_df.at[idx, "Days"] = None
            delivered += 1
        else:
            # If still In Transit, update date to today and compute days left
            master_df.at[idx, "Date"] = today
            master_df.at[idx, "Actual Delivery Date"] = pd.NaT
            etd = row[etd_col]
            if pd.notna(etd):
                master_df.at[idx, "Days"] = (pd.Timestamp(etd) - today).days
            else:
                master_df.at[idx, "Days"] = None
            in_transit += 1

    return master_df, {"updated": updated, "delivered": delivered, "in_transit": in_transit}

def process_vehicle_prev(vehicle_type, delhivery_df, master_bytes):
    """Process a single vehicle type's workbook updates."""
    master_df = load_master_prev(master_bytes, vehicle_type)
    
    # Load pincode sheet to keep it in the final workbook
    pincode_sheet = "Pin-Code" if vehicle_type == "2W" else "Pin-Codes"
    try:
        pincode_df_full = pd.read_excel(io.BytesIO(master_bytes), sheet_name=pincode_sheet)
    except ValueError:
        raise ReportError(f"The master file is missing the required '{pincode_sheet}' sheet.")

    # Only look at Delhivery records matching this vehicle type
    deliv_vt = delhivery_df[delhivery_df["vehicle_type"] == vehicle_type]

    # Perform updates in place
    master_df, stats = update_existing_rows_prev(master_df, deliv_vt)

    # Save to Excel preserving all formatting
    out = save_master(master_df, pincode_df_full, vehicle_type)
    return out, stats

def generate(delhivery_files, file_2w, file_cv):
    """
    delhivery_files: list of uploaded CSV file objects.
    file_2w, file_cv: uploaded master .xlsx file objects.
    Returns: dict {'2W': (BytesIO, filename), 'CV': (BytesIO, filename), 'summary': {...}}.
    """
    frames = [clean_delhivery_prev(f) for f in delhivery_files]
    delhivery_df = pd.concat(frames, ignore_index=True)
    delhivery_df["_rank"] = delhivery_df["Status_mapped"].apply(lambda x: 0 if x == "Delivered" else 1)
    delhivery_df = (delhivery_df.sort_values("_rank")
                    .drop_duplicates(subset="LRN", keep="first")
                    .drop(columns="_rank"))

    bytes_2w = file_2w.read()
    bytes_cv = file_cv.read()

    out_2w, sum_2w = process_vehicle_prev("2W", delhivery_df, bytes_2w)
    out_cv, sum_cv = process_vehicle_prev("CV", delhivery_df, bytes_cv)

    # Use a clear report date/name
    today_str = datetime.date.today().strftime("%d%b%y")
    return {
        "2W": (out_2w, f"2W_PrevUpdate_{today_str}.xlsx"),
        "CV": (out_cv, f"CV_PrevUpdate_{today_str}.xlsx"),
        "summary": {
            "delhivery_rows": len(delhivery_df),
            "two_w": sum_2w,
            "cv": sum_cv,
        },
    }
