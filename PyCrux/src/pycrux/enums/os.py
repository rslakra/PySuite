"""Client operating systems."""

from .base import CaseInsensitiveEnum


class OS(CaseInsensitiveEnum):
    """Operating system from client metadata."""

    ANDROID = "Android"
    IOS = "iOS"
    LINUX = "Linux"
    MACOS = "MacOS"
    WINDOWS = "Windows"
    OTHER = "Other"
