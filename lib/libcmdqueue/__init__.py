#!/usr/bin/env python
import logging, Queue, sys, threading
import paho.mqtt.client as mqtt

class CmdQueue(threading.Thread):
    # Expects parsed_args to contain:
    #	host (string), clientid (string), topic (string)
    def __init__(self, parsed_args, *args, **kwargs):
	super(CmdQueue, self).__init__()
	threading.currentThread().setName("CmdQueue")

	# Load the args
	self.host = parsed_args["host"]
	self.clientid = parsed_args["clientid"]
	self.topic = parsed_args["topic"]

	self.valid_commands = []

	# Command slots, max 5 can be queued until the server refuses to queue more
	self.command_queue = Queue.Queue(5)

	# Connect to the MQTT broker
	self.client = mqtt.Client(client_id=self.clientid)
	self.client.on_connect = self._on_connect
	self.client.on_message = self._on_message

	logging.debug("Connecting to MQTT: %s #%s as %s", self.host, self.topic, self.clientid)
	self.client.connect(self.host, 1883, 60)

    # Cleanly disconnect from the broker
    def join(self, timeout=None):
	self.client.loop_stop()
	self.client.disconnect()
	super(CmdQueue, self).join(timeout)

    def run(self):
	try:
	    # Threaded call to processes network traffic.
	    # Dispatches callbacks and reconnects automatically.
	    self.client.loop_start()
	except KeyboardInterrupt:
	    return

    # A generator to return commands whenever they are available
    # Usage: "for cmd in CmdQueue.get_commands:"
    def get_commands(self):
	while True:
	    try:
		command = self.command_queue.get(False)
	    except Queue.Empty:
		continue

	    yield command

    # Set the array of acceptable commands
    def set_valid_commands(self, command_array):
	logging.debug("Valid commands: %s", str(command_array))
	self.valid_commands = command_array

    # The callback for when the client receives a CONNACK response from the server.
    def _on_connect(self, client, userdata, flags, rc):
	# This is invoked in its own thread, so the name must be set here too.
	threading.currentThread().setName("CmdQueue.OnConnect")

	logging.debug("MQTT result code %d: %s", rc, mqtt.connack_string(rc))

	# If the connection isn't successful.
	# Stop trying to connect and kill the thread.
	if rc != 0:
	    logging.debug("Stopping connection attempts to %s #%s as %s", self.host, self.topic, self.clientid)
	    client.disconnect()

	# Subscribing in _on_connect() means that if we lose the connection and
	# reconnect then subscriptions will be renewed.
	client.subscribe(self.topic)

    # The callback for when a PUBLISH message is received from the server.
    def _on_message(self, client, userdata, msg):
	logging.debug("MQTT rx (#%s): %s", msg.topic, msg.payload)

	message = msg.payload.lower()

	if message in self.valid_commands:
	    logging.debug("Command is valid. Queue push: %s", message)

	    # Queue the command, but only if there is a free command slot
	    # If the queue is full, drop the command
	    try:
		self.command_queue.put(message, False)
	    except Queue.Full:
		pass

# Main function
if __name__ == "__main__":
    logging.error("Nothing to do. This is a module.")
    sys.exit(0)
