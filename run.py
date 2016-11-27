#!/usr/bin/env python
import argparse, time, sys, os, threading
import paho.mqtt.client as mqtt
sys.path.append('./lib')
from matrixdriver import Display
from libnextbus import Nextbus

get_commands = threading.Event()
get_busses = threading.Event()
display_on = threading.Event()

# Command thread, loops listening to the MQTT topic it's subscribed to
def _mqtt_sub():
    BROKER = "192.168.1.201"
    CLIENT_ID = "dobby-slave"
    TOPIC = "nextbus-on"

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(client, userdata, flags, rc):
	print("Connected with result code "+str(rc))

	# Subscribing in on_connect() means that if we lose the connection and
	# reconnect then subscriptions will be renewed.
	client.subscribe(TOPIC)

    # The callback for when a PUBLISH message is received from the server.
    def on_message(client, userdata, msg):
	print("MQTT rx: "+msg.topic+" ( "+str(msg.payload)+" )")

	if msg.payload == "TRUE":
	    display_on.set()

    client = mqtt.Client(client_id=CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER, 1883, 60)

    while get_commands.isSet():
      # Blocking call that processes network traffic, dispatches callbacks and
      # handles reconnecting.
      client.loop()

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
		if not get_busses.isSet():
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

	print("Starting MQTT thread, listening for commands")
	command_thread = threading.Thread( target=_mqtt_sub )
	command_thread.daemon = True
	display_on.set()
	get_commands.set()
	command_thread.start()

	# Loop forever (until ^C)
	while True:
	    if display_on.isSet():
		# TODO move the display thread out of while True.
		# display stuff should be setup with command thread.
		# TODO rearchitect Display() to have on() and off() funcs
		# call those here instead of spawning/killing threads
		print("Starting display thread")
		display = Display( args )
		display_thread = threading.Thread( target=display.start )
		display_thread.daemon = True
		display_thread.start()

		print("Starting NextBus API thread")
		bus_thread = threading.Thread( target=_busses, args=(display, args['refresh']) )
		bus_thread.daemon = True
		get_busses.set()
		bus_thread.start()

		# Keep the display on for a few seconds then turn off
		time.sleep(5)
		display_on.clear()
	    if not display_on.isSet():
		display.stop()
		display_thread.join()

		get_busses.clear()
		bus_thread.join()
    except KeyboardInterrupt:
	print "\nExiting\n"
	display.stop()
	#display_thread.join()

	#get_busses.clear()
	#bus_thread.join()

	#get_commands.clear()
	#command_thread.join()

	sys.exit(0)

if __name__ == "__main__":
    main()
