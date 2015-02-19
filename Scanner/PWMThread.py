#!/usr/bin/python
from collections import deque
from threading import Thread
from time import sleep 

class PWMThread (Thread):

	# callback for control, single parameter_function(Boolean) is expected 
	# duty cycle in [0,1] range, 
	# time period for which history is kept, 
	# minPulseRatio is ratio of the most frequent swith between states and back 
	def __init__(self, controlCallback, name = "PWMThread" , dutyCycle=0.0, periodSec=600, minPulseRatio=60):
		super(PWMThread, self).__init__(name = name)
		self.setDaemon(True)

		self.history = deque([0], minPulseRatio)
		self.dutyCycle = dutyCycle
		self.minPulseDurationSec = periodSec / minPulseRatio
		self.controlCallback = controlCallback

	def setDutyCycle(self, dutyCycle):
		self.dutyCycle = dutyCycle

	def run(self):
		while (True):
			effectiveDutyCycle = 1.0 * sum(self.history) / len(self.history)
			controlValue = effectiveDutyCycle < self.dutyCycle
			self.controlCallback(controlValue)
			self.history.append(1 * controlValue)
			
			sleep(self.minPulseDurationSec) 