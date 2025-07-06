from app.models.weekly_timeblock import WeeklyTimeblock
from app.schemas.single_timeblock import SingleTimeblock
from app.utilities.weekdays import map_int_weekday_to_enum_weekday
from datetime import datetime


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


def are_start_time_and_end_time_inside_connected_timeblocks(
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
    all_timeblocks = [SingleTimeblock.from_weekly_timeblock(wt) for wt in weekly_timeblocks]
    for start_weekly_timeblock in weekly_timeblocks_that_contain_start_time:
        start_timeblock = SingleTimeblock.from_weekly_timeblock(start_weekly_timeblock)
        for end_weekly_timeblock in weekly_timeblocks_that_contain_end_time:
            end_timeblock = SingleTimeblock.from_weekly_timeblock(end_weekly_timeblock)
            if SingleTimeblock.are_timeblocks_connected(start_timeblock, end_timeblock, all_timeblocks):
                return True
    return False
