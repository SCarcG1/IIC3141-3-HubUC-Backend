from app.schemas.single_timeblock import SingleTimeblock
from app.schemas.weekday import Weekday
from datetime import time
from unittest import TestCase


class TestSingleTimeblocks(TestCase):

    # Test are_adjacent()

    def test_are_adjacent(self):
        t1 = SingleTimeblock(
            weekday=Weekday.MONDAY,
            weekday_index=0,
            start_hour=time(9, 0),
            end_hour=time(10, 0)
        )
        t2 = SingleTimeblock(
            weekday=Weekday.MONDAY,
            weekday_index=0,
            start_hour=time(10, 0),
            end_hour=time(11, 0)
        )
        self.assertTrue(SingleTimeblock.are_adjacent(t1, t2))
        self.assertTrue(SingleTimeblock.are_adjacent(t2, t1))

    def test_are_adjacent_with_overlap(self):
        t1 = SingleTimeblock(
            weekday=Weekday.MONDAY,
            weekday_index=0,
            start_hour=time(9, 0),
            end_hour=time(10, 0)
        )
        t2 = SingleTimeblock(
            weekday=Weekday.MONDAY,
            weekday_index=0,
            start_hour=time(9, 30),
            end_hour=time(11, 0)
        )
        self.assertTrue(SingleTimeblock.are_adjacent(t1, t2))
        self.assertTrue(SingleTimeblock.are_adjacent(t2, t1))

    def test_are_adjacent_when_timeblocks_are_the_same(self):
        t1 = SingleTimeblock(
            weekday=Weekday.MONDAY,
            weekday_index=0,
            start_hour=time(9, 0),
            end_hour=time(10, 0)
        )
        self.assertTrue(SingleTimeblock.are_adjacent(t1, t1))

    def test_are_adjacent_when_timeblocks_are_not_adjacent(self):
        t1 = SingleTimeblock(
            weekday=Weekday.MONDAY,
            weekday_index=0,
            start_hour=time(9, 0),
            end_hour=time(10, 0)
        )
        t2 = SingleTimeblock(
            weekday=Weekday.MONDAY,
            weekday_index=0,
            start_hour=time(11, 0),
            end_hour=time(12, 0)
        )
        self.assertFalse(SingleTimeblock.are_adjacent(t1, t2))
        self.assertFalse(SingleTimeblock.are_adjacent(t2, t1))

    def test_are_adjacent_when_timeblocks_are_in_different_weekdays(self):
        t1 = SingleTimeblock(
            weekday=Weekday.MONDAY,
            weekday_index=0,
            start_hour=time(9, 0),
            end_hour=time(10, 0)
        )
        t2 = SingleTimeblock(
            weekday=Weekday.TUESDAY,
            weekday_index=1,
            start_hour=time(10, 0),
            end_hour=time(11, 0)
        )
        self.assertFalse(SingleTimeblock.are_adjacent(t1, t2))
        self.assertFalse(SingleTimeblock.are_adjacent(t2, t1))

    # Test are_timeblocks_connected()

    def test_are_timeblocks_connected_when_timeblocks_are_the_same(self):
        t1 = SingleTimeblock(
            weekday=Weekday.MONDAY,
            weekday_index=0,
            start_hour=time(9, 0),
            end_hour=time(10, 0)
        )
        t2 = SingleTimeblock(
            weekday=Weekday.MONDAY,
            weekday_index=0,
            start_hour=time(9, 0),
            end_hour=time(10, 0)
        )
        all_timeblocks = [t1, t2]
        self.assertTrue(SingleTimeblock.are_timeblocks_connected(
            t1, t1, all_timeblocks
        ))

    def test_are_timeblocks_connected_when_timeblocks_are_adjacent(self):
        t1 = SingleTimeblock(
            weekday=Weekday.MONDAY,
            weekday_index=0,
            start_hour=time(9, 0),
            end_hour=time(10, 0)
        )
        t2 = SingleTimeblock(
            weekday=Weekday.MONDAY,
            weekday_index=0,
            start_hour=time(10, 0),
            end_hour=time(11, 0)
        )
        all_timeblocks = [t1, t2]
        self.assertTrue(SingleTimeblock.are_timeblocks_connected(
            t1, t2, all_timeblocks
        ))
        self.assertTrue(SingleTimeblock.are_timeblocks_connected(
            t2, t1, all_timeblocks
        ))

    def test_are_timeblocks_connected_when_timeblocks_are_not_adjacent(self):
        t1 = SingleTimeblock(
            weekday=Weekday.MONDAY,
            weekday_index=0,
            start_hour=time(9, 0),
            end_hour=time(10, 0)
        )
        t2 = SingleTimeblock(
            weekday=Weekday.MONDAY,
            weekday_index=0,
            start_hour=time(10, 0),
            end_hour=time(11, 0)
        )
        t3 = SingleTimeblock(
            weekday=Weekday.MONDAY,
            weekday_index=0,
            start_hour=time(11, 0),
            end_hour=time(12, 0)
        )
        all_timeblocks = [t1, t2, t3]
        self.assertTrue(SingleTimeblock.are_timeblocks_connected(
            t1, t3, all_timeblocks
        ))
        self.assertTrue(SingleTimeblock.are_timeblocks_connected(
            t3, t1, all_timeblocks
        ))

    def test_are_timeblocks_connected_when_timeblocks_are_not_connected(self):
        t1 = SingleTimeblock(
            weekday=Weekday.MONDAY,
            weekday_index=0,
            start_hour=time(9, 0),
            end_hour=time(10, 0)
        )
        t2 = SingleTimeblock(
            weekday=Weekday.MONDAY,
            weekday_index=0,
            start_hour=time(10, 0),
            end_hour=time(11, 0)
        )
        t3 = SingleTimeblock(
            weekday=Weekday.MONDAY,
            weekday_index=0,
            start_hour=time(11, 0),
            end_hour=time(12, 0)
        )
        t4 = SingleTimeblock(
            weekday=Weekday.MONDAY,
            weekday_index=0,
            start_hour=time(12, 0),
            end_hour=time(13, 0)
        )
        t5 = SingleTimeblock(
            weekday=Weekday.MONDAY,
            weekday_index=0,
            start_hour=time(17, 0),
            end_hour=time(18, 0)
        )
        t6 = SingleTimeblock(
            weekday=Weekday.MONDAY,
            weekday_index=0,
            start_hour=time(18, 0),
            end_hour=time(19, 0)
        )
        all_timeblocks = [t1, t2, t3, t4, t5, t6]
        self.assertFalse(SingleTimeblock.are_timeblocks_connected(
            t1, t6, all_timeblocks
        ))
        self.assertFalse(SingleTimeblock.are_timeblocks_connected(
            t6, t1, all_timeblocks
        ))
