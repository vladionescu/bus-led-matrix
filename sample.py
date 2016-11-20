#!/usr/bin/env python
import argparse, time, sys, os, threading
sys.path.append('./lib')
from matrixdriver import Display
from libnextbus import Nextbus

get_busses = threading.Event()
stop_busses = threading.Event()

# Gets bus times from NextBus and updates the display every refresh_rate seconds
# Middle row: Next <bus number>
# Bottom row: x, y, z mins
def _busses(display, refresh_rate):
    while True:
	while get_busses.isSet():
	    agency = 'sf-muni'
	    route = '38'
	    stop = '4294' # Divisadero x Geary

	    bus_api = Nextbus(agency=agency, route=route, stop=stop)
	    predictions = bus_api.nextbus()
	    print "Next " + route + " in "
	    print predictions

	    display.set_row( display.MIDDLE_ROW, text='Next '+route, instant=True )
	    display.set_row( display.BOTTOM_ROW, text=', '.join(predictions)+' mins', scroll=True, instant=True )

	    for i in xrange(refresh_rate):
		if stop_busses.isSet():
		    return

		time.sleep(1)

# Main function
def main():
    try:
	print("Press CTRL-C to stop sample")

	parser = argparse.ArgumentParser()

	parser.add_argument("-R", "--refresh", action="store", help="Refresh interval for bus times in seconds. Default: 120", default=120, type=int)
	parser.add_argument("-r", "--rows", action="store", help="Display rows. 16 for 16x32, 32 for 32x32. Default: 32", default=32, type=int)
	parser.add_argument("-c", "--chain", action="store", help="Daisy-chained boards. Default: 2.", default=2, type=int)
	parser.add_argument("-P", "--parallel", action="store", help="For Plus-models or RPi2: parallel chains. 1..3. Default: 1", default=1, type = int)
	parser.add_argument("-p", "--pwmbits", action="store", help="Bits used for PWM. Something between 1..11. Default: 11", default=11, type=int)
	parser.add_argument("-l", "--luminance", action="store_true", help="Don't do luminance correction (CIE1931)")
	parser.add_argument("-b", "--brightness", action="store", help="Sets brightness level. Default: 30. Range: 1..100", default=30, type=int)

	args = vars(parser.parse_args())

	print("Starting display thread")
	display = Display( args )
	display_thread = threading.Thread( target=display.start )
	display_thread.start()

	print("Starting NextBus API thread")
	bus_thread = threading.Thread( target=_busses, args=(display, args['refresh']) )
	get_busses.set()
	bus_thread.start()
	
	# Loop forever, giving the display thread the opportunity to rejoin if it wants to
	# (forever until ^C, that is)
	while True:
	    display_thread.join(3)
    except KeyboardInterrupt:
	print "\nExiting\n"
	display.stop()
	stop_busses.set()
	display_thread.join()
	bus_thread.join()
	sys.exit(0)

if __name__ == "__main__":
    main()
