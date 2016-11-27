#!/usr/bin/env python
import argparse, sys, threading
sys.path.append('./lib')
from matrixdriver import Display
from libnextbus import Nextbus
from libcmdqueue import CmdQueue

stop_busses = threading.Event()

# Gets bus times from NextBus and updates the display every refresh_rate seconds until on_time seconds have passwd, then turns off 
# Middle row: Next <bus number>
# Bottom row: x, y, z mins
def _busses(display, refresh_rate):
    try:
	while True:
	    agency = 'sf-muni'
	    route = '38'
	    stop = '4294' # Divisadero x Geary

	    bus_api = Nextbus(agency=agency, route=route, stop=stop)
	    predictions = bus_api.nextbus()
	    print "Next " + route + " in "
	    print predictions

	    display.set_row( display.MIDDLE_ROW, text='Next '+route, instant=True )
	    display.set_row( display.BOTTOM_ROW, text=', '.join(predictions)+' mins', scroll=True, instant=True )

	    # After the busses have been retrieved, wait refresh_rate seconds
	    # If we aren't told to stop in refresh_rate, get busses again
	    if stop_busses.wait(refresh_rate):
#		display.set_row( display.MIDDLE_ROW, text='ENOBUS', instant=True )
#		display.set_row( display.BOTTOM_ROW, text='ENOBUS', scroll=False, instant=True )
		return
    except KeyboardInterrupt:
	return

# Main function
def main():
    try:
	print("Press CTRL-C to quit")

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

	args = vars(parser.parse_args())
	display_on_time = 10

	valid_commands = ['display on', 'display off']

	print("Starting MQTT thread, listening for commands")
	commands = CmdQueue( args )
	commands.daemon = True
	commands.set_valid_commands( valid_commands )
	commands.start()
	
	print("Starting display thread")
	display = Display( args )
	display.daemon = True
	display.start()
	display.off()

	# Loop until ^C
	for command in commands.get_commands():
	    if command == 'display on':
		# TODO move the display thread out of while True.
		# display stuff should be setup with command thread.
		# TODO rearchitect Display() to have on() and off() funcs
		# call those here instead of spawning/killing threads
		print("Turning display on")
		display.on()

		print("Starting NextBus API thread")
		stop_busses.clear()
		bus_thread = threading.Thread( target=_busses, args=(display, args['refresh']) )
		bus_thread.daemon = True
		bus_thread.start()
	    if command == 'display off':
		print("Turning display off")
		display.off()

		stop_busses.set()
    except KeyboardInterrupt:
	print "\nExiting\n"

	stop_busses.set()
	# We could wait for the bus thread to stop any remaining IO
	# And check the stop_busses Event, exiting (and joining up)
	# But waiting for the command and display threads to stop will
	#   take some time anyway, so we'll rely on that instead.
	#bus_thread.join()

	display.join(5)

	# Stop the command thread
	# And wait for MQTT to disconnect from broker
	commands.join()

	sys.exit(0)

if __name__ == "__main__":
    main()
