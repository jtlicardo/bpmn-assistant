class ProcessException(Exception):
    pass


class ElementNotFoundException(ProcessException):
    pass


class ElementAlreadyExistsError(ProcessException):
    pass


class GatewayUpdateError(ProcessException):
    pass
