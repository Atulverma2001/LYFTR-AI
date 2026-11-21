class AllProvidersUnavailable(Exception):
    """Every key in the pool failed with a retryable error."""


class InvalidSimulationHeader(ValueError):
    """X-Simulate-Failure could not be parsed."""
