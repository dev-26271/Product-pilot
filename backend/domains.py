import re
from typing import Dict, Any

# Supported domains
DOMAINS = [
    "SaaS Platform",
    "Mobile Application",
    "Website",
    "Marketplace",
    "Physical Consumer Product",
    "Hardware / IoT",
    "AI Product / AI Platform",
    "Healthcare Product",
    "Enterprise Software",
    "Service Business"
]

def detect_domain(idea: str, intent_context: Dict[str, Any] = None) -> str:
    """Classifies a project idea or intent context into one of the 10 supported domains."""
    # 1. Check intent_context product_type first
    if intent_context:
        prod_val = intent_context.get("product_type", {})
        if isinstance(prod_val, dict):
            prod_type = prod_val.get("value", "")
        else:
            prod_type = str(prod_val)
            
        industry_val = intent_context.get("industry", {})
        if isinstance(industry_val, dict):
            industry = industry_val.get("value", "")
        else:
            industry = str(industry_val)
            
        if "healthcare" in industry.lower() or "medical" in industry.lower():
            return "Healthcare Product"
            
        for d in DOMAINS:
            if d.lower() in prod_type.lower() or prod_type.lower() in d.lower():
                return d
                
        # Shorthand mapping
        if "mobile" in prod_type.lower() or "app" in prod_type.lower():
            return "Mobile Application"
        if "marketplace" in prod_type.lower():
            return "Marketplace"
        if "saas" in prod_type.lower() or "platform" in prod_type.lower():
            return "SaaS Platform"
        if "ai" in prod_type.lower() or "assistant" in prod_type.lower():
            return "AI Product / AI Platform"

    # 2. Check idea keywords
    idea_lower = idea.lower()
    if any(w in idea_lower for w in ["healthcare", "medical", "patient", "clinical", "ehr", "emr", "doctor"]):
        return "Healthcare Product"
    if any(w in idea_lower for w in ["ai ", " llm", "machine learning", "neural", "model", "gpt", "chatbot", "generator", "predictive"]):
        return "AI Product / AI Platform"
    if any(w in idea_lower for w in ["marketplace", "buyer", "seller", "double-sided", "transaction platform"]):
        return "Marketplace"
    if any(w in idea_lower for w in ["iot", "hardware", "device", "sensor", "wearable", "firmware", "connected device"]):
        return "Hardware / IoT"
    if any(w in idea_lower for w in ["towel", "shoes", "bottle", "apparel", "clothing", "furniture", "packaging", "consumer product", "fabric"]):
        return "Physical Consumer Product"
    if any(w in idea_lower for w in ["consulting", "agency", "cleaning service", "repair service", "service business"]):
        return "Service Business"
    if any(w in idea_lower for w in ["enterprise", "erp", "crm", "internal tool", "dashboard", "b2b"]):
        return "Enterprise Software"
    if any(w in idea_lower for w in ["website", "landing page", "web page"]):
        return "Website"
    if any(w in idea_lower for w in ["mobile app", "ios app", "android app"]):
        return "Mobile Application"
        
    return "SaaS Platform"  # Default

