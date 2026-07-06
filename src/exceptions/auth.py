class UserExceptions(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class UserAlreadyExists(UserExceptions):
    pass


class GroupDoesNotExist(UserExceptions):
    pass


class UserDoesNotExists(UserExceptions):
    pass


class UserAlreadyActivated(UserExceptions):
    pass


class InvalidCredentials(UserExceptions):
    pass


class UserNotActivated(UserExceptions):
    pass


class InvalidOldPassword(UserExceptions):
    pass


class TokenExceptions(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class TokenDoesNotExists(TokenExceptions):
    pass


class TokenAlreadyExpired(TokenExceptions):
    pass


class InvalidToken(TokenExceptions):
    pass
