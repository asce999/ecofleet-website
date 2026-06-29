def sanitize_excel_formula(val):
    if not isinstance(val, str):
        return val
    val = val.strip()
    if val and val[0] in ('=', '+', '-', '@'):
        return "'" + val
    return val

