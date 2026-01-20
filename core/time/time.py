# pip install leapseconddata
from datetime import datetime, timezone, timedelta
from leapseconddata import LeapSecondData

class TimeUtils:
    """TimeUtils class

    A leap second was inserted at the end of the day on June 30, 2012, to account for the gradual slowing of the
    Earth's rotation relative to the highly precise atomic clocks.

    What happened:
    - The adjustment: At 23:59:59 Coordinated Universal Time (UTC) on June 30, 2012, a 61st second was added to the
        minute before the time ticked over to 00:00:00 on July 1. This was the 25th leap second to be added since 1972.

    - Widespread server issues: The addition of this extra second caused widespread issues across the internet,
        including crashes and service outages for major websites and services that used the Linux operating system.

    - Affected companies: Websites affected by the "leap second bug" included LinkedIn, Reddit, Mozilla, Yelp,
        StumbleUpon, and Foursquare. The disruption also affected Qantas Airlines' flight reservation systems,
        causing delays.

    - Technical cause: Many computer systems, particularly those running on Linux, did not handle the extra second
        properly. Some systems logged the same second twice, confusing the servers and causing a system crash.

    The official source for announcements:
    The IERS is responsible for monitoring the Earth's rotation and determining when a leap second is necessary to
    keep Coordinated Universal Time (UTC) and astronomical time (UT1) aligned.
    [IERS Website](www.iers.org)

    """

    @staticmethod
    def now():
        """Returns the current time in UTC timezone."""
        return datetime.now(tz=timezone.utc)

    @staticmethod
    def get_leap_seconds(datatime_obj: datetime, since_leap_seconds_added:bool=False) -> int:
        """Returns the leap second of the current time in seconds.

        How the count is derived:
        - Initial offset: When the leap second system was introduced on January 1, 1972, TAI was exactly 10 seconds
            ahead of UTC.

        - Cumulative additions: Each time a positive leap second is added, the TAI-UTC offset increases by one second.

        - Current offset: The last leap second was added on January 1, 2017. The current TAI-UTC offset has been 37
            seconds since that date. The cumulative count of leap seconds added since 1972 is therefore (37-10=27).
        """
        utc_datetime = datatime_obj.astimezone(tz=timezone.utc)
        # Define the UTC time for which you want to find the offset
        # Let's use the current time (October 27, 2025)
        # utc_datetime = TimeUtils.now()

        # Initialize the leap second data
        leap_second_data = LeapSecondData.from_standard_source()

        # Get the TAI-UTC offset in seconds
        tai_utc_offset = leap_second_data.tai_utc_offset_at(utc_datetime).total_seconds()

        # The number of leap seconds added since 1972 is the offset minus 10
        total_leap_seconds = int(tai_utc_offset - 10) if since_leap_seconds_added else int(tai_utc_offset)
        return total_leap_seconds

    @staticmethod
    def to_tai(datatime_obj: datetime) -> datetime:
        # Get a UTC datetime object
        utc_datetime = datatime_obj.astimezone(tz=timezone.utc)
        # tai_datetime = datetime(tai_datetime.year, tai_datetime.month, tai_datetime.day, tai_datetime.hour, tai_datetime.minute, tai_datetime.second + 37, tzinfo=timezone.utc)

        # Get leap second data from a standard source
        leap_second_data = LeapSecondData.from_standard_source()

        # Convert to TAI
        tai_datetime = leap_second_data.to_tai(utc_datetime)
        return tai_datetime

    @staticmethod
    def from_tai(tai_datetime: datetime) -> datetime:
        # Get a TAI datetime object
        # utc_datetime = datatime_obj.astimezone(tz=timezone.utc)
        datatime_obj = datetime(tai_datetime.year, tai_datetime.month, tai_datetime.day, tai_datetime.hour, tai_datetime.minute, tai_datetime.second + 37, tzinfo=timezone.utc)

        # Get leap second data
        leap_second_data = LeapSecondData.from_standard_source()

        # Convert back to UTC
        utc_datetime = leap_second_data.from_tai(datatime_obj)
        return utc_datetime


# Get the TAI-UTC offset:
utc_datetime = TimeUtils.now()
leap_seconds = TimeUtils.get_leap_seconds(utc_datetime)
print(f"The TAI-UTC offset on {utc_datetime.date()} was: {leap_seconds} seconds.")
leap_seconds = TimeUtils.get_leap_seconds(utc_datetime, True)
print(f"The total number of leap seconds added since 1972 is: {leap_seconds}.")

# Expected output:
# The TAI-UTC offset on 2025-10-27 was: 37.0 seconds.
# The total number of leap seconds added since 1972 is: 27.

# Convert to TAI
utc_datetime = TimeUtils.now()
tai_datetime = TimeUtils.to_tai(utc_datetime)
print(f"UTC: {utc_datetime.isoformat()}")
print(f"TAI: {tai_datetime.isoformat()}")
# Expected output for the example: TAI: 2024-10-27T12:00:37+00:00

# Convert back to UTC
utc_datetime = TimeUtils.from_tai(tai_datetime)
print(f"TAI: {tai_datetime.isoformat()}")
print(f"UTC: {utc_datetime.isoformat()}")
# Expected output for the example: UTC: 2024-10-27T12:00:00+00:00
