import os
import time
import RPi.GPIO as GPIO
USE_HW = True
USE_VIM = True
USE_RPI = False


#### Everything happens here
if __name__ == '__main__':

    if USE_HW:

        if USE_RPI:
            RELAY_PIN = 18 # BCM 18, GPIO.1 physical pin 12
        elif USE_VIM:
            RELAY_PIN = 37

        # Relay is connected NORMALLY CLOSED so gpio.cleanup() leaves it SET.
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(RELAY_PIN,GPIO.OUT)
        # power on on startup
        GPIO.output(RELAY_PIN, GPIO.LOW)
        print("setting GPIO {} to GPIO.LOW".format(RELAY_PIN))
        
        time.sleep(1)
        try:
            GPIO.cleanup()  
        except RuntimeWarning:
            print('Caught warning')

