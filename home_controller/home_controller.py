"""
Alexa Controlled Raspberry Pi Home Controller
 
Author:  Brian Teachman
Date:    12/8/2016
"""

from __future__ import division # haha! This was a good one
from flask import Flask, render_template
from flask_ask import Ask, statement, question, convert_errors
import logging
import time, datetime
import serial
import csv

## ------------------------------------------------------------------------- ##

MAIN_ROOM = 0
DINING_ROOM = 1

room_list = {'main': MAIN_ROOM, 'dining': DINING_ROOM}

# system codes
SYS_MESSAGE = 0
SYS_LIGHT = 1
SYS_HEAT = 2

# message codes (system=0)
MC_GET_TEMP = 0             # case 0
MC_IS_HEAT_ON = 1           # case 1
MC_GET_TEMP_SETPOINT = 2    # case 2
MC_IS_LIGHT_ON = 3          # case 3
                            # default case error 400

# light codes
MC_TURN_OFF_LIGHT = -1

# heat codes (system=2)
MC_TURN_OFF_HEAT = 0

ON = 1
OFF = 0

## ------------------------------------------------------------------------- ##

app = Flask(__name__)
ask = Ask(app, '/')

# log to console
logging.getLogger("flask_ask").setLevel(logging.DEBUG)

# log to file
logger = logging.getLogger("B3HC")
logger.setLevel(logging.DEBUG)
today = str( datetime.date.today() )
fh = logging.FileHandler("data/"+today+"-debug.log")
fh.setLevel(logging.DEBUG)
fm = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(fm)
logger.addHandler(fh)

## ------------------------------------------------------------------------- ##

ser = serial.Serial(
    port='/dev/ttyS0',  # GPIO UART on Raspberry Pi 3
    baudrate=115200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
    )

## ------------------------------------------------------------------------- ##


@ask.launch
def welcome_message():
    logger.info('Home Controller initiated.')

    welcome_text = render_template('welcome')
    say_what = render_template('say_what')
    sample_ask = render_template('sample_ask')

    return question(welcome_text).reprompt(say_what) \
           .standard_card(title='Alexa Smart Home Controller', 
                          text=sample_ask,
                          large_image_url='https://d30y9cdsu7xlg0.cloudfront.net/png/132885-200.png')


@ask.intent('AMAZON.HelpIntent')
def help_message():
    help_message = render_template('help_message')

    logger.info("HelpIntent called.")
    return question(help_message).reprompt(help_message) \
           .simple_card(title='Home Controller Command List', content=sample_ask)


@ask.intent('AMAZON.CancelIntent')
@ask.intent('AMAZON.StopIntent')
def stop():
    quit = render_template('quit')
    return statement(quit)


@ask.intent('SwitchRoomLightIntent', mapping={'room': 'room', 'status': 'status'})
def switch_room_light(room, status):
    """ 
    Sample utterances:

    Turn the {room} room light {status}
    Turn {status} the {room} room light
    """
    if room in room_list:
        logger.info("SwitchRoomLightIntent called.")
    else:
        logger.debug('SwitchRoomLightIntent: Some room called %s was called.', room)
        return question( render_template('which_room') )

    if status in ['on', 'high']:    state = 255
    if status in ['off', 'low']:    state = 0

    # if room !== None:   tx(device, 1, state) # Light system = 1
    tx(device_id(room), SYS_LIGHT, state) # Light system = 1

    light_status = render_template('light_status_response', room=room, status=status)

    logger.debug('SwitchRoomLightIntent: %s. analogWrite(ledPin, %s)', light_status, state)

    title = room.capitalize() + " Room Lighting"
    return statement(light_status) \
           .simple_card(title=title, content=light_status)


@ask.intent('SetRoomLightPercentIntent', convert={'room': str, 'percent': int})
def set_room_light(room, percent):
    """ 
    Sample utterances:

    Set the {room} room light to {percent} percent
    Set the lights to {percent} percent in the {room} room
    """
    if room in room_list:
        logger.info("SetRoomLightPercentIntent called.")
    else:
        logger.debug('SetRoomLightPercentIntent: Some room called %s was called.', room)
        return question( render_template('which_room') )

    # scale percentage to room controller light level
    light_level = ( percent / 100 ) * 255

    # transmit packet to room controllers
    rx_response = fetch_response(device_id(room), SYS_LIGHT, light_level)

    voice_response = render_template('light_level_response', room=room, percent=percent)
    card_title = room.capitalize() + " Room Lighting"
    card_response = render_template('light_level_card_response', room=room, percent=percent)

    logger.debug('SetRoomLightPercentIntent: %s Or %s on a scale from 0-255.', card_response, light_level)

    return statement(voice_response) \
           .simple_card(title=card_title, content=card_response)


