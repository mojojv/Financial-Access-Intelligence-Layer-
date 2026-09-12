"""Core Domain Exceptions."""

class DomainException(Exception):
    """Base exception for all domain errors."""
    pass


class InvalidValueObjectError(DomainException):
    """Raised when value object constraints are violated."""
    pass


class EntityNotFoundError(DomainException):
    """Raised when an entity cannot be found."""
    pass


class InvalidStateTransitionError(DomainException):
    """Raised when an invalid state transition is attempted on an Aggregate/Entity."""
    pass
