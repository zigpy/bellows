from zigpy.exceptions import APIException, ControllerException


class EzspError(APIException):
    pass


class InvalidCommandError(EzspError):
    pass


class InvalidCommandPayload(InvalidCommandError):
    def __init__(self, msg: str, raw_bytes: bytes) -> None:
        super().__init__(msg)
        self.raw_bytes = raw_bytes


class ControllerError(ControllerException):
    pass


class StackAlreadyRunning(EzspError):
    pass
