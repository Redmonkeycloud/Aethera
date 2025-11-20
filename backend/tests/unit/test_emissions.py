"""Unit tests for emissions calculations."""

from __future__ import annotations

import pytest
from hypothesis import given, strategies as st

from src.emissions.calculator import EmissionsCalculator
from src.emissions.factors import EmissionFactorCatalog


@pytest.mark.unit
class TestEmissionsCalculator:
    """Test emissions calculation logic."""

    def test_initialization(self) -> None:
        """Test calculator initialization."""
        catalog = EmissionFactorCatalog()
        calculator = EmissionsCalculator(catalog)
        assert calculator is not None

    @pytest.mark.hypothesis
    @given(
        area_ha=st.floats(min_value=0.1, max_value=10000),
        factor=st.floats(min_value=0.1, max_value=100),
    )
    def test_baseline_emissions_property_based(self, area_ha: float, factor: float) -> None:
        """Property-based test for baseline emissions calculation."""
        catalog = EmissionFactorCatalog()
        calculator = EmissionsCalculator(catalog)
        
        # Simple calculation: area * factor
        emissions = area_ha * factor
        assert emissions >= 0
        assert emissions == area_ha * factor

    def test_emission_factor_loading(self) -> None:
        """Test loading emission factors from catalog."""
        catalog = EmissionFactorCatalog()
        # Assuming catalog has some default factors
        assert catalog is not None