@ask.intent('IsLightInRoomOnIntent', mapping={'room': 'room'})
def room_light_status(room):
    """ 
    Sample utterances:

    Is the light in the dining room on
    Is the light in the dining room off
    Is the light on in the main room 
    """
    if room in room_list:
        logger.info("IsLightInRoomOnIntent called.")
    else:
        logger.debug('IsLightInRoomOnIntent: Some room called %s was called.', room)
        return question( render_template('which_room') )

    rx_response = fetch_response(device_id(room), SYS_MESSAGE, MC_IS_LIGHT_ON)  # fetch light state
    light_state = rx_response['state']
    if light_state == ON:
        return_statement = render_template('light_status_response', room=room, status='on')
    else:
        return_statement = render_template('light_status_response', room=room, status='off')

    logger.debug('IsLightInRoomOnIntent: %s  (%s)', return_statement, bool(light_state))

    return statement(return_statement) \
            .simple_card(title="Smart Home Lighting", content=return_statement)


@ask.intent('WhatIsTempSetpointIntent', mapping={'room': 'room'})
def get_room_setpoint(room):
    """ 
    Sample utterances:

    What is the temperature set to in the main room
    What is the dining room temperature set to
    What is the temperature set point for the main room
    """
    if room in room_list:
        logger.info("WhatIsTempSetpointIntent called.")
    else:
        logger.debug('WhatIsTempSetpointIntent: Some room called %s was called.', room)
        return question( render_template('which_room') )

    rx_response = fetch_response(device_id(room), SYS_MESSAGE, MC_GET_TEMP_SETPOINT)  # fetch temperature from room controller
    temp = rx_response['state']

    if temp and (temp != 400):
        return_statement = render_template('temp_setpoint_response', room=room, temp=temp)
        logger.debug('GetRoomTemperatureIntent: '+return_statement)
    elif temp == 0:
        return_statement = render_template('get_setpoint_error', room=room)
        logger.error('GetRoomTemperatureIntent: '+return_statement)
    else:
        return_statement = render_template('get_temp_error', room=room)
        logger.error('GetRoomTemperatureIntent: '+return_statement)

    card_title = room.capitalize() + " Room Heating"
    return statement(return_statement) \
            .simple_card(title=card_title, content=return_statement)


@ask.intent('GetRoomTemperatureIntent', mapping={'room': 'room'})
def get_room_temp(room):
    """ 
    Sample utterances:

    What is the temperature in the main room
    Tell me the temperature in the dining room
    """
    if room in room_list:
        logger.info("GetRoomTemperatureIntent called.")
    else:
        logger.debug('GetRoomTemperatureIntent: Some room called %s was called.', room)
        return question( render_template('which_room') )

    rx_response = fetch_response(device_id(room), SYS_MESSAGE, MC_GET_TEMP)  # fetch temperature from room controller
    temp = rx_response['state']

    if temp and ( temp not in [400, 500] ):
        return_statement = render_template('get_temp', room=room, temp=temp)
        logger.debug('GetRoomTemperatureIntent: '+return_statement)
    else:
        return_statement = render_template('get_temp_error', room=room)
        logger.error('GetRoomTemperatureIntent: '+return_statement)

    card_title = room.capitalize() + " Room Heating"
    return statement(return_statement) \
            .simple_card(title=card_title, content=return_statement)


@ask.intent('SetRoomTemperatureIntent', mapping={'room': 'room', 'temp': 'temp'})
def set_room_temp(room, temp):
    """ 
    Sample utterances:

    Set the temperature in the main to 75 degrees
    Set the temperature to 75 in the dining room
    Set the heat in the dining room to 68
    """
    if room in room_list:
        logger.info("SetRoomTemperatureIntent called.")
    else:
        logger.debug( render_template('room_not_found', intent='SetRoomTemperatureIntent', room=room) )
        return question( render_template('which_room') )

    rx_response = fetch_response(device_id(room), SYS_HEAT, temp)  # set temperature from room controller
    is_set = rx_response['state']

    if is_set and ( is_set not in [400, 500] ):
        return_statement = render_template('set_temp_response', room=room, temp=temp)
    else:
        return_statement = render_template('set_temp_error', room=room)
    
    logger.error('SetRoomTemperatureIntent: '+return_statement)

    card_title = room.capitalize() + " Room Heating"
    return statement(return_statement) \
            .simple_card(title=card_title, content=return_statement)


@ask.intent('TurnOffAllHeatersIntent')
def turn_off_heaters():
    """ 
    Sample utterances:

    Turn the {room} room light {status}
    Turn {status} the {room} room light
    """
    logger.info("TurnOffAllHeatersIntent called.")

    tx(MAIN_ROOM, SYS_HEAT, MC_TURN_OFF_HEAT)
    tx(DINING_ROOM, SYS_HEAT, MC_TURN_OFF_HEAT)

    logger.debug('TurnOffAllHeatersIntent: All heaters off')

    card_title = "Smart Home Heating"
    heaters_off = render_template('heat_off_response')
    return statement(heaters_off) \
           .simple_card(title=card_title, content=heaters_off)


