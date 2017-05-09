#!/usr/bin/env python
import logging, threading, time, sys
from rgbmatrix import RGBMatrix, graphics

class Display(threading.Thread):
    DONE_ROW = 'Done scrolling row'

    # Expects parsed_args to contain:
    #	rows (int), chain (int), parallel (int), pwmbits (int), luminance (bool), brightness (int)
    def __init__(self, parsed_args, *args, **kwargs):
	super(Display, self).__init__()
	threading.currentThread().setName("Display")

	# Setup screen's variables
	self.TOP_ROW    = 10
	self.MIDDLE_ROW = 20
	self.BOTTOM_ROW = 30

	self.BOLD = graphics.Font()
	self.BOLD.LoadFont("./fonts/7x13B.bdf")

	self.REGULAR = graphics.Font()
	self.REGULAR.LoadFont("./fonts/7x13.bdf")

	self.color = graphics.Color(255, 0, 0)

	# Load the args
	self.matrix = RGBMatrix(parsed_args["rows"], parsed_args["chain"], parsed_args["parallel"])
	self.matrix.pwmBits = parsed_args["pwmbits"]
	self.matrix.brightness = parsed_args["brightness"]

	if parsed_args["luminance"]:
	    self.matrix.luminanceCorrect = False

	# Instance objects
        self.on_screen = { self.TOP_ROW : {}, self.MIDDLE_ROW : {}, self.BOTTOM_ROW : {} }
	self.to_be_displayed = {
	    self.TOP_ROW : [ 
		{'font': self.BOLD, 'scroll': False, 'text': time.strftime("%H:%M %p")}
	    ],
	    self.MIDDLE_ROW : [
		{'font': self.REGULAR, 'scroll': False, 'text': 'Bus Times'}
	    ],
	    self.BOTTOM_ROW : [
		{'font': self.REGULAR, 'scroll': True, 'text': 'Vlad Ionescu'},
		{'font': self.REGULAR, 'scroll': True, 'text': 'https://gitlab.com/vladionescu/bus-led-matrix'}
	    ]
	}
	self._stop = threading.Event()
	self._isOff = threading.Event()
	self._isClear = threading.Event()
	self._on = threading.Event()
	self._reset = threading.Event()

    # Ask the thread to die. Display._draw_screen() checks this every 0.1 seconds.
    def join(self, timeout=None):
	self._stop.set()
	super(Display, self).join(timeout)

    # Clear the display, turning it off
    def off(self):
	self._on.clear()
	self._isOff.set()

    # Set the _on flag, which will cause _draw_screen() to start drawing
    # If the display was previously off(), reset() text positioning
    def on(self):
	if self._isOff.isSet():
	    self._reset.set()

	self._on.set()
	self._isOff.clear()

    def run(self):
	threading.currentThread().setName("Display.Run")
	try:
	    # Initialize by starting the first message in each row
	    msg_index = { self.TOP_ROW: 0,
		self.MIDDLE_ROW: 0,
		self.BOTTOM_ROW: 0 }
	    
	    # Preseed the screen with the first messages
	    # So the first time the screen is drawn there is something there
	    for row, index in msg_index.iteritems():
		self._prepare_row(row, index)

	    # Update time every second
	    self._watch_the_time()

	    # Draw the screen and react to events it emits
	    # Because _draw_screen() is an infinite emitter, this should
	    #   never exit.
	    for event, code in self._draw_screen():
		# When a row is done scrolling (the message has gone off screen)
		# Display the next message for that row
		# This will show the same message again if there is only 1 message available
		if event == Display.DONE_ROW:
		    row = code

		    # Iterate through the list of messages available for this row
		    if msg_index[row] < len(self.to_be_displayed[row]) - 1:
			# If this is not the last message for this row, look to the next one
			msg_index[row] += 1
		    else:
			# If this is the last message for this row, loop to the beginning
			msg_index[row] = 0

		    # Set what the next rendering of the screen will show
		    self._prepare_row(row, msg_index[row])
	except KeyboardInterrupt:
	    return

    # Update on_screen for the specified row
    # Using the message from specified row & msg_index in to_be_displayed
    def _prepare_row(self, row, msg_index):
	if row not in [self.TOP_ROW, self.MIDDLE_ROW, self.BOTTOM_ROW]:
	    raise ValueError('Invalid row')
	    return False

	if msg_index >= len(self.to_be_displayed[row]):
	    raise ValueError('Message index does not exist in that row')
	    return False

	font = self.to_be_displayed[row][msg_index]['font']
	if font is None or font not in [self.REGULAR, self.BOLD]:
	    font = self.REGULAR

	scroll = self.to_be_displayed[row][msg_index]['scroll']
	if not isinstance(scroll, bool):
	    scroll = False

	self.on_screen[row]['font'] = font
	self.on_screen[row]['scroll'] = scroll
	self.on_screen[row]['text'] = self.to_be_displayed[row][msg_index]['text']
	self.on_screen[row]['current_index'] = msg_index

    def _draw_screen(self):
        logging.debug("Display thread is running")

        canvas = self.matrix.CreateFrameCanvas()
	
	# The position of the message on each row, used when message is scrolling
        pos = { self.TOP_ROW : canvas.width,
		self.MIDDLE_ROW : canvas.width,
		self.BOTTOM_ROW : canvas.width }

	line_len = { self.TOP_ROW: None, self.MIDDLE_ROW: None, self.BOTTOM_ROW: None }

	# Display the on_screen dict of rows continuously
        while True:
	    # Check if we need to exit
	    if self._stop.isSet():
		self.off()
		break
	    
	    # Check if the display is supposed to be off
	    # If so, clear it once then loop at a slower interval
	    if not self._on.isSet():
		if not self._isClear.isSet():
		    canvas.Clear()
		    canvas = self.matrix.SwapOnVSync(canvas) 
		    self._isClear.set()

		time.sleep(0.1)
		continue
	    
	    # Each time the display is turned on() after being off()
	    # Paint text at the edge of the display, not mid-scroll
	    if self._reset.isSet():
		pos = { self.TOP_ROW : canvas.width,
			self.MIDDLE_ROW : canvas.width,
			self.BOTTOM_ROW : canvas.width }
		line_len = { self.TOP_ROW: None, self.MIDDLE_ROW: None, self.BOTTOM_ROW: None }
		self._reset.clear()

	    # The display has text on it, not clear
	    self._isClear.clear()

	    # Turn off all the pixels before lighting up new ones
	    # Or else all will be on after a while
            canvas.Clear()

	    # Render each row in turn
            for row, message in self.on_screen.iteritems():
		# If this row is meant to scroll, make it scroll right to left
		if message['scroll']:
		    line_len[row] = graphics.DrawText(canvas, message['font'], pos[row], row, self.color, message['text'])

		    pos[row] -= 1
		    if (pos[row] + line_len[row] < 0):
			# If the row has scrolled all the way, reset it
			pos[row] = canvas.width

			# Emit a "row done scrolling" event
			yield Display.DONE_ROW, row
		else:
		    # Otherwise display it statically adjusted left
		    graphics.DrawText(canvas, message['font'], 0, row, self.color, message['text'])

	    # Wait a brief period before drawing the next screenful of rows
            time.sleep(0.1)
	    # Draw the canvas we just made
            canvas = self.matrix.SwapOnVSync(canvas) 

    # Update time every second
    def _watch_the_time(self):
	self.on_screen[self.TOP_ROW]['text'] = time.strftime("%H:%M %p")
	threading.Timer(1, self._watch_the_time).start()

    # Requires a row.
    # Given only a row it will blank that row, removing all messages for the row
    # By default the font is REGULAR and there is no scrolling
    # Note that giving a msg_index will only change that index and will not remove all messages for the row
    # To set the row to a single message, pass a row and text, and optionally font and scroll
    # To set the row to mutliple messages, pass the above and the msg_indexes you want to set, no index gaps!
    # Setting instant will cause the update to be immediate, ignoring scrolling text
    def set_row(self, row=None, text='', font=None, scroll=False, msg_index=None, instant=True):
	logging.debug("Setting row %s to: %s", row, text)

	if row is None:
	    raise ValueError('Need to know what row to set')
	    return False

	if row not in [self.TOP_ROW, self.MIDDLE_ROW, self.BOTTOM_ROW]:
	    raise ValueError('Invalid row')
	    return False

	if font is None or font not in [self.REGULAR, self.BOLD]:
	    font = self.REGULAR
	
	# If no msg_index was specified, clear the messages for this row then set the new one
	if msg_index is None:
	    index = 0
	    self.to_be_displayed[row] = []
	else:
	    index = msg_index

	message = {'font': font, 'scroll': scroll, 'text': text}

	# If the currently displayed message is being changed and it is static
	# We have to change it immediately because there will be no 'scroll finished' event to trigger an update
	if ( index == self.on_screen[row]['current_index'] and not self.on_screen[row]['scroll'] ) or instant:
	    self.on_screen[row] = message
	    self.on_screen[row]['current_index'] = index

	self.to_be_displayed[row].insert(index, message)

	return True

# Main function
if __name__ == "__main__":
    logging.error("Nothing to do. This is a module.")
    sys.exit(0)
