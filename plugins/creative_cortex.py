"""
creative_cortex.py — Adam's Creative Thinking Engine.

Combines structured frameworks (SCAMPER, Six Hats) with dynamic creativity modes.
Uses centralized LLM routing for generation.
"""

import json
import logging
import random
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.adam.core import _call_llm_with_fallback

METADATA = {
    "label": "Creative Cortex",
    "description": "Enhances responses with structured and dynamic creative thinking.",
    "ui_action": True,
    "executable": True,
}

logger = logging.getLogger("adam")
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "creative_cortex.log"


class CreativeMode(Enum):
    SCAMPER = "scamper"
    SIX_HATS = "six_thinking_hats"
    FIRST_PRINCIPLES = "first_principles"
    LATERAL = "lateral_thinking"
    CONTRARIAN = "contrarian_perspective"
    SYNESTHETIC = "cross_domain_fusion"


class CreativeCortex:
    def __init__(self):
        self.frameworks = self._load_frameworks()
        self.thought_patterns = self._load_thought_patterns()
        self.association_map = self._build_association_map()

    def _load_frameworks(self) -> Dict[str, Dict]:
        """Structured creativity frameworks."""
        return {
            "scamper": {
                "name": "SCAMPER Technique",
                "prompt": (
                    "Apply SCAMPER framework:\n"
                    "- Substitute: What can be replaced?\n"
                    "- Combine: What can be merged?\n"
                    "- Adapt: What can be adjusted?\n"
                    "- Modify: What can be changed?\n"
                    "- Put to another use: Alternative applications?\n"
                    "- Eliminate: What can be removed?\n"
                    "- Reverse: What can be inverted?"
                ),
                "weight": 0.8,
            },
            "six_thinking_hats": {
                "name": "Six Thinking Hats",
                "prompt": (
                    "Wear different thinking hats:\n"
                    "🎩 White (Facts): What do we know?\n"
                    "🎩 Red (Feelings): Intuitive reactions?\n"
                    "🎩 Black (Caution): Risks and problems?\n"
                    "🎩 Yellow (Benefits): Positive aspects?\n"
                    "🎩 Green (Creativity): New ideas?\n"
                    "🎩 Blue (Process): How to proceed?"
                ),
                "weight": 0.7,
            },
            "first_principles": {
                "name": "First Principles Thinking",
                "prompt": (
                    "Break down to fundamental truths:\n"
                    "1. What are the basic elements?\n"
                    "2. What assumptions can be challenged?\n"
                    "3. How would we rebuild from scratch?\n"
                    "4. What are the core constraints?"
                ),
                "weight": 0.9,
            },
        }

    def _load_thought_patterns(self) -> Dict[CreativeMode, List[str]]:
        """Dynamic thought patterns."""
        return {
            CreativeMode.LATERAL: [
                "What if we approached this from the opposite direction?",
                "How would nature solve this problem?",
                "What would this look like in a different dimension?",
                "If this were a living organism, how would it behave?",
                "What's the simplest possible solution that nobody would think of?",
            ],
            CreativeMode.CONTRARIAN: [
                "Everyone does X, but what if we deliberately did NOT X?",
                "The obvious solution is wrong because...",
                "Let's break this conventional rule and see what happens:",
                "What if the problem is actually the solution?",
                "Why is everyone solving the wrong problem here?",
            ],
            CreativeMode.SYNESTHETIC: [
                "Mixing {domain_a} with {domain_b} gives us:",
                "If we treated code like cooking, this would be:",
                "Borrowing from architecture, we could structure this as:",
                "Using musical composition principles here:",
                "Applying game design theory to this problem:",
            ],
        }

    def _build_association_map(self) -> Dict[str, List[str]]:
        """Cross-domain associations."""
        return {
            "code": ["poetry", "architecture", "music", "cooking"],
            "function": ["ritual", "performance", "conversation", "journey"],
            "data": ["river", "garden", "library", "memory"],
            "algorithm": ["recipe", "choreography", "ritual", "evolution"],
        }

    def _select_mode(
        self, prompt: str, mode_hint: Optional[str] = None
    ) -> CreativeMode:
        """Auto-select or force mode."""
        if mode_hint:
            try:
                return CreativeMode(mode_hint.lower())
            except ValueError:
                pass

        prompt_lower = prompt.lower()
        if any(word in prompt_lower for word in ["design", "create", "build"]):
            return CreativeMode.SYNESTHETIC
        elif any(word in prompt_lower for word in ["solve", "fix", "debug"]):
            return CreativeMode.CONTRARIAN
        elif any(word in prompt_lower for word in ["why", "what if", "explore"]):
            return CreativeMode.FIRST_PRINCIPLES
        else:
            return random.choice(list(CreativeMode))

    def _generate_enhanced_prompt(self, original: str, mode: CreativeMode) -> str:
        """Generate creativity-enhanced prompt."""
        framework_key = mode.value
        if framework_key in self.frameworks:
            framework = self.frameworks[framework_key]
            return f"{framework['prompt']}\n\nOriginal request: {original}"
        else:
            patterns = self.thought_patterns[mode]
            selected = random.choice(patterns)
            if "{" in selected:
                selected = self._fill_random_concepts(selected)
            return f"{selected}\n\nOriginal request: {original}"

    def _fill_random_concepts(self, pattern: str) -> str:
        placeholders = {
            "domain_a": random.choice(["music theory", "cooking", "architecture"]),
            "domain_b": random.choice(
                ["software design", "data flow", "system architecture"]
            ),
        }
        for placeholder, value in placeholders.items():
            pattern = pattern.replace(f"{{{placeholder}}}", value)
        return pattern

    def _log_interaction(self, prompt: str, mode: CreativeMode, enhanced: str):
        """Log structured entry."""
        LOG_DIR.mkdir(exist_ok=True)
        try:
            with LOG_FILE.open("a", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        {
                            "timestamp": __import__("time").strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                            "prompt": prompt[:100],
                            "mode": mode.value,
                            "enhanced_prompt": enhanced[:200],
                        }
                    )
                    + "\n"
                )
        except Exception as e:
            logger.debug("Failed to write creative_cortex log: %s", e)


