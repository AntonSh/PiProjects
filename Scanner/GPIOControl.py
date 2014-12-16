import RPi.GPIO as GPIO
controlPins = {}
pinMode = {}
pullUpDown = [GPIO.PUD_UP, GPIO.PUD_DOWN]

def setupPin(pin, inverted):
	global controlPin
        global controlPinState
	
	GPIO.setup(pin, GPIO.OUT,  pull_up_down = pullUpDown[inverted])
        pinMode[pin] = inverted
	controlPins[pin] = None
        state = switchPin(pin, False)

def setup(pins):
        GPIO.setmode(GPIO.BCM)
	for pin in pins:
		setupPin(pin, pins[pin])
	       
def switchPin(pin, state): 
	if not pin in controlPins:
		print "not initialized"
		return False

	if controlPins[pin] == state:
		print "value aready set"
		return True

	mode = pinMode[pin]
	value = state ^ mode
        GPIO.output(pin, value)
        print "Pin {} set to: {}".format(pin, ["HI", "low"][1*value])
	controlPins[pin] = state
	return True
