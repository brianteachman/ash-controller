# Raspberry Pi and Alexa Smart Home Controller #

### What is this repository for? ###

* Smart Home Capstone Project
* Version 0.1
* Built on [Alexa Skills Kit](https://developer.amazon.com/alexa-skills-kit), [Python](https://www.python.org/), [Flask](http://flask.readthedocs.io/en/latest/), [Flask-Ask](https://flask-ask.readthedocs.io/en/latest/index.html), [pagekite.py](https://pagekite.net/), [Raspberry Pi 3](https://www.raspberrypi.org/documentation/), [Amazon ECHO](https://www.amazon.com/All-New-Amazon-Echo-Dot-Add-Alexa-To-Any-Room) device.

### How do I get set up? ###


1. Load source code on device:
	
	`> git clone https://brianteachman@bitbucket.org/brianteachman/b3hc-home-controller.git hc`

2. Change into hc directory:

	`> cd hc`

3. Run these scripts: (each in their own terminal)

	`> python pagekite.py 5000 b3hc.pagekite.me`

	`> python home_controller.py`

	Pagekite and this script must be running at the same time!

### Current Utterances ###

Niave Smart Home API behaviour:

```
Turn the { room } room light { status }
Turn the { room } room lights { status }
Turn { status } the { room } room light
Turn { status } the { room } room lights

Set the { room } room light to { percent } percent
Set the lights to { percent } percent in the { room } room
Set the { room } room light to { percent } percent
Set the lights to { percent } percent in the { room } room

What's the temperature in the { room } room
What's the { room } room temperature
What is the temperature in the { room } room
What is the { room } room temperature
What temperature is it in the { room } room
Tell me the temperature in the { room } room
Tell me the { room } room temperature

Set the temperature in the { room } room to { temp }
Set the temperature in the { room } room to { temp } degrees
Set the temperature of the { room } room to { temp }
Set the temperature of the { room } room to { temp } degrees
Set the temperature to { temp } in the { room } room
Set the temperature to { temp } degrees in the { room } room
Set the { room } room temperature to { temp }
Set the { room } room temperature to { temp } degrees
Set the heat in the { room } room to { temp }
Set the heat in the { room } room to { temp }
Set the heater in the { room } room to { temp } degrees
Set the heater in the { room } room to { temp } degrees

Is the heater in the { room } room running
Is the heat in the { room } room running
Is the heat on in the { room } room
Is the heater running in the { room } room
Is the heat in the { room } room on
Is the { room } room  heater on

Tell me if any heaters are running
Are any heaters running
Are there any heaters running
Are there heaters running in any rooms
Are there heaters running in any of the rooms
```