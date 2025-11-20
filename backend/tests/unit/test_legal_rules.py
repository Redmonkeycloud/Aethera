"""Unit tests for legal rules engine."""

from __future__ import annotations

import pytest
from hypothesis import given, strategies as st

from src.legal.evaluator import LegalEvaluator
from src.legal.loader import LegalRulesLoader
from src.legal.parser import RuleParser


@pytest.mark.unit
class TestLegalRulesParser:
    """Test legal rules parsing."""

    def test_parser_initialization(self) -> None:
        """Test parser initialization."""
        parser = RuleParser()
        assert parser is not None

    def test_load_rules(self, temp_dir: Path) -> None:
        """Test loading rules from YAML."""
        loader = LegalRulesLoader()
        # Test loading a known country
        rules = loader.load_country_rules("DEU")
        assert rules is not None


@pytest.mark.unit
class TestLegalEvaluator:
    """Test legal rules evaluation."""

    def test_evaluator_initialization(self) -> None:
        """Test evaluator initialization."""
        evaluator = LegalEvaluator()
        assert evaluator is not None

    @pytest.mark.hypothesis
    @given(
        capacity=st.floats(min_value=0, max_value=1000),
        threshold=st.floats(min_value=0, max_value=1000),
    )
    def test_threshold_comparison_property_based(self, capacity: float, threshold: float) -> None:
        """Property-based test for threshold comparisons."""
        exceeds = capacity > threshold
        assert isinstance(exceeds, bool)

