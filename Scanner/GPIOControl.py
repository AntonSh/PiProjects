import RPi.GPIO as GPIO
controlPins = {}

def setup(pins):
	global controlPin
	global controlPinState

        GPIO.setmode(GPIO.BCM)
	for pin in pins:
	        GPIO.setup(pin, GPIO.OUT,  pull_up_down = GPIO.PUD_UP)
                controlPins[pin] = None
                state = switchPin(pin, False)

def switchPin(pin, state): 
	if not pin in controlPins:
		print "not initialized"
		return False

	if controlPins[pin] == state:
		print "value aready set"

	inverted = not state
        GPIO.output(pin, inverted)
        print "Pin {} set to: {}".format(pin, ["HI", "low"][1*inverted])
	controlPins[pin] = state
	return True
