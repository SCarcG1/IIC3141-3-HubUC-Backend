from app.models.weekly_timeblock import WeeklyTimeblock
from app.schemas.weekday import Weekday
from datetime import datetime


def map_int_weekday_to_enum_weekday(weekday: int):
    if weekday == 0:
        return Weekday.MONDAY
    elif weekday == 1:
        return Weekday.TUESDAY
    elif weekday == 2:
        return Weekday.WEDNESDAY
    elif weekday == 3:
        return Weekday.THURSDAY
    elif weekday == 4:
        return Weekday.FRIDAY
    elif weekday == 5:
        return Weekday.SATURDAY
    elif weekday == 6:
        return Weekday.SUNDAY
    raise ValueError("Invalid weekday value")


def does_weekly_timeblock_contain_date_time(weekly_timeblock: WeeklyTimeblock, time: datetime) -> bool:
    weekday_number = time.weekday()
    weekday = map_int_weekday_to_enum_weekday(weekday_number)
    if time < weekly_timeblock.valid_from:
        return False
    if weekly_timeblock.weekday != weekday:
        return False
    if time.hour < weekly_timeblock.start_hour:
        return False
    if time.hour > weekly_timeblock.end_hour:
        return False
    if time.hour == weekly_timeblock.end_hour and (time.minute > 0 or time.second > 0):
        return False
    if time > weekly_timeblock.valid_until:
        return False
    return True


def get_weekly_timeblocks_that_contain_date_time(
    weekly_timeblocks: list[WeeklyTimeblock], date_time: datetime
) -> list[WeeklyTimeblock]:
    return [
        weekly_timeblock
        for weekly_timeblock in weekly_timeblocks
        if does_weekly_timeblock_contain_date_time(weekly_timeblock, date_time)
    ]


def are_timeblocks_contiguous(
    start_timeblock: WeeklyTimeblock,
    end_timeblock: WeeklyTimeblock,
    all_timeblocks: list[WeeklyTimeblock]
) -> bool:
    return True


def are_start_time_and_end_time_inside_contiguous_timeblocks(
    start_time: datetime,
    end_time: datetime,
    weekly_timeblocks: list[WeeklyTimeblock],
):
    weekly_timeblocks_compatible_with_start_time = get_weekly_timeblocks_that_contain_date_time(
        time=start_time,
        weekly_timeblocks=weekly_timeblocks,
    )
    weekly_timeblocks_compatible_with_end_time = get_weekly_timeblocks_that_contain_date_time(
        time=end_time,
        weekly_timeblocks=weekly_timeblocks,
    )
    for start_timeblock in weekly_timeblocks_compatible_with_start_time:
        for end_timeblock in weekly_timeblocks_compatible_with_end_time:
            if are_timeblocks_contiguous(start_timeblock, end_timeblock, all_timeblocks=weekly_timeblocks):
                return True
    return False