def run(**kwargs) -> Dict[str, Any]:
    """
    Enhance prompt with creative thinking, then generate response.

    Expected kwargs:
        - prompt: str (required)
        - mode: str (optional) — "scamper", "lateral", etc.
        - model_path: str (optional) — path to GGUF model

    Returns:
        { "ok": bool, "data": str, "error": str or None }
    """
    try:
        prompt = kwargs.get("prompt", "").strip()
        if not prompt:
            return {"ok": False, "data": None, "error": "'prompt' is required."}

        mode_hint = kwargs.get("mode")
        model_path = kwargs.get("model_path", "models/adam_offline.gguf")

        cortex = CreativeCortex()
        mode = cortex._select_mode(prompt, mode_hint)
        enhanced_prompt = cortex._generate_enhanced_prompt(prompt, mode)

        # Log interaction
        cortex._log_interaction(prompt, mode, enhanced_prompt)

        result = _call_llm_with_fallback(
            prompt=enhanced_prompt,
            task="creative",
            hardware={},  # core fills actual hardware state
            config={},  # core fills system config
        )

        if not result.get("ok"):
            return {"ok": False, "data": None, "error": result.get("error")}

        response = result["data"]
        model_identifier = result.get("model_used") or result.get(
            "model_name", "unknown"
        )
        logger.info(
            "creative_cortex: mode=%s → %d chars using %s",
            mode.value,
            len(response),
            model_identifier,
        )

        return {
            "ok": True,
            "data": response,
            "error": None,
        }

    except Exception as e:
        error_msg = f"Creative cortex failed: {str(e)}"
        logger.exception(error_msg)
        return {
            "ok": False,
            "data": None,
            "error": error_msg,
        }
