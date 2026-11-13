"""Shared model configuration for the research agents."""

from agents import ModelSettings

DEFAULT_AGENT_MODEL = "gpt-4.1-mini"


def shared_model_settings() -> ModelSettings:
    """Return consistent conservative settings for all agents."""
    return ModelSettings(temperature=0.1, max_tokens=4000)
