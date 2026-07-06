from exceptions.payments import BusinessException


class NotificationNotFoundException(BusinessException):
    pass


class EmailDeliveryException(BusinessException):
    pass


class TemplateRenderException(BusinessException):
    pass
