from auth_token.backends import DeviceBackend as OriginDeviceBackend

from chamber.multidomains.auth.backends import GetUserMixin


class DeviceBackend(GetUserMixin, OriginDeviceBackend):
    pass
