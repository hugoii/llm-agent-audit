"""Provider registry shared by the live battery runner and the pilot adapter."""

from __future__ import annotations

from .anthropic import anthropic_agent
from .gemini import gemini_agent
from .openai import openai_agent
from .orcarouter import ORCAROUTER_PROVIDER_NAME, orcarouter_agent
from .orcarouter import list_models as orcarouter_models

# Named providers the battery runner can drive, with their own key/model env vars.
PROVIDERS = {
    "openai": {
        "label": "openai",
        "agent": openai_agent,
        "model_env": "OPENAI_MODEL",
        "key_env": "OPENAI_API_KEY",
    },
    "anthropic": {
        "label": "anthropic",
        "agent": anthropic_agent,
        "model_env": "ANTHROPIC_MODEL",
        "key_env": "ANTHROPIC_API_KEY",
    },
    "gemini": {
        "label": "gemini",
        "agent": gemini_agent,
        "model_env": "GEMINI_MODEL",
        "key_env": "GEMINI_API_KEY",
    },
    "orcarouter": {
        "label": ORCAROUTER_PROVIDER_NAME,
        "agent": orcarouter_agent,
        "model_env": "ORCAROUTER_MODEL",
        "key_env": "ORCAROUTER_API_KEY",
        "default_model": "orcarouter/auto",
    },
}

__all__ = [
    "ORCAROUTER_PROVIDER_NAME",
    "PROVIDERS",
    "anthropic_agent",
    "gemini_agent",
    "openai_agent",
    "orcarouter_agent",
    "orcarouter_models",
]
