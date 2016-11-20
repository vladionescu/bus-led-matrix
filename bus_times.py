#!/usr/bin/env python
import argparse, time, sys, os
sys.path.append('./lib')
from rgbmatrix import RGBMatrix, graphics

def usleep(value):
    time.sleep(value / 1000000.0)

class Display():
    def __init__(self, text, parsed_args, *args, **kwargs):
	# Setup screen's variables
	self.TOP_ROW	= 10
	self.MIDDLE_ROW = 20
	self.BOTTOM_ROW = 30

        self.BOLD = graphics.Font()
        self.BOLD.LoadFont("./fonts/7x13B.bdf")
	
        self.REGULAR = graphics.Font()
        self.REGULAR.LoadFont("./fonts/7x13.bdf")

        self.color = graphics.Color(255, 0, 0)

	# Load the args
	self.text = text

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
            for msg, code in self.Run():
	      current += 1
	      print msg
	      print code
	      print current
        except KeyboardInterrupt:
            print("Exiting\n")
            sys.exit(0)

        return True

    def Run(self):
        print("Running")
        offscreenCanvas = self.matrix.CreateFrameCanvas()
        pos = offscreenCanvas.width

        while True:
	    offscreenCanvas.Clear()
	    graphics.DrawText(offscreenCanvas, self.BOLD, 0, self.TOP_ROW, self.color, "15:35 PM")
	    len = graphics.DrawText(offscreenCanvas, self.REGULAR, pos, self.BOTTOM_ROW, self.color, "2")

            pos -= 1
            if (pos + len < 0):
                pos = offscreenCanvas.width
		yield "done", 3

            time.sleep(0.1)
            offscreenCanvas = self.matrix.SwapOnVSync(offscreenCanvas)


# Main function
if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-r", "--rows", action="store", help="Display rows. 16 for 16x32, 32 for 32x32. Default: 32", default=32, type=int)
    parser.add_argument("-c", "--chain", action="store", help="Daisy-chained boards. Default: 2.", default=2, type=int)
    parser.add_argument("-P", "--parallel", action="store", help="For Plus-models or RPi2: parallel chains. 1..3. Default: 1", default=1, type = int)
    parser.add_argument("-p", "--pwmbits", action="store", help="Bits used for PWM. Something between 1..11. Default: 11", default=11, type=int)
    parser.add_argument("-l", "--luminance", action="store_true", help="Don't do luminance correction (CIE1931)")
    parser.add_argument("-b", "--brightness", action="store", help="Sets brightness level. Default: 30. Range: 1..100", default=30, type=int)

    display = Display("Hello World!!", vars(parser.parse_args())

    display.start()
