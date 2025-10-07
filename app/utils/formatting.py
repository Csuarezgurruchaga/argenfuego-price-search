def format_ars(value) -> str:
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return "-"
    # Format with US locale first: 1,234,567.89
    s = f"{amount:,.2f}"
    # Convert to AR format: 1.234.567,89
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s


