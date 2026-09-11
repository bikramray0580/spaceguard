"""Covariance validation, projection, and uncertainty assessment APIs.

This package intentionally does not calculate a collision probability.
"""

from .assessment import UncertaintyAssessment, UncertaintyProvenance, assess_uncertainty
from .covariance import Covariance
from .cross_covariance import CrossCovariance
from .quality_flags import UncertaintyQuality, UncertaintyStatus

__all__ = ["Covariance", "CrossCovariance", "UncertaintyAssessment", "UncertaintyProvenance", "UncertaintyQuality", "UncertaintyStatus", "assess_uncertainty"]
