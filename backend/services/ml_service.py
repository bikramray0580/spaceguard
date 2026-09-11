"""Thin ML scoring wrapper for the backend conjunction pipeline.
 
This service only orchestrates the existing ``ml`` module. It does not
duplicate feature extraction or prediction logic. Imports are kept lazy so a
missing ML dependency produces a clear request-time error instead of breaking
backend startup.
"""
 
 
class MLServiceError(RuntimeError):
    """Raised when ML feature extraction or prediction cannot complete."""
 
 
def predict_event_risk(event, states_a, states_b, *, analysis_time):
    """Score one collision-engine event with the existing ML module.
 
    ``event`` must be the actual ``collision_engine.ConjunctionEvent`` object
    (not its dict form) because ``ml.features.build_features`` uses attribute
    access. ``states_a`` and ``states_b`` must be the matching
    ``collision_engine.OrbitalState`` series.
    """
    try:
        from ml.features import build_features
        from ml.predict import predict_features
    except ImportError as error:
        raise MLServiceError(
            "ML dependencies are not installed; check backend/requirements.txt"
        ) from error
 
    try:
        features = build_features(event, states_a, states_b, analysis_time=analysis_time)
        return predict_features(features)
    except Exception as error:
        raise MLServiceError(f"ML prediction failed: {error}") from error