@ask.intent('IsHeatOnInRoomIntent', mapping={'room': 'room'})
def room_heat_status(room):
    """ 
    Sample utterances:

    Is the heater in the dining room running
    Is the heater in the dining room on
    Is the heater running in the main room 
    """
    if room in room_list:
        logger.info("IsHeatOnInRoomIntent called.")
    else:
        logger.debug('IsHeatOnInRoomIntent: Some room called %s was called.', room)
        return question( render_template('which_room') )

    rx_response = fetch_response(device_id(room), SYS_MESSAGE, MC_IS_HEAT_ON)  # fetch heater state
    heater_state = rx_response['state']

    if heater_state == ON:
        return_statement = render_template('heat_status', room=room, status='on')
    else:
        return_statement = render_template('heat_status', room=room, status='off')

    logger.debug('IsHeatOnInRoomIntent: %s  (%s)', return_statement, bool(heater_state))

    card_title = "Smart Home Heating"
    return statement(return_statement) \
            .simple_card(title=card_title, content=return_statement)


@ask.intent('AreAnyHeatersOnIntent')  
def any_heat_status():
    """ 
    Sample utterances:

    Tell me if any heaters are running
    Are any heaters running
    Are there any heaters running
    Are there heaters running in any rooms
    Are there heaters running in any of the rooms
    """
    logger.info("AreAnyHeatersOnIntent called.")

    main_room = fetch_response(MAIN_ROOM, SYS_MESSAGE, MC_IS_HEAT_ON)  # fetch heater state
    time.sleep(0.1) # give some time for propagation
    dining_room = fetch_response(DINING_ROOM, SYS_MESSAGE, MC_IS_HEAT_ON)  # fetch heater state

    logger.debug('AreAnyHeatersOnIntent: Main room: %s', main_room)
    logger.debug('AreAnyHeatersOnIntent: Dining room: %s', dining_room)

    if ( main_room['state'] == ON ) and ( dining_room['state'] == ON ):
        return_statement = 'The heater is currently running in both rooms'

    elif main_room['state'] == ON:
        return_statement = 'The heater in the main room is on'

    elif dining_room['state'] == ON:
        return_statement = 'The heater in the dining room is on'

    elif ( main_room['state'] == 500 ) or ( dining_room['state'] == 500 ):
        return_statement = 'There was a problem reading a temperature sensor'

    else:
        return_statement = 'There are currently no heaters running'

    return statement(return_statement) \
            .simple_card(title='Smart Home Heater Status', content=return_statement)


## ------------------------------------------------------------------------- ##

def device_id(room):
    """ Set device id, either 0 or 1 (1 of 2 devices) """
    return MAIN_ROOM if room == 'main' else DINING_ROOM

def csv_format(device, system, state):
    """ Return csv formated string: "device,system,state"
    device: 0=Main, 1=Dining
    system: 0=Messaging, 1=Lighting, 2=Heating
    """
    return str(device) + ',' + str(system) + ',' + str(state)

def csv_parse(serial_string):
    csv_strings = csv.reader([serial_string])
    return list( map( int, list(csv_strings)[0]))

def tx(device, system, state):
    """ Send message to Room Controller over serial port """
    payload = csv_format(device, system, state)

    ser.flushInput()
    ser.flushOutput()

    ser.write( payload )
    logger.debug('Tx: Sending message: %s', payload)

rx_retry = 0 # Rx retry counter

def rx():
    """ Recieve and parse message from Room Controller, via serial """
    csv_packet = ser.readline().rstrip()   # fetch serial and strip "\r\n"
    return csv_parse(csv_packet)       # parse csv


def fetch_response(device, system, state):
    """ Transmit and recieve serial message """
    global rx_retry # use global counter

    tx(device, system, state)  # send request payload

    time.sleep(.3)             # give the serial port time to receive the data

    rx_failed = True
    while rx_failed:
        csv_list = rx()        # return response payload from serial buffer

        if (len(csv_list) == 3):
            rx_failed = False

        # if there aren't three elements in the response, and we haven't already tried three times
        if (len(csv_list) < 3) and (rx_retry < 3):
            logger.debug('Rx: Retry=%s - Failed fetch: %s', rx_retry, csv_list)
            rx_retry += 1
            time.sleep(.5)

        if (len(csv_list) < 3) and rx_retry == 3: # reset counter and return error status
            rx_retry = 0
            logger.error('Rx: TIMED OUT - %s', csv_list)
            return {'device': 1, 'system': 0, 'state': 400}

    rx_retry = 0

    logger.debug('Rx: Incoming message: %s', csv_list)

    return {'device': csv_list[0], 'system': csv_list[1], 'state': csv_list[2]}


## ------------------------------------------------------------------------- ##

if __name__ == '__main__':
    port = 5000 # set same as tunnel
    app.run(host='0.0.0.0', port=port)
