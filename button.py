# -*- coding: utf-8 -*-

# imports
from psychopy       import visual, event, gui, core
from PIL            import Image
from utils          import round2step

import os
import re
import yaml
import numpy  as np
import pandas as pd


def plot_Feedback(stim, plotter, pth, keys=None, wait_time=5, resize=1.0):
	'''
	return feedback image in stim['centerImage']. Does not draw the image.
	'''
	# get file names from
	imfls = plotter.plot(pth)
	if not isinstance(imfls, type([])):
		imfls = [imfls]

	for im in imfls:
		# check image size:
		img = Image.open(im)
		imgsize = np.array(img.size)
		del img

		# clear buffer
		k = event.getKeys()

		# set image
		stim['centerImage'].size = np.round(imgsize * resize)
		stim['centerImage'].setImage(im)
		return stim


class Interface(object):
	exp = None
	stim = None
	def __init__(self, exp, stim, main_win=2):
		self.exp = exp
		self.stim = stim
		self.two_windows = 'window2' in stim
		if self.two_windows:
			main_w = 'window2' if main_win == 2 else 'window'
			sec_w  = 'window'  if main_win == 2 else 'window2'
			self.win = stim[main_w]
			self.win2 = stim[sec_w]

			if self.wait_text:
				self.wait_txt = visual.TextStim(stim[sec_w],
					text=self.wait_text)
				self.wait_txt.draw()
				stim[sec_w].flip()
		else:
			self.win = stim['window']


class ContrastInterface(Interface):

	def __init__(self, exp=None, stim=None, trial=None):
		self.contrast = []

		# monitor setup
		# -------------
		self.wait_text = u'Proszę czekać, trwa dobieranie kontrastu...'	
		super(ContrastInterface, self).__init__(exp, stim)	

		self.win.setMouseVisible(True)
		self.mouse = event.Mouse(win=self.win)

		# change units, size and position of centerImage:
		self.origunits = self.win.units
		self.win.units = 'norm'

		win_pix_size = self.win.size
		pic_pix_size = self.stim['centerImage'].size
		pic_nrm_size = [(p / (w * 1.)) * 2. for (p, w) in
			zip(pic_pix_size, win_pix_size)]
		self.stim['centerImage'].units = 'norm'
		self.stim['centerImage'].setPos((-0.4, 0.4))
		self.stim['centerImage'].setSize([pic_nrm_size])


		button_pos = np.zeros([4,2])
		button_pos[:,0] = 0.7
		button_pos[:,1] = np.linspace(-0.25, -0.8, num=4)
		button_text = [u'kontynuuj', u'zakończ', u'edytuj', '0.1']
		self.buttons = [Button(win=self.win, pos=p, text=t,
			size=(0.35, 0.12)) for p, t in zip(button_pos, button_text)]

		self.buttons[-1].click_fun = self.cycle_vals
		self.grain_vals = [0.1, 0.05, 0.01, 0.005]
		self.current_grain_val = 0
		self.text = visual.TextStim(win=self.win, text='kontrast:\n',
			pos=(0.75, 0.5), units='norm', height=0.1)
		self.text_height = {0: 0.12, 5: 0.1, 9: 0.06, 15: 0.04, 20: 0.03}

		# scale
		self.scale = ClickScale(win=self.win, pos=(0.,-0.8), size=(0.75, 0.1))
		self.edit_mode = False
		self.last_pressed = False


	def draw(self):
		[b.draw() for b in self.buttons]
		if self.buttons[-2].clicked:
			self.scale.draw()
			# TODO: this might be moved to refresh:
			if self.last_pressed:
				step = self.grain_vals[self.current_grain_val]
				self.contrast = round2step(np.array(self.scale.points), step=step)
				txt = 'kontrast:\n' + '\n'.join(map(str, self.contrast))
				num_cntrst = len(self.contrast)
				k = np.sort(self.text_height.keys())
				sel = np.where(np.array(k) <= num_cntrst)[0][-1]
				self.text.setHeight(self.text_height[k[sel]])
				self.text.setText(txt)
				self.last_pressed = False
			self.text.draw()
		self.stim['centerImage'].draw()


	def cycle_vals(self):
		self.current_grain_val += 1
		if self.current_grain_val >= len(self.grain_vals):
			self.current_grain_val = 0
		self.buttons[-1].setText(str(self.grain_vals[self.current_grain_val]))
		# TODO: change contrast values


	def refresh(self):
		if_click = self.check_mouse_click()
		self.last_pressed = if_click
		if not self.edit_mode and self.buttons[-1].clicked:
			self.edit_mode = True
		self.draw()
		self.win.flip()
		if if_click:
			core.wait(0.1)


	def check_mouse_click(self):
		m1, m2, m3 = self.mouse.getPressed()
		if m1:
			self.mouse.clickReset()
			# test buttons
			print "mouse click pos: ", self.mouse.getPos()
			ifclicked = [b.contains(self.mouse) for b in self.buttons]
			which_clicked = np.where(ifclicked)[0]
			if which_clicked.size > 0:
				self.buttons[which_clicked[0]].click()

			# test scale
			self.scale.test_click(self.mouse)
			
		elif m3:
			self.mouse.clickReset()
			self.scale.remove_point(-1)
		return m1 or m3


	def quit(self):
		self.win.setMouseVisible(False)
		self.win.units = self.origunits


class Button:
	'''
	Simple button class, does not check itself, needs to be checked
	in some event loop.

	create buttons
	--------------
	win = visual.Window(monitor="testMonitor")
	button_pos = np.zeros([3,2])
	button_pos[:,0] = 0.5
	button_pos[:,1] = [0.5, 0., -0.5]
	button_text = list('ABC')
	buttons = [Button(win=win, pos=p, text=t) for p, t in
		zip(button_pos, button_text)]

	draw buttons
	------------
	[b.draw() for b in buttons]
	win.flip()

	check if buttons were pressed
	-----------------------------
	mouse = event.Mouse()
    
    #from here it should be closed in a loop (if slider NoResponse==True then the following, else turn_page)
	m1, m2, m3 = mouse.getPressed()
	if m1:
		mouse.clickReset()
		ifclicked = [b.contains(mouse) for b in buttons]
		which_clicked = np.where(ifclicked)[0]
		if which_clicked.size > 0:
			buttons[which_clicked[0]].click()
	'''

	def __init__(self, pos=(0, 0), win=None, size=(0.4, 0.15),
		text='...', box_color=(-0.3, -0.3, -0.3), font_height=0.08,
		units='norm', click_color=(0.2, -0.3, -0.3)):
		self.rect_stim = visual.Rect(win, pos=pos, width=size[0],
			height=size[1], fillColor=box_color, lineColor=box_color,
			units=units)
		self.text_stim = visual.TextStim(win, text=text, pos=pos,
			height=font_height, units=units)
		self.clicked = False
		self.orig_color = box_color
		self.click_color = click_color
		self.click_fun = self.default_click_fun


	def draw(self):
		self.rect_stim.draw()
		self.text_stim.draw()


	def contains(self, obj):
		return self.rect_stim.contains(obj)


	def setText(self, text):
		self.text_stim.setText(text)


	def default_click_fun(self):
		if self.clicked:
			self.clicked = False
			self.rect_stim.setFillColor(self.orig_color)
			self.rect_stim.setLineColor(self.orig_color)
		else:
			self.clicked = True
			self.rect_stim.setFillColor(self.click_color)
			self.rect_stim.setLineColor(self.click_color)


	def click(self):
		self.click_fun()
