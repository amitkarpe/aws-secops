"""Server-owned catalog for the two implemented AWS compliance controls."""
from __future__ import annotations

from copy import deepcopy

CONTROL_CATALOG = {
    "s3-bucket-level-public-access-prohibited": {
        "resource_type": "S3_BUCKET",
        "config_resource_type": "AWS::S3::Bucket",
        "family": "S3_BPA",
        "action": "set_bucket_bpa",
        "executor": "start_batch_execution",
        "provider_postcondition": "all four bucket-level Block Public Access settings are true",
        "operator_family": "s3",
    },
    "restricted-ssh": {
        "resource_type": "SECURITY_GROUP",
        "config_resource_type": "AWS::EC2::SecurityGroup",
        "family": "SG_RESTRICTED_SSH",
        "action": "remove_unrestricted_ssh",
        "executor": "start_sg_batch_execution",
        "provider_postcondition": "no TCP/22 ingress from 0.0.0.0/0",
        "operator_family": "sg",
    },
}


def get_control(control: str) -> dict[str, str]:
    if control not in CONTROL_CATALOG:
        raise ValueError("unsupported control")
    return deepcopy(CONTROL_CATALOG[control])


def public_catalog() -> dict[str, dict[str, str]]:
    return deepcopy(CONTROL_CATALOG)
