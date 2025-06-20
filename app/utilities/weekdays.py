from app.schemas.weekday import Weekday


def map_enum_weekday_to_int_weekday(weekday: Weekday):
    if weekday == Weekday.MONDAY:
        return 0
    elif weekday == Weekday.TUESDAY:
        return 1
    elif weekday == Weekday.WEDNESDAY:
        return 2
    elif weekday == Weekday.THURSDAY:
        return 3
    elif weekday == Weekday.FRIDAY:
        return 4
    elif weekday == Weekday.SATURDAY:
        return 5
    elif weekday == Weekday.SUNDAY:
        return 6
    raise ValueError("Invalid weekday value")


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
