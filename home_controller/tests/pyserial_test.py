#!/usr/bin/env python

import serial, time

SERIAL_PORT = '/dev/ttyS0' # http://raspberrypi.stackexchange.com/a/47383
BAUD_RATE = 115200
# BAUD_RATE = 9600

ser = serial.Serial(
    port=SERIAL_PORT,  
    baudrate=BAUD_RATE,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
    )

## ------------------------------------------------------------------------- ##

def csv_format(device, system, state):
    ## Return csv formated string: "device,system,state"
    #  device: 0=Main, 1=Dining
    #  system: messaging=0, lighting=1, heating=2
    return str(device) + ',' + str(system) + ',' + str(state) # + '\n'

def tx(device, system, state):
    ## Send message to Room Controller over serial port
    ser.write( csv_format(device, system, state) )

rx_retry = 0 # Rx retry counter

def rx():
    ## Recieve and parse message from Room Controller, via serial
    raw_message = ser.readline().rstrip()   # fetch serial and strip "\r\n"
    mess_arry = raw_message.split(',')      # parse csv

    global rx_retry # use global counter
    # if there aren't three elements in the response,
    # and we haven't already tried three times
    if (len(mess_arry) < 3) and (rx_retry < 3):
        rx_retry += 1
        rx()

    if rx_retry == 3: # reset counter and return error status
        rx_retry = 0
        return {'device': '1', 'system': '0', 'state': '400'}

    return {'device': mess_arry[0], 'system': mess_arry[1], 'state': mess_arry[2]}

def fetch_response(device, system, state):
    ## 
    tx(device, system, state)  # send payload
    time.sleep(0.3)   # give the serial port time to receive the data
    return rx()       # return serial response from buffer

## ------------------------------------------------------------------------- ##

if __name__ == '__main__':

    i = 0
    
    # test serial here
    while True:

        # tx(1,0,0)
        # time.sleep(0.1)  # wait for response
        # response = rx()  # fetch serial response from buffer

        response = fetch_response(1, 0, i)

        if response['state'] != 400:
            # print( len(response) )
            print( str(response) )
        else:
            print( response['state'] )

        # check every second
        time.sleep(1)

        i += 1 # then increment
