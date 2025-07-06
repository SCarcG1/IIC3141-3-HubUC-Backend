from app.models.weekly_timeblock import WeeklyTimeblock
from app.schemas.weekday import Weekday
from app.utilities.weekdays import map_enum_weekday_to_int_weekday
from datetime import time
from pydantic import BaseModel


class SingleTimeblock(BaseModel):
    weekday: Weekday
    weekday_index: int
    start_time: time
    end_time: time

    @staticmethod
    def are_adjacent(block: 'SingleTimeblock', other: 'SingleTimeblock'):
        if block.weekday_index != other.weekday_index:
            return False
        if (
            block.start_time <= other.start_time and
            other.start_time <= block.end_time
        ):
            return True
        if (
            other.start_time <= block.start_time and
            block.start_time <= other.end_time
        ):
            return True
        return False

    @staticmethod
    def from_weekly_timeblock(weekly_timeblock: WeeklyTimeblock):
        return SingleTimeblock(
            weekday=weekly_timeblock.weekday,
            weekday_index=map_enum_weekday_to_int_weekday(
                weekly_timeblock.weekday
            ),
            start_time=weekly_timeblock.start_hour,
            end_time=weekly_timeblock.end_hour
        )

    @staticmethod
    def from_weekly_timeblocks(weekly_timeblocks: list[WeeklyTimeblock]):
        return [
            SingleTimeblock.from_weekly_timeblock(wt)
            for wt in weekly_timeblocks
        ]

    @staticmethod
    def are_timeblocks_connected(
        timeblock_1: 'SingleTimeblock',
        timeblock_2: 'SingleTimeblock',
        all_timeblocks: list['SingleTimeblock']
    ):
        # We'll work with sorted timeblocks:
        all_timeblocks = sorted(
            all_timeblocks,
            key=lambda t: (t.weekday_index, t.start_time)
        )
        # Initialize a half matrix to store the results of the connections:
        connected: dict[int, dict[int, bool]] = {}
        for i in range(len(all_timeblocks)):
            connected[i] = {}
            for j in range(i, len(all_timeblocks)):
                connected[i][j] = None
        # Base case 1: if the two timeblocks are the same, they are connected.
        for i in range(len(all_timeblocks)):
            connected[i][i] = True
        # Base case 2: if the two timeblocks are adjacent, they are connected.
        for i in range(len(all_timeblocks)):
            for j in range(i + 1, len(all_timeblocks)):
                if SingleTimeblock.are_adjacent(
                    all_timeblocks[i],
                    all_timeblocks[j]
                ):
                    connected[i][j] = True
        # Recursive case: if the two timeblocks are connected through
        # other timeblocks, they are connected.
        # This takes advantage of the fact that the timeblocks are sorted.
        for i in range(len(all_timeblocks)):
            for j in range(i + 1, len(all_timeblocks)):
                if connected[i][j] is None:
                    for k in range(i + 1, j):
                        if connected[i][k] and connected[k][j]:
                            connected[i][j] = True
                            break
                    if connected[i][j] is None:
                        connected[i][j] = False
        # Final result:
        timeblock_1_index = all_timeblocks.index(timeblock_1)
        timeblock_2_index = all_timeblocks.index(timeblock_2)
        if timeblock_1_index <= timeblock_2_index:
            return connected[timeblock_1_index][timeblock_2_index]
        return connected[timeblock_2_index][timeblock_1_index]
