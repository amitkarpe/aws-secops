"""Harmless exact backend for the Phase 0B.3 Gateway Policy experiment."""


def lambda_handler(event, context):
    environment = event.get("environment")
    if environment != "dev":
        raise ValueError("only the synthetic dev input is accepted")

    return {
        "result": "HARMLESS_LAMBDA_OK",
        "environment": "dev",
        "effect": "none",
    }
