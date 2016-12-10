Raspberry Pi Zero driving a 32x64 LED matrix (3mm pitch) using hzeller's excellent [rpi-rgb-led-matrix](https://github.com/hzeller/rpi-rgb-led-matrix/) and their [wiring guide for the RPi](https://github.com/hzeller/rpi-rgb-led-matrix/blob/master/wiring.md).

Make sure you follow the instructions to install the [Python 2 bindings](https://github.com/hzeller/rpi-rgb-led-matrix/tree/master/python).

I wrote an LED Matrix driver shim for this project, it's in **lib/matrixdriver/**.

## Running

```
$ sudo ./run.py
```

Script currently expects a hard coded MQTT broker and the #commands topic.

## TODO

* Add an independent config file.
  * For MQTT parameters
  * And NextBus parameters
* Implement proper logging.
* Display should turn off after 60 seconds of on time.
* Multiple 'display on' commands should extend the display on time by 60 seconds.
* MQTT should be optional.
* Add 433 MHz remote as additional on/off trigger.
