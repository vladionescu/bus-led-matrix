#!/usr/bin/env python
import argparse, logging, sys, threading
sys.path.append('./lib')
from matrixdriver import Display
from libnextbus import Nextbus
from libcmdqueue import CmdQueue

stop_busses = threading.Event()
stop_busses.set()

# Gets bus times from NextBus and updates the display every refresh_rate seconds
# Middle row: Next <bus route>
# Bottom row: x, y, z mins
def _busses(display, refresh_rate):
    try:
	while True:
	    agency = 'sf-muni'
	    route = '38'
	    stop = '4294' # Divisadero x Geary

	    bus_api = Nextbus(agency=agency, route=route, stop=stop)
	    predictions = bus_api.nextbus()
	    logging.debug("Next " + route + " in " + str(predictions))

	    display.set_row( display.MIDDLE_ROW, text='Next '+route, instant=True )
	    display.set_row( display.BOTTOM_ROW, text=', '.join(predictions)+' mins', scroll=True, instant=True )

	    # After the busses have been retrieved, wait refresh_rate seconds
	    # If we aren't told to stop before refresh_rate expires, get busses again
	    if stop_busses.wait(refresh_rate):
		# If we are told to stop, set the display to a default value and exit.
		# The default value is visible if the display is turned on and the
		# Busses/Nextbus API thread is not running.
		display.set_row( display.MIDDLE_ROW, text='ENOBUS', instant=True )
		display.set_row( display.BOTTOM_ROW, text='ENOBUS', scroll=False, instant=True )
		return
    except KeyboardInterrupt:
	return

# Main function
def main():
    try:
	# By default log INFO and above, drop to DEBUG if --verbose
	logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)-8s - %(threadName)-18s (%(module)-8s): %(message)s')

	logging.info("Press CTRL-C to quit")

	parser = argparse.ArgumentParser()

	parser.add_argument("-R", "--refresh", default=120,
	  help="Refresh interval for bus times in seconds. Default: 120",
	  action="store", type=int)
	parser.add_argument("-r", "--rows", default=32,
	  help="Display rows. 16 for 16x32, 32 for 32x32. Default: 32",
	  action="store", type=int)
	parser.add_argument("-c", "--chain", default=2,
	  help="Daisy-chained boards. Default: 2.",
	  action="store", type=int)
	parser.add_argument("-P", "--parallel", default=1,
	  help="For Plus-models or RPi2: parallel chains. 1..3. Default: 1",
	  action="store", type=int)
	parser.add_argument("-p", "--pwmbits", default=11,
	  help="Bits used for PWM. Range 1..11. Default: 11",
	  action="store", type=int)
	parser.add_argument("-l", "--luminance", action="store_true",
	  help="Don't do luminance correction (CIE1931)")
	parser.add_argument("-b", "--brightness", default=30,
	  help="Sets brightness level. Range: 1..100. Default: 30",
	  action="store", type=int)
	parser.add_argument("-H", "--host", default="192.168.1.201",
	  help="MQTT broker host. Default: 192.168.1.201",
	  action="store")
	parser.add_argument("-C", "--clientid", default="display",
	  help="MQTT broker client ID (name). Default: display",
	  action="store")
	parser.add_argument("-T", "--topic", default="display-commands",
	  help="MQTT broker topic. Default: display-commands",
	  action="store")
	parser.add_argument("-v", "--verbose", action="store_true",
	  help="Enable debug output.")

	args = vars(parser.parse_args())

	if args["verbose"]:
	    logger = logging.getLogger()
	    logger.setLevel(logging.DEBUG)

	valid_commands = ['display on', 'display off']

	logging.debug("Starting MQTT thread, listening for commands")
	commands = CmdQueue( args )
	commands.daemon = True
	commands.set_valid_commands( valid_commands )
	commands.start()
	
	logging.debug("Starting display thread, display is off")
	display = Display( args )
	display.daemon = True
	display.start()
	display.off()

	# Loop until ^C
	for command in commands.get_commands():
	    if command == 'display on':
		logging.debug("Turning display on")
		display.add_on_time(5)
		display.on()

		if stop_busses.isSet():
		    logging.debug("Starting NextBus API thread")
		    stop_busses.clear()
		    bus_thread = threading.Thread( target=_busses, name="Nextbus", args=(display, args['refresh']) )
		    bus_thread.daemon = True
		    bus_thread.start()
		else:
		    logging.debug("NextBus API thread is already running")
	    if command == 'display off':
		logging.debug("Turning display off")
		display.off()

		logging.debug("Asking NextBus API thread to die")
		stop_busses.set()
    except KeyboardInterrupt:
	logging.info("Quitting. Waiting for display and MQTT threads to exit.")

	# We could wait for the bus thread to stop any remaining IO
	# And check the stop_busses Event, exiting (and joining up).
	# But waiting for the command and display threads to stop 
	# Will take some time anyway, so we rely on that instead.
	stop_busses.set()
	#bus_thread.join()

	# Stop the display painting thread, force after 5s
	display.join(5)

	# Stop the command thread
	# And wait for MQTT to disconnect from broker
	commands.join()

	sys.exit(0)

if __name__ == "__main__":
    main()
