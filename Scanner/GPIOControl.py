import RPi.GPIO as GPIO
initialized = False
controlPin = -1
controlPinState = False

def setup(pin):
	global controlPin
	global controlPinState
	global initialized

	controlPin = pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(controlPin, GPIO.OUT,  pull_up_down = GPIO.PUD_UP)
        initialized = True
	controlPinState = switchPin(controlPin, False)

def switchPin(pin, state): 
	if not initialized:
		print "not initialized"
		return False

	inverted = not state
        GPIO.output(pin, inverted)
        print "Pin {} set to: {}".format(pin, inverted)
	return state
