"""Signal scoring API."""

from .composite import WEIGHTS, ScoreBreakdown, compute_score
from .verdict import Verdict, bucket

__all__ = ["Verdict", "bucket", "compute_score", "ScoreBreakdown", "WEIGHTS"]
