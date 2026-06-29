# Copyright 2026 Ameen Saeed — Apache 2.0 License

"""Tests for ForkResult and synthesize() function signature."""

import sys
import os
import inspect

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from thought_fork import synthesize, ForkResult, Fork
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
        )
        # All imports succeeded
        assert True
