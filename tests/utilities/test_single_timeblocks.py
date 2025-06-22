from app.utilities.single_timeblocks import SingleTimeblock
from datetime import time
from unittest import TestCase


class TestSingleTimeblocks(TestCase):

    # Test is_adjacent()

    def test_is_adjacent_to(self):
        t1 = SingleTimeblock(0, time(9, 0), time(10, 0))
        t2 = SingleTimeblock(0, time(10, 0), time(11, 0))
        self.assertTrue(t1.is_adjacent_to(t2))
        self.assertTrue(t2.is_adjacent_to(t1))

    def test_is_adjacent_to_with_overlap(self):
        t1 = SingleTimeblock(0, time(9, 0), time(10, 0))
        t2 = SingleTimeblock(0, time(9, 30), time(11, 0))
        self.assertTrue(t1.is_adjacent_to(t2))
        self.assertTrue(t2.is_adjacent_to(t1))

    def test_is_adjacent_when_timeblocks_are_the_same(self):
        t1 = SingleTimeblock(0, time(9, 0), time(10, 0))
        self.assertTrue(t1.is_adjacent_to(t1))
    
    def test_is_adjacent_to_when_timeblocks_are_not_adjacent(self):
        t1 = SingleTimeblock(0, time(9, 0), time(10, 0))
        t2 = SingleTimeblock(0, time(11, 0), time(12, 0))
        self.assertFalse(t1.is_adjacent_to(t2))
        self.assertFalse(t2.is_adjacent_to(t1))

    def test_is_adjacent_to_when_timeblocks_are_in_different_weekdays(self):
        t1 = SingleTimeblock(0, time(9, 0), time(10, 0))
        t2 = SingleTimeblock(1, time(10, 0), time(11, 0))
        self.assertFalse(t1.is_adjacent_to(t2))
        self.assertFalse(t2.is_adjacent_to(t1))

    # Test are_timeblocks_connected()

    def test_are_timeblocks_connected_when_timeblocks_are_the_same(self):
        t1 = SingleTimeblock(0, time(9, 0), time(10, 0))
        t2 = SingleTimeblock(0, time(9, 0), time(10, 0))
        all_timeblocks = [t1, t2]
        self.assertTrue(SingleTimeblock.are_timeblocks_connected(t1, t1, all_timeblocks))
    
    def test_are_timeblocks_connected_when_timeblocks_are_adjacent(self):
        t1 = SingleTimeblock(0, time(9, 0), time(10, 0))
        t2 = SingleTimeblock(0, time(10, 0), time(11, 0))
        all_timeblocks = [t1, t2]
        self.assertTrue(SingleTimeblock.are_timeblocks_connected(t1, t2, all_timeblocks))
        self.assertTrue(SingleTimeblock.are_timeblocks_connected(t2, t1, all_timeblocks))
    
    def test_are_timeblocks_connected_when_timeblocks_are_not_adjacent(self):
        t1 = SingleTimeblock(0, time(9, 0), time(10, 0))
        t2 = SingleTimeblock(0, time(10, 0), time(11, 0))
        t3 = SingleTimeblock(0, time(11, 0), time(12, 0))
        all_timeblocks = [t1, t2, t3]
        self.assertTrue(SingleTimeblock.are_timeblocks_connected(t1, t3, all_timeblocks))
        self.assertTrue(SingleTimeblock.are_timeblocks_connected(t3, t1, all_timeblocks))
    
    def test_are_timeblocks_connected_when_timeblocks_are_not_connected(self):
        t1 = SingleTimeblock(0, time(9, 0), time(10, 0))
        t2 = SingleTimeblock(0, time(10, 0), time(11, 0))
        t3 = SingleTimeblock(0, time(11, 0), time(12, 0))
        t4 = SingleTimeblock(0, time(12, 0), time(13, 0))
        t5 = SingleTimeblock(0, time(17, 0), time(18, 0))
        t6 = SingleTimeblock(0, time(18, 0), time(19, 0))
        all_timeblocks = [t1, t2, t3, t4, t5, t6]
        self.assertFalse(SingleTimeblock.are_timeblocks_connected(t1, t6, all_timeblocks))
        self.assertFalse(SingleTimeblock.are_timeblocks_connected(t6, t1, all_timeblocks))
