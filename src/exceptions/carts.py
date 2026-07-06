class CartError(Exception):
    """Base class for cart domain errors."""


class MovieAlreadyPurchasedError(CartError):
    """Movie has already been purchased by this user."""


class MovieAlreadyInCartError(CartError):
    """Movie is already present in the user's cart."""


class CartItemNotFoundError(CartError):
    """Cart item does not exist in this cart."""
