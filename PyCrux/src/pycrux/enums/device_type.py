"""Client device categories."""

from .base import CaseInsensitiveEnum


class DeviceType(CaseInsensitiveEnum):
    """Device type from client metadata."""

    DESKTOP = "Desktop"
    MOBILE = "Mobile"
    TABLET = "Tablet"
    TV = "Tv"
