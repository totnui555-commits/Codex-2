"""Shared Temporal transport settings for local services and authenticated cloud clusters."""
from temporalio.client import Client

from .settings import settings


async def connect_temporal():
    config = settings()
    if config.temporal_api_key and not config.temporal_tls:
        raise ValueError("Temporal API-key authentication requires TLS")
    return await Client.connect(
        config.temporal_address,
        namespace=config.temporal_namespace,
        tls=config.temporal_tls,
        api_key=config.temporal_api_key or None,
    )
