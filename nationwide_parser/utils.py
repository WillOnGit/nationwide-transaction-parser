def decimalise(quantity):
    """Format an int penny quantity into (-)£PPP.pp"""

    if quantity < 0:
        prefix = "-"
    else:
        prefix = ""
    quantity = abs(quantity)

    return f"{prefix}{quantity // 100}.{quantity % 100:02}"
