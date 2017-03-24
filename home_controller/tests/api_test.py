#!/usr/bin/env python

import serial, time, logging, csv

SERIAL_PORT = '/dev/ttyS0' # http://raspberrypi.stackexchange.com/a/47383
BAUD_RATE = 115200

ser = serial.Serial(
    port=SERIAL_PORT,  
    baudrate=BAUD_RATE,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
    )

## ------------------------------------------------------------------------- ##

logger = logging.getLogger("API TEST")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('/home/pi/hc/data/api_test.log')
fh.setLevel(logging.DEBUG)
fm = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(fm)
logger.addHandler(fh)

## ------------------------------------------------------------------------- ##

def csv_format(device, system, state):
    ## Return csv formated string: "device,system,state"
    #  device: 0=Main, 1=Dining
    #  system: messaging=0, lighting=1, heating=2
    return str(device) + ',' + str(system) + ',' + str(state) # + '\n'

def csv_parse(serial_string):
    csv_strings = csv.reader([serial_string])
    return list( map( int, list(csv_strings)[0]))

def tx(device, system, state):
    ## Send message to Room Controller over serial port
    ser.write( csv_format(device, system, state) )

rx_retry = 0 # Rx retry counter

def rx():
    ## Recieve and parse message from Room Controller, via serial
    csv_packet = ser.readline().rstrip()   # fetch serial and strip "\r\n"
    csv = csv_packet.split(',')            # parse csv

    global rx_retry # use global counter

    # if there aren't three elements in the response,
    # and we haven't already tried three times
    if (len(csv) < 3) and (rx_retry < 3):
        rx_retry += 1
        rx()

    if (len(csv) < 3) and rx_retry == 3: # reset counter and return error status
        rx_retry = 0
        return {'device': int( csv[0] ), 'system': 0, 'state': 400}

    rx_retry = 0

    return {'device': int( csv[0] ), 'system': int( csv[1] ), 'state': int( csv[2] )}

def fetch_response(device, system, state):
    ## Transmit and recieve serial message
    tx(device, system, state)  # send request payload
    time.sleep(1)            # give the serial port time to receive the data
    return rx()                # return response payload from serial buffer

## ------------------------------------------------------------------------- ##

device = 0
# device = 1

if __name__ == '__main__':

    # SwitchRoomLightIntent test
    tx(device, 1, 0)
    time.sleep(1)
    tx(device, 1, 255)

    # SetRoomLightPercentIntent test
    percent = '50'
    light_level = (int( percent )/100)*255
    tx(device, 1, light_level) # Light system = 1
    logger.debug('SetRoomLightPercent: %s percent -> %s', percent, light_level)

    # WhatsTheTempIntent test
    response = fetch_response(device, 0, 0)  # fetch temperature from room controller
    logger.debug('WhatsTheTemp Response: %s', response)

    # IsHeatOnInRoomIntent test
    response = fetch_response(device, 0, 1)  # fetch heater state
    logger.debug('IsHeatOnInRoom Response: %s', response)

    # AreAnyHeatersOnIntent test
    main_room = fetch_response(0, 0, 1)  # fetch heater state
    dining_room = fetch_response(1, 0, 1)  # fetch heater state
    logger.info('AreAnyHeatersOn Main Room Response: %s', main_room)
    logger.info('AreAnyHeatersOn Dining Room Response: %s', dining_room)


