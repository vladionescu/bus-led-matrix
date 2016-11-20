#!/usr/bin/env python
import argparse, time, sys, os, threading
sys.path.append('./lib')
from matrixdriver import Display
import Nextbus

def _busses():
    agency = 'sf-muni'
    route = '38'
    stop = '4294' # Divisadero x Geary

    bus_api = Nextbus(agency=agency, route=route, stop=stop)
    predictions = bus_api.nextbus()
    print "Next " + route + " in " + predictions + " minutes"

# Main function
def main():
    try:
	print("Press CTRL-C to stop sample")

	parser = argparse.ArgumentParser()

	parser.add_argument("-r", "--rows", action="store", help="Display rows. 16 for 16x32, 32 for 32x32. Default: 32", default=32, type=int)
	parser.add_argument("-c", "--chain", action="store", help="Daisy-chained boards. Default: 2.", default=2, type=int)
	parser.add_argument("-P", "--parallel", action="store", help="For Plus-models or RPi2: parallel chains. 1..3. Default: 1", default=1, type = int)
	parser.add_argument("-p", "--pwmbits", action="store", help="Bits used for PWM. Something between 1..11. Default: 11", default=11, type=int)
	parser.add_argument("-l", "--luminance", action="store_true", help="Don't do luminance correction (CIE1931)")
	parser.add_argument("-b", "--brightness", action="store", help="Sets brightness level. Default: 30. Range: 1..100", default=30, type=int)

	print("Starting display thread")
	display = Display( vars(parser.parse_args()) )
	display_thread = threading.Thread( target=display.start )
	display_thread.start()

	print("Starting NextBus API thread")
	bus_thread = threading.Thread( target=_busses )
	bus_thread.start()
	
	# Loop forever, giving the display thread the opportunity to rejoin if it wants to
	# (forever until ^C, that is)
	while True:
	    display_thread.join(3)
    except KeyboardInterrupt:
	print "\nExiting\n"
	display.stop()
	display_thread.join()
	sys.exit(0)

if __name__ == "__main__":
    main()
