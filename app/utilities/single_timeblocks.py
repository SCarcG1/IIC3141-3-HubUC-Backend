from app.models.weekly_timeblock import WeeklyTimeblock
from app.utilities.weekdays import map_enum_weekday_to_int_weekday
from dataclasses import dataclass
from datetime import time


@dataclass
class SingleTimeblock:
    weekday_index: int
    start_time: time
    end_time: time

    def __init__(self, weekly_timeblock: WeeklyTimeblock):
        self.weekday_index = map_enum_weekday_to_int_weekday(weekly_timeblock.weekday)
        self.start_time = weekly_timeblock.start_hour
        self.end_time = weekly_timeblock.end_hour
    
    def is_adjacent_to(self, other: 'SingleTimeblock'):
        if self.weekday_index != other.weekday_index:
            return False
        if self.start_time <= other.start_time and other.start_time <= self.end_time:
            return True
        if other.start_time <= self.start_time and self.start_time <= other.end_time:
            return True            
        return False


def are_timeblocks_connected(
    timeblock_1: SingleTimeblock,
    timeblock_2: SingleTimeblock,
    all_timeblocks: list[SingleTimeblock]
):
    # We'll work with sorted timeblocks:
    all_timeblocks = sorted(all_timeblocks, key=lambda t: (t.weekday_index, t.start_time))
    # Initialize a half matrix to store the results of the connections:
    connected = {}
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
            if all_timeblocks[i].is_adjacent_to(all_timeblocks[j]):
                connected[i][j] = True
    # Recursive case: if the two timeblocks are connected through other timeblocks,
    # they are connected. This takes advantage of the fact that the timeblocks are sorted.
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
        return connected[timeblock_1][timeblock_2]
    return connected[timeblock_2][timeblock_1]
