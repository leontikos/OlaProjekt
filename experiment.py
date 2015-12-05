# -*- coding: utf-8 -*-
import sys  
reload(sys)  
sys.setdefaultencoding('utf8')

# import from psychopy
#from psychopy import visual, event, gui, core
#import os

# imports
import settings as st
import scale

# Create a window
win = visual.Window()

scale.draw()


q1 = [rating, decisionTime, choiceHistory]
for i in q1:
    st.exp['i'] = i