#!/usr/bin/env python
import argparse, time, sys, os
sys.path.append('./lib')
from rgbmatrix import RGBMatrix, graphics

def usleep(value):
    time.sleep(value / 1000000.0)

class Display():
    DONE_ROW = 'Done scrolling row'

    def __init__(self, parsed_args, *args, **kwargs):
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

    def start(self):
        try:
            # Start loop
            print("Press CTRL-C to stop sample")
            current = 0 
            for msg, code in self.draw_screen():
                current += 1
                print msg
                print code
                print current
        except KeyboardInterrupt:
            print("Exiting\n")
            sys.exit(0)

        return True

    def draw_screen(self):
        print("Running")

	# Dummy dict of rows and their display parameters
        on_screen = { self.TOP_ROW : {'font': self.REGULAR, 'scroll': False, 'text': '17:25 PM'},
		      self.MIDDLE_ROW : {'font': self.REGULAR, 'scroll': False, 'text':''},
		      self.BOTTOM_ROW : {'font': self.BOLD, 'scroll': True, 'text': '38R in 1 min'} }

        canvas = self.matrix.CreateFrameCanvas()
	
	# The position of the message on each row, used when message is scrolling
        pos = { self.TOP_ROW : canvas.width,
		self.MIDDLE_ROW : canvas.width,
		self.BOTTOM_ROW : canvas.width }

	line_len = { self.TOP_ROW: None, self.MIDDLE_ROW: None, self.BOTTOM_ROW: None }

	# Display the on_screen dict of rows continuously
        while True:
	    # Turn off all the pixels before lighting up new ones
	    # Or else all will be on after a while
            canvas.Clear()

	    # Render each row in turn
            for row in on_screen:
		# If this row is meant to scroll, make it scroll right to left
		if on_screen[row]['scroll']:
		    line_len[row] = graphics.DrawText(canvas, on_screen[row]['font'], pos[row], row, self.color, on_screen[row]['text'])

		    pos[row] -= 1
		    if (pos[row] + line_len[row] < 0):
			# If the row has scrolled all the way, reset it
			pos[row] = canvas.width
			# Emit a "row done scrolling" message with corresponding row value
			yield Display.DONE_ROW, row
	      else:
		  # Otherwise display it statically adjusted left
		  graphics.DrawText(canvas, on_screen[row]['font'], 0, row, self.color, on_screen[row]['text'])

	    # Wait a brief period before drawing the next screenful of rows
            time.sleep(0.1)
	    # Draw the canvas we just made
            canvas = self.matrix.SwapOnVSync(canvas) 

# Main function
if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-r", "--rows", action="store", help="Display rows. 16 for 16x32, 32 for 32x32. Default: 32", default=32, type=int)
    parser.add_argument("-c", "--chain", action="store", help="Daisy-chained boards. Default: 2.", default=2, type=int)
    parser.add_argument("-P", "--parallel", action="store", help="For Plus-models or RPi2: parallel chains. 1..3. Default: 1", default=1, type = int)
    parser.add_argument("-p", "--pwmbits", action="store", help="Bits used for PWM. Something between 1..11. Default: 11", default=11, type=int)
    parser.add_argument("-l", "--luminance", action="store_true", help="Don't do luminance correction (CIE1931)")
    parser.add_argument("-b", "--brightness", action="store", help="Sets brightness level. Default: 30. Range: 1..100", default=30, type=int)

    display = Display( vars(parser.parse_args()) )
    display.start()
