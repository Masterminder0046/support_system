def classify_issue(subject, body):
    text = (subject + " " + body).lower()
    if "delay" in text or "late" in text:
        return "order_delay"
    elif "payment" in text or "card" in text or "transaction" in text:
        return "payment_failed"
    elif "return" in text or "refund" in text or "exchange" in text:
        return "return_request"
    else:
        return "general"
