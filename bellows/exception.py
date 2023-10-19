from zigpy.exceptions import APIException, ControllerException


class EzspError(APIException):
    pass


class InvalidCommandError(EzspError):
    pass


class ControllerError(ControllerException):
    pass


class StackAlreadyRunning(EzspError):
    pass
