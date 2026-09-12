"""Domain Exceptions for Financial Access Intelligence Layer."""

class DomainError(Exception):
    """Base exception for all domain rule violations."""
    pass

# Alias for backward compatibility
DomainException = DomainError


class InvalidDimensionScoreError(DomainError):
    """Raised when a dimension score is out of the valid range [0.0, 100.0]."""
    pass


class InvalidWalletAddressError(DomainError):
    """Raised when a wallet address URL is malformed or non-HTTPS."""
    pass


class ProfileNotFoundError(DomainError):
    """Raised when a requested financial profile identity does not exist."""
    pass


class DomainRuleViolationError(DomainError):
    """Raised when an operation violates a core aggregate invariant."""
    pass


class InvalidStateTransitionError(DomainError):
    """Raised when an entity attempts an unauthorized state transition."""
    pass


class InvalidValueObjectError(DomainError):
    """Raised when value object constraints are violated."""
    pass


class EntityNotFoundError(DomainError):
    """Raised when an entity cannot be found."""
    pass
