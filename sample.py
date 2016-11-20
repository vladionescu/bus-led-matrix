#!/usr/bin/env python
import argparse, time, sys, os
sys.path.append('./lib')
from matrixdriver import Display

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
