class UserExceptions(Exception):
    pass


class UserDoesNotExists(UserExceptions):
    pass


class UserAlreadyExists(UserExceptions):
    pass


class UserNotActivated(UserExceptions):
    pass


class UserAlreadyActivated(UserExceptions):
    pass


class GroupDoesNotExist(UserExceptions):
    pass


class InvalidCredentials(UserExceptions):
    pass


class PermissionDenied(UserExceptions):
    pass


class TokenExceptions(Exception):
    pass


class TokenAlreadyExists(TokenExceptions):
    pass


class TokenNotExists(TokenExceptions):
    pass


class TokenExpired(TokenExceptions):
    pass


class TokenInvalid(TokenExceptions):
    pass
