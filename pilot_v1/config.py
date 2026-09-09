"""Public-safe Pilot v1 configuration contract."""

from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_REGION = "ap-southeast-1"
DEFAULT_MODEL_ID = "global.amazon.nova-2-lite-v1:0"


@dataclass(frozen=True)
class PilotConfig:
    region: str
    model_id: str
    harness_arn: str
    gateway_url: str
    read_tool_name: str
    remediation_tool_name: str
    s3_tool_name: str

    @classmethod
    def from_env(cls) -> "PilotConfig":
        return cls(
            region=os.getenv("AWS_REGION", DEFAULT_REGION),
            model_id=os.getenv("PILOT_MODEL_ID", DEFAULT_MODEL_ID),
            harness_arn=os.getenv("PILOT_HARNESS_ARN", ""),
            gateway_url=os.getenv("PILOT_GATEWAY_URL", ""),
            read_tool_name=os.getenv("PILOT_SG_READ_TOOL", ""),
            remediation_tool_name=os.getenv("PILOT_SG_REMEDIATE_TOOL", ""),
            s3_tool_name=os.getenv("PILOT_S3_READ_TOOL", ""),
        )

    def require_harness(self) -> None:
        if not self.harness_arn:
            raise ValueError("PILOT_HARNESS_ARN is required")

    def require_gateway(self) -> None:
        if not self.gateway_url.startswith("https://"):
            raise ValueError("PILOT_GATEWAY_URL must be an HTTPS URL")
