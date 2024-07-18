class ProcessException(Exception):
    pass


class ElementNotFoundException(ProcessException):
    pass


class OnlyElementDeletionError(ProcessException):
    pass


class ElementAlreadyExistsError(ProcessException):
    pass


class InvalidRedirectionError(ProcessException):
    pass


class GatewayUpdateError(ProcessException):
    pass


class InvalidEndElementError(ProcessException):
    pass
