"""A/B Testing Framework: Compare model versions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

import numpy as np
from psycopg.types.json import Jsonb
from scipy import stats

from ..db.client import DatabaseClient


class ABTestStatus(str, Enum):
    """A/B test status."""

    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class ABTest:
    """Represents an A/B test configuration."""

    test_name: str
    model_a_name: str
    model_a_version: str
    model_b_name: str
    model_b_version: str
    success_metric: str
    traffic_split: float = 0.5
    min_samples: int = 100
    success_threshold: float | None = None
    statistical_test: str = "t_test"
    significance_level: float = 0.05
    description: str | None = None
    status: ABTestStatus = ABTestStatus.DRAFT
    start_date: datetime | None = None
    end_date: datetime | None = None
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    id: UUID | None = None
    model_a_registry_id: UUID | None = None
    model_b_registry_id: UUID | None = None


@dataclass
class ABTestResult:
    """Represents A/B test results for a metric."""

    ab_test_id: UUID
    metric_name: str
    model_a_value: float
    model_b_value: float
    difference: float
    relative_improvement: float | None
    p_value: float | None
    is_significant: bool
    confidence_interval_lower: float | None
    confidence_interval_upper: float | None
    sample_size_a: int
    sample_size_b: int
    evaluated_at: datetime
    id: UUID | None = None


class ABTestManager:
    """Manages A/B tests for model comparison."""

    def __init__(self, db_client: DatabaseClient) -> None:
        """Initialize A/B test manager.

        Args:
            db_client: Database client for persistence
        """
        self.db_client = db_client

    def create_test(
        self,
        test_name: str,
        model_a_name: str,
        model_a_version: str,
        model_b_name: str,
        model_b_version: str,
        success_metric: str,
        traffic_split: float = 0.5,
        min_samples: int = 100,
        success_threshold: float | None = None,
        statistical_test: str = "t_test",
        significance_level: float = 0.05,
        description: str | None = None,
        created_by: str | None = None,
    ) -> ABTest:
        """Create a new A/B test.

        Args:
            test_name: Unique test name
            model_a_name: Control model name
            model_a_version: Control model version
            model_b_name: Treatment model name
            model_b_version: Treatment model version
            success_metric: Primary metric to compare
            traffic_split: Percentage of traffic to model B (0-1)
            min_samples: Minimum samples before evaluation
            success_threshold: Minimum improvement to consider B better
            statistical_test: Statistical test method
            significance_level: Significance level (e.g., 0.05)
            description: Optional description
            created_by: User creating the test

        Returns:
            Created A/B test
        """
        ab_test = ABTest(
            test_name=test_name,
            model_a_name=model_a_name,
            model_a_version=model_a_version,
            model_b_name=model_b_name,
            model_b_version=model_b_version,
            success_metric=success_metric,
            traffic_split=traffic_split,
            min_samples=min_samples,
            success_threshold=success_threshold,
            statistical_test=statistical_test,
            significance_level=significance_level,
            description=description,
            created_by=created_by,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                # Get model registry IDs
                cur.execute(
                    "SELECT id FROM model_registry WHERE model_name = %s AND version = %s",
                    (model_a_name, model_a_version),
                )
                a_row = cur.fetchone()
                ab_test.model_a_registry_id = a_row[0] if a_row else None

                cur.execute(
                    "SELECT id FROM model_registry WHERE model_name = %s AND version = %s",
                    (model_b_name, model_b_version),
                )
                b_row = cur.fetchone()
                ab_test.model_b_registry_id = b_row[0] if b_row else None

                # Insert test
                cur.execute(
                    """
                    INSERT INTO model_ab_tests (
                        id, test_name, description, model_a_registry_id, model_b_registry_id,
                        model_a_name, model_a_version, model_b_name, model_b_version,
                        status, traffic_split, min_samples, success_metric, success_threshold,
                        statistical_test, significance_level, created_by, created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING id, created_at, updated_at
                    """,
                    (
                        uuid4(),
                        ab_test.test_name,
                        ab_test.description,
                        ab_test.model_a_registry_id,
                        ab_test.model_b_registry_id,
                        ab_test.model_a_name,
                        ab_test.model_a_version,
                        ab_test.model_b_name,
                        ab_test.model_b_version,
                        ab_test.status.value,
                        ab_test.traffic_split,
                        ab_test.min_samples,
                        ab_test.success_metric,
                        ab_test.success_threshold,
                        ab_test.statistical_test,
                        ab_test.significance_level,
                        ab_test.created_by,
                        ab_test.created_at,
                        ab_test.updated_at,
                    ),
                )
                row = cur.fetchone()
                ab_test.id = row[0]
                ab_test.created_at = row[1]
                ab_test.updated_at = row[2]

        return ab_test

    def start_test(self, test_id: UUID) -> ABTest:
        """Start an A/B test.

        Args:
            test_id: Test ID

        Returns:
            Updated A/B test
        """
        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE model_ab_tests
                    SET status = %s, start_date = %s, updated_at = %s
                    WHERE id = %s
                    RETURNING id, test_name, description, model_a_registry_id, model_b_registry_id,
                              model_a_name, model_a_version, model_b_name, model_b_version,
                              status, traffic_split, min_samples, success_metric, success_threshold,
                              statistical_test, significance_level, created_by, start_date, end_date,
                              created_at, updated_at
                    """,
                    (
                        ABTestStatus.RUNNING.value,
                        datetime.now(timezone.utc),
                        datetime.now(timezone.utc),
                        test_id,
                    ),
                )
                row = cur.fetchone()
                if not row:
                    raise ValueError(f"A/B test {test_id} not found")

                return self._row_to_test(row)

    def evaluate_test(
        self,
        test_id: UUID,
        model_a_results: list[float] | np.ndarray,
        model_b_results: list[float] | np.ndarray,
        metric_name: str | None = None,
    ) -> ABTestResult:
        """Evaluate A/B test results.

        Args:
            test_id: Test ID
            model_a_results: Results from model A
            model_b_results: Results from model B
            metric_name: Metric name (uses test's success_metric if None)

        Returns:
            A/B test result
        """
        # Get test configuration
        test = self.get_test(test_id)
        if not test:
            raise ValueError(f"A/B test {test_id} not found")

        metric = metric_name or test.success_metric

        a_array = np.array(model_a_results)
        b_array = np.array(model_b_results)

        # Calculate statistics
        a_mean = np.mean(a_array)
        b_mean = np.mean(b_array)
        difference = b_mean - a_mean
        relative_improvement = (difference / a_mean * 100) if a_mean != 0 else None

        # Perform statistical test
        p_value, is_significant, ci_lower, ci_upper = self._perform_statistical_test(
            a_array, b_array, test.statistical_test, test.significance_level
        )

        result = ABTestResult(
            ab_test_id=test_id,
            metric_name=metric,
            model_a_value=float(a_mean),
            model_b_value=float(b_mean),
            difference=float(difference),
            relative_improvement=float(relative_improvement) if relative_improvement else None,
            p_value=float(p_value) if p_value else None,
            is_significant=is_significant,
            confidence_interval_lower=float(ci_lower) if ci_lower else None,
            confidence_interval_upper=float(ci_upper) if ci_upper else None,
            sample_size_a=len(a_array),
            sample_size_b=len(b_array),
            evaluated_at=datetime.now(timezone.utc),
        )

        # Save result
        self._save_result(result)

        return result

    def get_test(self, test_id: UUID) -> ABTest | None:
        """Get an A/B test.

        Args:
            test_id: Test ID

        Returns:
            A/B test or None
        """
        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, test_name, description, model_a_registry_id, model_b_registry_id,
                           model_a_name, model_a_version, model_b_name, model_b_version,
                           status, traffic_split, min_samples, success_metric, success_threshold,
                           statistical_test, significance_level, created_by, start_date, end_date,
                           created_at, updated_at
                    FROM model_ab_tests
                    WHERE id = %s
                    """,
                    (test_id,),
                )
                row = cur.fetchone()
                if not row:
                    return None

                return self._row_to_test(row)

    def list_tests(
        self,
        status: ABTestStatus | str | None = None,
        limit: int = 100,
    ) -> list[ABTest]:
        """List A/B tests.

        Args:
            status: Filter by status
            limit: Maximum number of results

        Returns:
            List of A/B tests
        """
        conditions = []
        params: list[Any] = []

        if status:
            status_value = status.value if isinstance(status, ABTestStatus) else status
            conditions.append("status = %s")
            params.append(status_value)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        params.append(limit)

        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT id, test_name, description, model_a_registry_id, model_b_registry_id,
                           model_a_name, model_a_version, model_b_name, model_b_version,
                           status, traffic_split, min_samples, success_metric, success_threshold,
                           statistical_test, significance_level, created_by, start_date, end_date,
                           created_at, updated_at
                    FROM model_ab_tests
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    tuple(params),
                )
                rows = cur.fetchall()
                return [self._row_to_test(row) for row in rows]

    def get_test_results(self, test_id: UUID) -> list[ABTestResult]:
        """Get results for an A/B test.

        Args:
            test_id: Test ID

        Returns:
            List of test results
        """
        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, ab_test_id, metric_name, model_a_value, model_b_value,
                           difference, relative_improvement, p_value, is_significant,
                           confidence_interval_lower, confidence_interval_upper,
                           sample_size_a, sample_size_b, evaluated_at
                    FROM model_ab_test_results
                    WHERE ab_test_id = %s
                    ORDER BY evaluated_at DESC
                    """,
                    (test_id,),
                )
                rows = cur.fetchall()
                return [self._row_to_result(row) for row in rows]

    def _perform_statistical_test(
        self,
        a: np.ndarray,
        b: np.ndarray,
        test_type: str,
        significance_level: float,
    ) -> tuple[float | None, bool, float | None, float | None]:
        """Perform statistical test between two samples.

        Args:
            a: Sample A
            b: Sample B
            test_type: Test type ('t_test', 'mann_whitney')
            significance_level: Significance level

        Returns:
            Tuple of (p_value, is_significant, ci_lower, ci_upper)
        """
        if test_type == "t_test":
            statistic, p_value = stats.ttest_ind(a, b)
            is_significant = p_value < significance_level

            # Calculate confidence interval
            a_se = stats.sem(a)
            b_se = stats.sem(b)
            se_diff = np.sqrt(a_se**2 + b_se**2)
            t_critical = stats.t.ppf(1 - significance_level / 2, len(a) + len(b) - 2)
            mean_diff = np.mean(b) - np.mean(a)
            ci_lower = mean_diff - t_critical * se_diff
            ci_upper = mean_diff + t_critical * se_diff

            return float(p_value), is_significant, float(ci_lower), float(ci_upper)

        elif test_type == "mann_whitney":
            statistic, p_value = stats.mannwhitneyu(a, b, alternative="two-sided")
            is_significant = p_value < significance_level
            # No simple CI for Mann-Whitney
            return float(p_value), is_significant, None, None

        else:
            raise ValueError(f"Unknown statistical test: {test_type}")

    def _save_result(self, result: ABTestResult) -> None:
        """Save A/B test result to database."""
        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO model_ab_test_results (
                        id, ab_test_id, metric_name, model_a_value, model_b_value,
                        difference, relative_improvement, p_value, is_significant,
                        confidence_interval_lower, confidence_interval_upper,
                        sample_size_a, sample_size_b, evaluated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING id
                    """,
                    (
                        uuid4(),
                        result.ab_test_id,
                        result.metric_name,
                        result.model_a_value,
                        result.model_b_value,
                        result.difference,
                        result.relative_improvement,
                        result.p_value,
                        result.is_significant,
                        result.confidence_interval_lower,
                        result.confidence_interval_upper,
                        result.sample_size_a,
                        result.sample_size_b,
                        result.evaluated_at,
                    ),
                )
                row = cur.fetchone()
                result.id = row[0]

    def _row_to_test(self, row: tuple) -> ABTest:
        """Convert database row to ABTest."""
        return ABTest(
            id=row[0],
            test_name=row[1],
            description=row[2],
            model_a_registry_id=row[3],
            model_b_registry_id=row[4],
            model_a_name=row[5],
            model_a_version=row[6],
            model_b_name=row[7],
            model_b_version=row[8],
            status=ABTestStatus(row[9]),
            traffic_split=float(row[10]),
            min_samples=int(row[11]),
            success_metric=row[12],
            success_threshold=float(row[13]) if row[13] else None,
            statistical_test=row[14],
            significance_level=float(row[15]),
            created_by=row[16],
            start_date=row[17],
            end_date=row[18],
            created_at=row[19],
            updated_at=row[20],
        )

    def _row_to_result(self, row: tuple) -> ABTestResult:
        """Convert database row to ABTestResult."""
        return ABTestResult(
            id=row[0],
            ab_test_id=row[1],
            metric_name=row[2],
            model_a_value=float(row[3]),
            model_b_value=float(row[4]),
            difference=float(row[5]),
            relative_improvement=float(row[6]) if row[6] else None,
            p_value=float(row[7]) if row[7] else None,
            is_significant=bool(row[8]),
            confidence_interval_lower=float(row[9]) if row[9] else None,
            confidence_interval_upper=float(row[10]) if row[10] else None,
            sample_size_a=int(row[11]),
            sample_size_b=int(row[12]),
            evaluated_at=row[13],
        )

