Raspberry Pi Zero driving a 32x64 LED matrix (3mm pitch) using hzeller's excellent [rpi-rgb-led-matrix](https://github.com/hzeller/rpi-rgb-led-matrix/) and their [wiring guide for the RPi](https://github.com/hzeller/rpi-rgb-led-matrix/blob/master/wiring.md).

Make sure you follow the instructions to install the [Python 2 bindings](https://github.com/hzeller/rpi-rgb-led-matrix/tree/master/python).

I wrote an LED Matrix driver shim for this project, it's in **lib/matrixdriver/**. I also included a threaded MQTT and Queues implementation in **lib/libcmdqueue/**.

## Running

```
$ sudo ./run.py
```

```
usage: run.py [-h] [-R REFRESH] [-r ROWS] [-c CHAIN] [-P PARALLEL]
              [-p PWMBITS] [-l] [-b BRIGHTNESS] [-H HOST] [-C CLIENTID]
              [-T TOPIC] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -R REFRESH, --refresh REFRESH
                        Refresh interval for bus times in seconds. Default:
                        120
  -r ROWS, --rows ROWS  Display rows. 16 for 16x32, 32 for 32x32. Default: 32
  -c CHAIN, --chain CHAIN
                        Daisy-chained boards. Default: 2.
  -P PARALLEL, --parallel PARALLEL
                        For Plus-models or RPi2: parallel chains. 1..3.
                        Default: 1
  -p PWMBITS, --pwmbits PWMBITS
                        Bits used for PWM. Range 1..11. Default: 11
  -l, --luminance       Don't do luminance correction (CIE1931)
  -b BRIGHTNESS, --brightness BRIGHTNESS
                        Sets brightness level. Range: 1..100. Default: 30
  -H HOST, --host HOST  MQTT broker host. Default: 192.168.1.201
  -C CLIENTID, --clientid CLIENTID
                        MQTT broker client ID (name). Default: display
  -T TOPIC, --topic TOPIC
                        MQTT broker topic. Default: display-commands
  -v, --verbose         Enable debug output.
```


## TODO

* Add an independent config file.
  * For MQTT parameters
  * And NextBus parameters
  * And Display parameters
* MQTT should be optional.
* Add 433 MHz remote as additional on/off trigger.
