# -*- coding: utf-8 -*-

"""Tests for touchpadlib """

import pytest
import types 

from touchpadlib import touchpadlib

def monkey_interrupt_and_finish(self):
    """ Function to moneky patching exiting function.

        It is used to test if something fails"""
    self.ans = -1

#change interupt and finish function for a test
touchpadlib.Touchpadlib.interrupt_and_finish = types.MethodType(monkey_interrupt_and_finish,touchpadlib.Touchpadlib)
touchpadlib.Touchpadlib.ans = 0

tlib = touchpadlib.Touchpadlib

#--- TESTS ---

def test_monkey():
    assert tlib.ans == 0
    tlib.interrupt_and_finish()
    
    assert tlib.ans == -1
    tlib.ans = 0

def test_conncect_to_library():
    global TOUCHPADLIB_SHARED_LIBRARY
    #make it right
    touchpadlib.TOUCHPADLIB_SHARED_LIBRARY = "../../lib/touchpadlib.so"
    tlib.conncect_to_library()
    assert tlib.ans == 0

    #make it wronk
    touchpadlib.TOUCHPADLIB_SHARED_LIBRARY = "sthstupid"
    tlib.conncect_to_library()
    assert tlib.ans == -1
   
    #reset
    tlib.ans = 0
    touchpadlib.TOUCHPADLIB_SHARED_LIBRARY = "../lib/touchpadlib.so"

    
    
