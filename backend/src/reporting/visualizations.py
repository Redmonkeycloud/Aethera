"""Visualization utilities for generating charts and graphs from analysis results."""

from __future__ import annotations

import base64
import io
from typing import Any, Dict, List, Optional
from pathlib import Path

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.colors import LinearSegmentedColormap
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from ..logging_utils import get_logger

logger = get_logger(__name__)


class VisualizationGenerator:
    """Generate charts and visualizations for reports."""

    def __init__(self) -> None:
        if not MATPLOTLIB_AVAILABLE:
            logger.warning("matplotlib not available. Visualizations will be disabled.")
            logger.warning("Install with: pip install matplotlib")

    def score_bar_chart(
        self,
        scores: Dict[str, float],
        title: str = "Assessment Scores",
        output_path: Optional[Path] = None,
    ) -> Optional[bytes]:
        """
        Create a horizontal bar chart for scores (0-100 scale).

        Args:
            scores: Dictionary of metric_name -> score (0-100)
            title: Chart title
            output_path: Optional path to save the image

        Returns:
            PNG image bytes or None if matplotlib not available
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            metrics = list(scores.keys())
            values = list(scores.values())
            
            # Color bars based on score ranges
            colors = []
            for val in values:
                if val >= 70:
                    colors.append('#d32f2f')  # Red - high impact/risk
                elif val >= 40:
                    colors.append('#f57c00')  # Orange - medium
                else:
                    colors.append('#388e3c')  # Green - low

            bars = ax.barh(metrics, values, color=colors)
            
            # Add value labels on bars
            for i, (bar, val) in enumerate(zip(bars, values)):
                width = bar.get_width()
                ax.text(width + 1, bar.get_y() + bar.get_height()/2,
                       f'{val:.1f}', ha='left', va='center', fontweight='bold')
            
            ax.set_xlabel('Score (0-100)', fontsize=12, fontweight='bold')
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            ax.set_xlim(0, 100)
            ax.grid(axis='x', alpha=0.3, linestyle='--')
            
            # Add legend
            legend_elements = [
                mpatches.Patch(facecolor='#388e3c', label='Low (0-40)'),
                mpatches.Patch(facecolor='#f57c00', label='Medium (40-70)'),
                mpatches.Patch(facecolor='#d32f2f', label='High (70-100)'),
            ]
            ax.legend(handles=legend_elements, loc='lower right')
            
            plt.tight_layout()
            
            if output_path:
                fig.savefig(output_path, dpi=150, bbox_inches='tight')
                plt.close(fig)
                return None
            
            # Return as bytes
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            plt.close(fig)
            return buf.read()

        except Exception as e:
            logger.error("Error creating score bar chart: %s", e)
            plt.close('all')
            return None

    def emissions_comparison_chart(
        self,
        emissions: Dict[str, float],
        title: str = "Carbon Emissions Comparison",
        output_path: Optional[Path] = None,
    ) -> Optional[bytes]:
        """
        Create a bar chart comparing different emission sources.

        Args:
            emissions: Dictionary of emission_type -> tCO2e value
            title: Chart title
            output_path: Optional path to save the image

        Returns:
            PNG image bytes or None
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            categories = list(emissions.keys())
            values = list(emissions.values())
            
            bars = ax.bar(categories, values, color='#1976d2', alpha=0.8)
            
            # Add value labels on bars
            for bar, val in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{val:.2f}', ha='center', va='bottom', fontweight='bold')
            
            ax.set_ylabel('tCO₂e', fontsize=12, fontweight='bold')
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            ax.grid(axis='y', alpha=0.3, linestyle='--')
            
            # Rotate x-axis labels if needed
            plt.xticks(rotation=45, ha='right')
            
            plt.tight_layout()
            
            if output_path:
                fig.savefig(output_path, dpi=150, bbox_inches='tight')
                plt.close(fig)
                return None
            
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            plt.close(fig)
            return buf.read()

        except Exception as e:
            logger.error("Error creating emissions chart: %s", e)
            plt.close('all')
            return None

    def score_radar_chart(
        self,
        scores: Dict[str, float],
        title: str = "Multi-Dimensional Assessment",
        output_path: Optional[Path] = None,
    ) -> Optional[bytes]:
        """
        Create a radar/spider chart for multiple scores.

        Args:
            scores: Dictionary of metric_name -> score (0-100)
            title: Chart title
            output_path: Optional path to save the image

        Returns:
            PNG image bytes or None
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            import numpy as np
            
            categories = list(scores.keys())
            values = list(scores.values())
            N = len(categories)
            
            # Compute angle for each category
            angles = [n / float(N) * 2 * np.pi for n in range(N)]
            angles += angles[:1]  # Complete the circle
            
            values += values[:1]  # Complete the circle
            
            fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
            
            # Plot
            ax.plot(angles, values, 'o-', linewidth=2, color='#1976d2')
            ax.fill(angles, values, alpha=0.25, color='#1976d2')
            
            # Add category labels
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories, fontsize=11)
            
            # Set y-axis (0-100)
            ax.set_ylim(0, 100)
            ax.set_yticks([20, 40, 60, 80, 100])
            ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=10)
            ax.grid(True, linestyle='--', alpha=0.7)
            
            ax.set_title(title, size=16, fontweight='bold', pad=20)
            
            plt.tight_layout()
            
            if output_path:
                fig.savefig(output_path, dpi=150, bbox_inches='tight')
                plt.close(fig)
                return None
            
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            plt.close(fig)
            return buf.read()

        except Exception as e:
            logger.error("Error creating radar chart: %s", e)
            plt.close('all')
            return None

    def score_to_base64(self, image_bytes: bytes) -> str:
        """Convert image bytes to base64 data URI."""
        if not image_bytes:
            return ""
        encoded = base64.b64encode(image_bytes).decode('utf-8')
        return f"data:image/png;base64,{encoded}"

    def generate_score_scale_image(
        self,
        score: float,
        label: str,
        output_path: Optional[Path] = None,
    ) -> Optional[bytes]:
        """
        Generate a visual scale/gauge showing a single score.

        Args:
            score: Score value (0-100)
            label: Label for the score
            output_path: Optional path to save

        Returns:
            PNG image bytes or None
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            fig, ax = plt.subplots(figsize=(8, 4))
            
            # Create a horizontal bar as a scale
            ax.barh([0], [100], height=0.3, color='#e0e0e0', alpha=0.5)
            
            # Color the score portion
            if score >= 70:
                color = '#d32f2f'  # Red
            elif score >= 40:
                color = '#f57c00'  # Orange
            else:
                color = '#388e3c'  # Green
            
            ax.barh([0], [score], height=0.3, color=color, alpha=0.8)
            
            # Add score marker
            ax.plot([score, score], [-0.2, 0.2], 'k-', linewidth=3)
            ax.text(score, 0.4, f'{score:.1f}', ha='center', va='bottom',
                   fontsize=16, fontweight='bold')
            
            ax.text(50, -0.5, label, ha='center', va='top', fontsize=12, fontweight='bold')
            
            ax.set_xlim(0, 100)
            ax.set_ylim(-0.8, 0.6)
            ax.axis('off')
            
            # Add scale markers
            for x in [0, 25, 50, 75, 100]:
                ax.plot([x, x], [-0.15, -0.05], 'k-', linewidth=1)
                ax.text(x, -0.2, str(x), ha='center', va='top', fontsize=9)
            
            plt.tight_layout()
            
            if output_path:
                fig.savefig(output_path, dpi=150, bbox_inches='tight')
                plt.close(fig)
                return None
            
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            plt.close(fig)
            return buf.read()

        except Exception as e:
            logger.error("Error creating score scale: %s", e)
            plt.close('all')
            return None

