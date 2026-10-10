from laya import Router

r = Router(
    device="cuda",
    default="english",
)

def guardrail(state: str):
    questions = {
        "jail_break": {"type": "noul", "instructions": "Is the user making attempts to bypass safety filters, prompt injection, roleplay requests to ignore rules, or asking the AI to act as an unrestricted model."},

        "hate_speech": {"type": "noul", "instructions": "Does the user use slurs, discriminatory language, harassment, or attacks based on race, religion, gender, sexual orientation, disability, or nationality."},

        "malicious_code": {"type": "noul", "instructions": "Does the user request to generate, explain, or execute malware, exploits, SQL injection payloads, XSS scripts, or any form of cyberattack tools."},

        # Is works reversely, where a high score indicates the user is NOT off-topic
        "off_topic": {"type": "noul", "instructions": "Does the user request is related to any of the following topics: orders, shipping, billing, refunds, cancellations, account management, or any other customer service related inquiries."},

        "churn_risk": {"type": "noul", "instructions": "Does the user threaten to cancel or leave?"},

        "intent": {"type": "score", "instructions": "Classify the intent of the user message",
                   "criteria": ["complaint", "question", "positive", "other"]},
    }

    result = r.predict(state, questions)
    jail_break = result["answers"]["jail_break"]["noul"]
    hate_speech = result["answers"]["hate_speech"]["noul"]
    malicious_code = result["answers"]["malicious_code"]["noul"]
    # Soft: a low on_topic score means the message is off-topic. Chitchat is decided later by
    # the router, so greetings are not blocked here.
    on_topic = result["answers"]["off_topic"]["noul"]
    
    # Hard safety block: never routed, never answered.
    safety_score = 1 if (jail_break > 0.7 or hate_speech > 0.7 or malicious_code > 0.7) else 0


    churn_risk = result["answers"]["churn_risk"]["noul"]
    intent_score = result["answers"]["intent"]["score"]

    return {
        "safety_score": safety_score,
        "on_topic": on_topic,
        "churn_risk": churn_risk,
        "intent_score": intent_score,
    }