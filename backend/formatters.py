"""Utility functions for formatting currency and numbers in Indian notation."""

def format_inr_lakh(amount: float) -> str:
    """Formats a numeric INR amount into Indian lakh/crore notation.
    
    Examples:
        150000    -> '₹1.5 lakh'
        1800000   -> '₹18 lakh'
        75000     -> '₹75,000'
        10000000  -> '₹1 crore'
        25000000  -> '₹2.5 crore'
        360000    -> '₹3.6 lakh'
    """
    if amount is None:
        return "₹0"
    
    amount = float(amount)
    
    if amount >= 1_00_00_000:  # 1 crore = 10,000,000
        crores = amount / 1_00_00_000
        if crores == int(crores):
            return f"₹{int(crores)} crore"
        return f"₹{crores:.1f} crore"
    elif amount >= 1_00_000:  # 1 lakh = 100,000
        lakhs = amount / 1_00_000
        if lakhs == int(lakhs):
            return f"₹{int(lakhs)} lakh"
        return f"₹{lakhs:.1f} lakh"
    elif amount >= 1000:
        return f"₹{amount:,.0f}"
    else:
        return f"₹{amount:.0f}"


def format_inr_text(text: str) -> str:
    """Post-processes text to convert any ₹X,XXX,XXX.XX patterns to Indian notation."""
    import re
    
    def _replace_match(match):
        raw = match.group(0)
        # Remove ₹ prefix, commas, and parse
        numeric_str = raw.replace("₹", "").replace(",", "").strip()
        try:
            amount = float(numeric_str)
            return format_inr_lakh(amount)
        except ValueError:
            return raw
    
    # Match patterns like ₹1,800,000.00 or ₹75,000 or ₹360000
    pattern = r'₹[\d,]+(?:\.\d+)?'
    return re.sub(pattern, _replace_match, text)
