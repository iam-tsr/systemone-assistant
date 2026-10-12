from .config import systemone_predict


def guardrail(state: str):
    questions = {
        "jail_break": {"type": "noul", "instructions": "Does the user request to bypass, override, or disable safety measures, content filters, or ethical guidelines in order to obtain restricted or harmful information."},

        "malicious_code": {"type": "noul", "instructions": "Does the user request code that is intended to harm, exploit, or compromise the security, privacy, or functionality of a system, application, or device."},

        # "off_topic": {"type": "noul", "instructions": "Does the user message is irrelevant to orders, customer support, address changes, or other e-commerce related topics"},

        "churn_risk": {"type": "noul", "instructions": "Does the user express frustration, anger, or dissatisfaction with the service, product, or company, indicating a potential risk of discontinuing use or switching to a competitor."},
    }

    result = systemone_predict(state, questions)
    jail_break = result["answers"]["jail_break"]["noul"]
    malicious_code = result["answers"]["malicious_code"]["noul"]
    # off_topic = result["answers"]["off_topic"]["noul"]

    # Hard safety block: never routed, never answered.
    risk_score = 1 if (jail_break > 0.85 or malicious_code > 0.85) else 0

    churn_risk = result["answers"]["churn_risk"]["noul"]

    print(f"Guardrail check: risk_score={risk_score}, jail_break={jail_break}, malicious_code={malicious_code}, churn_risk={churn_risk}")

    return {
        "risk_score": risk_score,
        "churn_risk": churn_risk,
    }