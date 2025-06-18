from app.models.weekly_timeblock import WeeklyTimeblock
from app.schemas.weekday import Weekday
from datetime import datetime


def map_int_weekday_to_enum_weekday(weekday_number: int):
    if weekday_number == 0:
        return Weekday.MONDAY
    elif weekday_number == 1:
        return Weekday.TUESDAY
    elif weekday_number == 2:
        return Weekday.WEDNESDAY
    elif weekday_number == 3:
        return Weekday.THURSDAY
    elif weekday_number == 4:
        return Weekday.FRIDAY
    elif weekday_number == 5:
        return Weekday.SATURDAY
    elif weekday_number == 6:
        return Weekday.SUNDAY
    raise ValueError("Invalid weekday value")


def does_weekly_timeblock_contain_date_time(weekly_timeblock: WeeklyTimeblock, date_time: datetime):
    weekday_number = date_time.weekday()
    weekday = map_int_weekday_to_enum_weekday(weekday_number)
    if date_time < weekly_timeblock.valid_from:
        return False
    if weekly_timeblock.weekday != weekday:
        return False
    if date_time.time() < weekly_timeblock.start_hour:
        return False
    if date_time.time() > weekly_timeblock.end_hour:
        return False
    if date_time > weekly_timeblock.valid_until:
        return False
    return True


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
    weekly_timeblocks_that_contain_start_time = [
        weekly_timeblock
        for weekly_timeblock in weekly_timeblocks
        if does_weekly_timeblock_contain_date_time(weekly_timeblock, start_time)
    ]
    weekly_timeblocks_that_contain_end_time = [
        weekly_timeblock
        for weekly_timeblock in weekly_timeblocks
        if does_weekly_timeblock_contain_date_time(weekly_timeblock, end_time)
    ]
    for start_timeblock in weekly_timeblocks_that_contain_start_time:
        for end_timeblock in weekly_timeblocks_that_contain_end_time:
            if are_timeblocks_contiguous(
                start_timeblock, end_timeblock, all_timeblocks=weekly_timeblocks
            ):
                return True
    return False
