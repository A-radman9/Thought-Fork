# Copyright 2026 Thought Fork Contributors — Apache 2.0 License

"""Tests for ForkResult and synthesize() function signature."""

import inspect

from thought_fork import synthesize, ForkResult, Fork, ForkConfig
from thought_fork.result import ForkResult as ForkResultDirect


class TestForkResult:
    """Tests for the ForkResult dataclass."""

    def test_creation_minimal(self):
        result = ForkResult(synthesis="Merged answer.")
        assert result.synthesis == "Merged answer."
        assert result.forks == {}
        assert result.fork_details == []
        assert result.token_usage == {}
        assert result.duration_ms == 0

    def test_creation_full(self):
        result = ForkResult(
            synthesis="The cautious fork found risks...",
            forks={"cautious": "Risk analysis here.", "creative": "Novel idea here."},
            fork_details=[
                {"id": "A", "stance": "cautious", "output": "Risk analysis here.", "token_count": 100, "duration_ms": 500},
                {"id": "B", "stance": "creative", "output": "Novel idea here.", "token_count": 120, "duration_ms": 450},
            ],
            token_usage={"forks": 220, "synthesis": 150, "total": 370},
            duration_ms=2000,
        )
        assert result.forks["cautious"] == "Risk analysis here."
        assert result.forks["creative"] == "Novel idea here."
        assert len(result.fork_details) == 2
        assert result.token_usage["total"] == 370
        assert result.duration_ms == 2000

    def test_forks_dict_access(self):
        result = ForkResult(
            synthesis="merged",
            forks={"cautious": "safe", "creative": "bold", "critical": "skeptical"},
        )
        assert "cautious" in result.forks
        assert result.forks["creative"] == "bold"
        assert len(result.forks) == 3

    def test_token_usage_structure(self):
        usage = {"forks": 500, "synthesis": 200, "total": 700}
        result = ForkResult(synthesis="answer", token_usage=usage)
        assert result.token_usage["forks"] == 500
        assert result.token_usage["synthesis"] == 200
        assert result.token_usage["total"] == result.token_usage["forks"] + result.token_usage["synthesis"]

    def test_import_consistency(self):
        """ForkResult imported from __init__ is the same class as from result.py."""
        assert ForkResult is ForkResultDirect


class TestSynthesizeSignature:
    """Tests for the synthesize() function interface (without calling the API)."""

    def test_synthesize_is_callable(self):
        assert callable(synthesize)

    def test_synthesize_is_async(self):
        assert inspect.iscoroutinefunction(synthesize)

    def test_synthesize_accepts_expected_params(self):
        sig = inspect.signature(synthesize)
        param_names = list(sig.parameters.keys())
        assert "prompt" in param_names
        assert "fork_count" in param_names
        assert "stances" in param_names
        assert "forks" in param_names
        assert "config" in param_names

    def test_synthesize_defaults(self):
        sig = inspect.signature(synthesize)
        assert sig.parameters["fork_count"].default == 3
        assert sig.parameters["stances"].default is None
        assert sig.parameters["forks"].default is None
        assert sig.parameters["config"].default is None


class TestPublicAPI:
    """Test that all expected names are importable."""

    def test_imports(self):
        from thought_fork import (
            synthesize,
            Fork,
            ForkConfig,
            ForkManager,
            ForkResult,
            SynthesisEngine,
            BUILT_IN_STANCES,
            get_stance_prompt,
            SYNTHESIS_SYSTEM_PROMPT,
            SYNTHESIS_USER_TEMPLATE,
            FORK_OUTPUT_TEMPLATE,
        )
        # All imports succeeded
        assert True


class TestConfigValidation:
    """Tests for the new ForkConfig validation and fields."""

    def test_missing_api_key_raises(self):
        """ForkConfig should raise ValueError when no API key is available."""
        import os
        # Temporarily clear env vars
        old_or = os.environ.pop("OPENROUTER_API_KEY", None)
        old_oai = os.environ.pop("OPENAI_API_KEY", None)
        try:
            import pytest
            with pytest.raises(ValueError, match="No API key found"):
                ForkConfig(api_base_url="https://api.openai.com/v1")
        finally:
            if old_or is not None:
                os.environ["OPENROUTER_API_KEY"] = old_or
            if old_oai is not None:
                os.environ["OPENAI_API_KEY"] = old_oai

    def test_local_url_bypasses_api_key_check(self):
        """ForkConfig should NOT raise ValueError for local URLs without an API key."""
        import os
        old_or = os.environ.pop("OPENROUTER_API_KEY", None)
        old_oai = os.environ.pop("OPENAI_API_KEY", None)
        try:
            # This should not raise
            config = ForkConfig(api_base_url="http://localhost:11434/v1")
            assert config.api_key is None
            
            config2 = ForkConfig(api_base_url="http://127.0.0.1:8000/v1")
            assert config2.api_key is None
        finally:
            if old_or is not None:
                os.environ["OPENROUTER_API_KEY"] = old_or
            if old_oai is not None:
                os.environ["OPENAI_API_KEY"] = old_oai

    def test_explicit_api_key_works(self):
        config = ForkConfig(api_key="test-key-123")
        assert config.api_key == "test-key-123"

    def test_synthesis_max_tokens_default(self):
        config = ForkConfig(api_key="test-key")
        assert config.synthesis_max_tokens == 6144
        assert config.max_tokens == 2048

    def test_timeout_seconds_default(self):
        config = ForkConfig(api_key="test-key")
        assert config.timeout_seconds == 120.0


class TestPublicConstants:
    """Test that synthesis constants are accessible as public API."""

    def test_synthesis_system_prompt_is_string(self):
        from thought_fork import SYNTHESIS_SYSTEM_PROMPT
        assert isinstance(SYNTHESIS_SYSTEM_PROMPT, str)
        assert len(SYNTHESIS_SYSTEM_PROMPT) > 50

    def test_synthesis_user_template_has_placeholders(self):
        from thought_fork import SYNTHESIS_USER_TEMPLATE
        assert "{fork_count}" in SYNTHESIS_USER_TEMPLATE
        assert "{prompt}" in SYNTHESIS_USER_TEMPLATE

    def test_fork_output_template_has_placeholders(self):
        from thought_fork import FORK_OUTPUT_TEMPLATE
        assert "{fork_id}" in FORK_OUTPUT_TEMPLATE
        assert "{stance}" in FORK_OUTPUT_TEMPLATE

