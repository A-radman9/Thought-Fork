# Copyright 2026 — Apache 2.0 License

"""Tests for Fork dataclass, stance resolution, and ForkConfig."""

from thought_fork.config import BUILT_IN_STANCES, ForkConfig
from thought_fork.fork import Fork, get_stance_prompt


class TestFork:
    """Tests for the Fork dataclass."""

    def test_fork_creation(self):
        fork = Fork(id="A", stance="cautious", system_prompt="Be careful.")
        assert fork.id == "A"
        assert fork.stance == "cautious"
        assert fork.system_prompt == "Be careful."
        assert fork.output == ""
        assert fork.token_count == 0
        assert fork.duration_ms == 0

    def test_fork_with_output(self):
        fork = Fork(
            id="B",
            stance="creative",
            system_prompt="Think laterally.",
            output="Here is a creative answer.",
            token_count=42,
            duration_ms=1500,
        )
        assert fork.output == "Here is a creative answer."
        assert fork.token_count == 42
        assert fork.duration_ms == 1500


class TestStanceResolution:
    """Tests for get_stance_prompt()."""

    def test_builtin_stance_resolves(self):
        prompt = get_stance_prompt("cautious")
        assert "cautious" in prompt.lower() or "risk" in prompt.lower()
        assert len(prompt) > 20

    def test_all_builtin_stances_resolve(self):
        for stance_name in BUILT_IN_STANCES:
            prompt = get_stance_prompt(stance_name)
            assert isinstance(prompt, str)
            assert len(prompt) > 10

    def test_custom_stance_passes_through(self):
        custom = "You are a pirate. Reason like a pirate."
        result = get_stance_prompt(custom)
        assert result == custom

    def test_unknown_stance_passes_through(self):
        result = get_stance_prompt("nonexistent_stance")
        assert result == "nonexistent_stance"


class TestForkConfig:
    """Tests for ForkConfig."""

    def test_default_config(self):
        config = ForkConfig(api_key="test-key")
        assert "haiku" in config.fork_model.lower() or "claude" in config.fork_model.lower()
        assert "sonnet" in config.synthesis_model.lower() or "claude" in config.synthesis_model.lower()
        assert config.max_tokens > 0
        assert len(config.default_stances) == 3
        assert "cautious" in config.default_stances

    def test_custom_config(self):
        config = ForkConfig(
            api_key="test-key",
            fork_model="custom/model-a",
            synthesis_model="custom/model-b",
            max_tokens=512,
            default_stances=["optimistic", "contrarian"],
        )
        assert config.fork_model == "custom/model-a"
        assert config.max_tokens == 512
        assert len(config.default_stances) == 2

    def test_api_base_url_default(self):
        config = ForkConfig(api_key="test-key")
        assert "openrouter" in config.api_base_url


class TestBuiltInStances:
    """Tests for the BUILT_IN_STANCES dictionary."""

    def test_has_seven_stances(self):
        assert len(BUILT_IN_STANCES) == 7

    def test_expected_stances_present(self):
        expected = [
            "cautious", "creative", "critical", "pragmatic",
            "first-principles", "optimistic", "contrarian",
        ]
        for stance in expected:
            assert stance in BUILT_IN_STANCES, f"Missing stance: {stance}"

    def test_all_prompts_are_nonempty_strings(self):
        for name, prompt in BUILT_IN_STANCES.items():
            assert isinstance(prompt, str), f"{name} prompt is not a string"
            assert len(prompt) > 20, f"{name} prompt is too short"
