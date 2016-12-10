#!/usr/bin/env python
import argparse, time, sys, os, threading
import Queue
import paho.mqtt.client as mqtt
sys.path.append('./lib')
from matrixdriver import Display
from libnextbus import Nextbus

get_commands = threading.Event()
stop_busses = threading.Event()

# Command slots, max 5 can be queued until the server refuses to queue more
commands_q = Queue.Queue(5)

valid_commands = ['display on', 'display off']

# Command thread, loops listening to the MQTT topic it's subscribed to
def _mqtt_sub():
    BROKER = "192.168.1.201"
    CLIENT_ID = "dobby-display"
    TOPIC = "commands"

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(client, userdata, flags, rc):
	print("Connected with result code "+str(rc))

	# Subscribing in on_connect() means that if we lose the connection and
	# reconnect then subscriptions will be renewed.
	client.subscribe(TOPIC)

    # The callback for when a PUBLISH message is received from the server.
    def on_message(client, userdata, msg):
	print("MQTT rx: "+msg.topic+" ( "+str(msg.payload)+" )")

	message = msg.payload.lower()

	if message in valid_commands:
	    print ("+Q: "+message)

	    # Queue the command, but only if there is a free command slot
	    try:
		commands_q.put(message, False)

		# The display.off() must be called twice, so queue it twice
		#if message == 'display off':
		#    commands_q.put(message, False)
	    except Queue.Full:
		pass

    client = mqtt.Client(client_id=CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER, 1883, 60)

    while get_commands.isSet():
	# Blocking call that processes network traffic, dispatches callbacks and
	# handles reconnecting. Loops every 0.25 seconds.
	client.loop(0.25)
    else:
	# Disconnect cleanly
	client.disconnect()

# Gets bus times from NextBus and updates the display every refresh_rate seconds
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

	get_commands.set()

	print("Starting MQTT thread, listening for commands")
	command_thread = threading.Thread( target=_mqtt_sub )
	command_thread.daemon = True
	command_thread.start()

	print("Starting display thread")
	display = Display( args )
	display.daemon = True
	display.start()
	display.on()

	# Loop forever (until ^C)
	while True:
	    # Check if a command is available in the queue
	    try:
		command = commands_q.get(False)
	    except Queue.Empty:
		continue

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
	get_commands.clear()
	# And wait for MQTT to disconnect from broker
	command_thread.join()

	sys.exit(0)

if __name__ == "__main__":
    main()
