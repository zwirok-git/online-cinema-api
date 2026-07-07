class MovieError(Exception):
    pass


class MovieNotFoundError(MovieError):
    pass


class MovieAlreadyExistsError(MovieError):
    pass


class MovieHasPurchasesError(MovieError):
    pass


class GenreNotFoundError(MovieError):
    pass


class StarNotFoundError(MovieError):
    pass


class DirectorNotFoundError(MovieError):
    pass


class CertificationNotFoundError(MovieError):
    pass


class DictionaryItemAlreadyExistsError(MovieError):
    pass


class CommentNotFoundError(MovieError):
    pass


class FavoriteNotFoundError(MovieError):
    pass