# Domain Specific Prompt Additions
DOMAIN_PROMPT_ADDITIONS = {
    "SaaS Platform": """
This is a SaaS Platform. Define functional requirements for tenancy isolation, user onboarding, database scaling, API authentication, and RBAC roles.
NFRs must focus on: Latency (under 200ms), Availability (99.9% uptime), and Security (TLS encryption). Do NOT include physical manufacturing or materials rules.
""",
    "Mobile Application": """
This is a Mobile Application. Define requirements for app store compliance, push notifications, offline local database storage, and platform support (iOS/Android).
NFRs must focus on: Battery drain, start-up latency, and responsiveness. Do NOT include physical manufacturing rules.
""",
    "Website": """
This is a Website. Define requirements for SEO indexing, fast asset delivery (CDN), responsive layouts, and cross-browser accessibility.
NFRs must focus on: Time-to-First-Byte (TTFB), page speed score, and responsive layout scaling.
""",
    "Marketplace": """
This is a double-sided Marketplace. Define requirements for Buyer Flow, Seller Flow, Matchmaking algorithms, Payments settlement, Commission splits, and Trust & Safety / Moderation workflows.
NFRs must focus on: Transaction processing speed, transaction volume scalability, and fraud detection metrics.
""",
    "Physical Consumer Product": """
This is a Physical Consumer Product (e.g. consumer goods, apparel, household items). 
You MUST include these keys at the top-level of your output JSON:
- "Materials_and_Dimensions": "Core materials used, texture, weight, dimensions, and manufacturing tolerances."
- "Manufacturing_Requirements": "Sourcing, mass production specifications, assembly rules, and cost targets."
- "Packaging_and_Logistics": "Retail package requirements, shipping parameters, and shelf life."
- "Durability_and_Safety": "Stress tests, hazard preventions, safety certifications, and wash cycles."
- "Supply_Chain_and_Cost_Targets": "Cost of Goods Sold (COGS), supply logistics, and target pricing."
- "Certifications": "Regulatory compliance, labeling certifications, and ecological badges."

Do NOT include software requirements like database schemas, TLS encryption, REST APIs, or online dashboards. NFRs must focus on: wash cycles durability, drop-test height, shelf-life, and weight limit.
""",
    "Hardware / IoT": """
This is a Hardware / IoT device. You MUST include these keys at the top-level of your output JSON:
- "Hardware_Specs": "Processor, hardware layout, sensors, memory, and physical dimensions."
- "Connectivity_and_Power": "BLE/Wi-Fi specifications, battery capacity, power management modes, and offline queues."
- "Compliance_and_Manufacturing": "FCC/CE testing, PCB design safety, assembly lines, and firmware flashing."

Ensure requirements specify firmware update paths (OTA) and device onboarding. NFRs must focus on: battery lifecycle, connection latency, and waterproof IP rating.
""",
    "AI Product / AI Platform": """
This is an AI / Machine Learning Product. You MUST include these keys at the top-level of your output JSON:
- "Model_Architecture": "Neural model configuration, training dataset specifications, and fine-tuning parameters."
- "Inference_and_Training": "Real-time vs batch inference pipelines, latency thresholds, GPU/CPU scaling, and retraining workflows."
- "Safety_and_Guardrails": "Content filtering systems, safety alignment, drift detection tools, and bias constraints."
- "Hallucination_Controls": "Verification pipelines, fallback mechanisms, grounding vector retrieval, and verification metrics."

NFRs must focus on: Inference latency (under 100ms), model accuracy / F1 score, drift bounds, and hallucination percentages.
""",
    "Healthcare Product": """
This is a Healthcare / Medical Product. You MUST include these keys at the top-level of your output JSON:
- "Clinical_and_EHR_Integration": "EHR integration pipelines (HL7/FHIR), clinical workflows, and intake protocols."
- "HIPAA_and_Patient_Safety": "HIPAA/GDPR compliance mapping, patient safety thresholds, clinical validation criteria, and emergency overrides."
- "Regulatory_and_Audit": "FDA regulatory pathways, strict data access audit logs, and compliance logs."

NFRs must focus on: data-at-rest encryption, zero-data-loss audit trails, and strict availability metrics.
""",
    "Enterprise Software": """
This is Enterprise Software. Define requirements for SSO/SAML integrations, fine-grained access audits, massive data volume backups, and custom workflow engines.
NFRs must focus on: high database query throughput, auditability compliance, and system failover availability.
""",
    "Service Business": """
This is a Service Business (e.g. cleaning, consulting, agency). You MUST include these keys at the top-level of your output JSON:
- "Service_Booking_and_Matching": "Booking scheduler, service provider matching rules, and quality verification standards."
- "Resource_and_Billing": "Billing models, resource allocations, and provider commission structures."

NFRs must focus on: service response intervals, matching accuracy, and customer satisfaction (CSAT) ratings.
"""
}
