from zigpy.exceptions import APIException, ControllerException, FormationFailure


class EzspError(APIException):
    pass


class InvalidCommandError(EzspError):
    pass


class PayloadTooLongError(InvalidCommandError):
    pass


class InvalidCommandPayload(InvalidCommandError):
    def __init__(self, msg: str, raw_bytes: bytes) -> None:
        super().__init__(msg)
        self.raw_bytes = raw_bytes


class ControllerError(ControllerException):
    pass


class StackAlreadyRunning(EzspError):
    pass


class InvalidTxPower(FormationFailure):
    """The radio does not support the requested TX power."""
