def categorize_email(text:str) -> str:
    t = (text or "").lower()

    if any (k in t for k in ["job", "apply", "interview", "hiring"]):
        return "job"

    if any (k in t for k in ["bank", "statement", "account", "otp" , "transaction"]):
        return "finance"

    if any(k in t for k in ["leave", "policy", "hr", "holiday"]):
        return "hr"

    if any(k in t for k in ["offer", "sale", "discount", "coupon", "deal"]):
        return "promotions"

    if any(k in t for k in ["verify", "security alert", "login attempt"]):
        return "security"

    return "other"