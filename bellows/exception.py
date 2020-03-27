from zigpy.exceptions import APIException, ControllerException


class EzspError(APIException):
    pass


class ControllerError(ControllerException):
    pass
