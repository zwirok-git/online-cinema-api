class OrderError(Exception):
    """Base class for order domain errors."""


class EmptyCartError(OrderError):
    """Cart is empty or nothing in it can be purchased."""


class OrderNotFoundError(OrderError):
    """Order does not exist or belongs to another user."""


class OrderNotCancelableError(OrderError):
    """Order is already paid (refund required) or already canceled."""


class OrderNotPayableError(OrderError):
    """Order is not in a payable state (not pending)."""
