class MovieError(Exception):


class MovieNotFoundError(MovieError):


class MovieAlreadyExistsError(MovieError):


class MovieHasPurchasesError(MovieError):


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
