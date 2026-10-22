import json
from pathlib import Path

teams = {
    "Executive Command": ["chief_of_staff", "portfolio_manager", "technical_architect"],
    "Revenue Lab": [
        "venture_scout",
        "market_intelligence",
        "opportunity_evaluator",
        "product_incubator",
        "pricing",
        "growth_seo",
        "revenue_operations",
        "customer_feedback",
    ],
    "Design Studio": ["business_analyst", "ux_researcher", "ui_designer", "content_brand"],
    "Engineering Lab": ["frontend_engineer", "backend_engineer", "documentation"],
    "Quality & Watchtower": ["qa_engineer", "security_reviewer", "inspector_general", "compliance_privacy"],
    "Operations": ["devops_release", "financial_controller", "support"],
}
roles = []
for floor, keys in teams.items():
    for key in keys:
        roles.append(
            dict(
                id=key,
                role=key.replace("_", " ").title(),
                mission=f"Perform bounded {key.replace('_', ' ')} work and produce independently verifiable evidence.",
                floor=floor,
                version="1.0.0",
                capabilities=[key],
                allowed_tools=["research_search"]
                if key in ["venture_scout", "market_intelligence"]
                else ["scoped_context", "artifact_read"],
                prohibited_actions=[
                    "modify_policy",
                    "self_approve",
                    "unapproved_spend",
                    "production_credentials",
                    "external_outreach",
                ],
                data_scope="assigned_project",
                delegation_rules=["only_configured_roles", "dependency_dag"],
                max_turns=4,
                max_runtime=300,
                max_tokens=8000,
                max_cost={"amount": 30, "currency": "THB"},
                required_artifacts=["source_backed_result"],
                quality_gates=["schema_validation", "independent_review"],
                escalation_policy="founder_inbox_after_bounded_failure",
            )
        )
Path("config/roles.json").write_text(json.dumps(roles, indent=2) + "\n")
