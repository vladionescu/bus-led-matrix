#!/usr/bin/env python
# Display a runtext with double-buffering.
from samplebase import SampleBase
from rgbmatrix import graphics
import time

class RunText(SampleBase):
    def __init__(self, text, *args, **kwargs):
        super(RunText, self).__init__(*args, **kwargs)

	self.TOP_ROW	= 10
	self.MIDDLE_ROW = 20
	self.BOTTOM_ROW = 30

        self.BOLD = graphics.Font()
        self.BOLD.LoadFont("./fonts/7x13B.bdf")
	
        self.REGULAR = graphics.Font()
        self.REGULAR.LoadFont("./fonts/7x13.bdf")

        self.color = graphics.Color(255, 0, 0)

	self.text = text

    def Run(self):
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

            #time.sleep(0.05)
            time.sleep(0.1)
            offscreenCanvas = self.matrix.SwapOnVSync(offscreenCanvas)


# Main function
if __name__ == "__main__":
    parser = RunText("Hello World!!")
    if (not parser.process()):
        parser.print_help()
