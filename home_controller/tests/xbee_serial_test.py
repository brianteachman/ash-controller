#!/usr/bin/env python

import serial, time, datetime, sys
from xbee import XBee

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

# Send message to Room Controller over serial port
def tx(device, system, state):
    # sends csv formated string: "system,state"
    # system (lighting=1, heating=2)
    message.join(device, ',', system, ',', state)
    ser.write(message) # ser.write('Tx message: %s \n'%(message))


# Recieve and parse message from Room Controller, via serial
def rx():
    raw_message = ser.readline()

    # parse csv
    mess_arry = raw_message.split(',')

    return {'device': mess_arry[0], 'system': mess_arry[1], 'state': mess_arry[2]}

## ------------------------------------------------------------------------- ##

if __name__ == '__main__':
    
    # test serial here
    print ("Ahoy!")

    xbee = XBee(ser)

    print ('Prepare for battle!')
    # Continuously read and print packets
    while True:
        try:
            response = xbee.wait_read_frame()
            print response
        except KeyboardInterrupt:
            break

    ser.close()
