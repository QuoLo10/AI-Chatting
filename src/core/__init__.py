"""
Core module for An An Persona Chatbot.
Provides dynamic response length control, persona system prompts, and prompt templates.
"""

from src.core.length_controller import (
    LengthTier,
    LengthDecision,
    determine_response_length,
    TIER_TOKEN_LIMITS,
    TIER_WORD_BOUNDS,
    TIER_EMPIRICAL_RATIOS,
    TIER_GUIDANCE_INSTRUCTIONS,
)
from src.core.prompts import (
    SYSTEM_PROMPT_BASE,
    DEFAULT_LENGTH_GUIDANCE,
    build_system_prompt,
    get_chat_prompt_template,
    get_few_shot_messages,
    format_few_shot_text_block,
)

__all__ = [
    "LengthTier",
    "LengthDecision",
    "determine_response_length",
    "TIER_TOKEN_LIMITS",
    "TIER_WORD_BOUNDS",
    "TIER_EMPIRICAL_RATIOS",
    "TIER_GUIDANCE_INSTRUCTIONS",
    "SYSTEM_PROMPT_BASE",
    "DEFAULT_LENGTH_GUIDANCE",
    "build_system_prompt",
    "get_chat_prompt_template",
    "get_few_shot_messages",
    "format_few_shot_text_block",
]
