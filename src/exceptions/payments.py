class BusinessException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class OrderNotFoundException(BusinessException):
    pass


class OrderAccessDeniedException(BusinessException):
    pass


class InvalidOrderStatusException(BusinessException):
    pass
