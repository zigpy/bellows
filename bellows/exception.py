from zigpy.exceptions import ZigbeeException


class BellowsException(ZigbeeException):
    pass


class EzspError(BellowsException):
    pass


class ControllerError(BellowsException):
    pass
