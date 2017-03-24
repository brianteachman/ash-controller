import unittest
import math
import csv
import time, datetime

def csv_format(device, system, state):
    ## Return csv formated string: "device,system,state"
    #  device: 0=Main, 1=Dining
    #  system: messaging=0, lighting=1, heating=2
    return str(device) + ',' + str(system) + ',' + str(state) # + '\n'

def csv_parse(serial_string):
    csv_strings = csv.reader([serial_string])
    return list( map( int, list(csv_strings)[0]))

## -------------------------------------------------------------------------

rx_retry = 0


def rx( csv_payload, return_str=False ):
    global rx_retry # use global counter
    # print( rx_retry )

    csv = csv_payload.split(',') # parse csv
    csv_length = len( csv )

    if ( csv_length < 3 ) and ( rx_retry < 3 ):
        rx_retry += 1
        # csv_payload += ',0'
        rx( csv_payload+',0' )
     
    # if rx_retry == 3: # reset counter and return error status
    #     device = csv[0] if return_str else int( csv[0] )
    #     system = '0' if return_str else 0    # messaging system
    #     state = '400' if return_str else 400 # request error code

    if csv_length == 3:
        device = csv[0] if return_str else int( csv[0] )
        system = csv[1] if return_str else int( csv[1] )
        state = csv[2] if return_str else int( csv[2] ) 

    rx_retry = 0
    return {'device': device, 'system': system, 'state': state}

## -------------------------------------------------------------------------

class CastIntToBoolIsFalseTest(unittest.TestCase):
    def test(self):
        """
        bool(isOn) == False
        """
        isOn = 0
        self.assertEqual(bool(isOn), False)

class CastIntToBoolIsTrueTest(unittest.TestCase):
    """
    bool(isOn) == True
    """
    def test(self):
        isOn = 1
        self.assertEqual(bool(isOn), True)

class CSVSplitElementIsStringTest(unittest.TestCase):
    """
    """
    def test(self):
        csv = '0,0,1'
        arr = csv.split(',')      # parse csv
        self.assertEqual(arr[2], '1')

class CSVSplitElementIsIntTest(unittest.TestCase):
    """
    """
    def test(self):
        csv = '0,0,1'
        arr = csv.split(',')      # parse csv
        self.assertEqual(int(arr[2]), 1)

class LightLevelMappingTest(unittest.TestCase):
    """
    """
    def test(self):
        percent = 50
        light_level = math.ceil( (int(percent)/100)*255 )

        self.assertEqual(light_level, 128)


## - rx() Tests ------------------------------------------------------------

class rxReturnsIntDictByDefaultTest(unittest.TestCase):
    """
    """
    def test(self):
        csv = csv_format(0,0,1)
        arr = rx(csv)      # parse csv
        self.assertEqual(arr, {'system': 0, 'device': 0, 'state': 1})

class rxReturnsStringDictTest(unittest.TestCase):
    """
    """
    def test(self):
        csv = csv_format(0,0,1)
        arr = rx(csv, True)
        self.assertEqual(arr, {'system': '0', 'device': '0', 'state': '1'})

# class rxAppendsZeroToDictTest(unittest.TestCase):
#     """
#     """
#     def test(self):
#         arr = rx('1,0')
#         self.assertEqual(arr, {'system': 1, 'device': 0, 'state': 0})

## -------------------------------------------------------------------------

class CSVParseTest(unittest.TestCase):
    """
    """
    def test(self):
        csv_list = csv_parse("0,0,1")
        self.assertEqual(csv_list, [0,0,1])

class datetimeTest(unittest.TestCase):
    def test(self):
        today = str( datetime.date.today() )
        # update the date string below to pass test
        self.assertEqual("data/"+today+"-debug.log", "data/2017-03-08-debug.log")

## -------------------------------------------------------------------------

if __name__ == '__main__':
    ## 
    unittest.main()

    # print( rx(csv_format(0,0,1)) )
    # print( rx(csv_format(0,0,1), True) )
    # print( rx('1,0') )
    # print( rx('1,0', True) )
    # print( rx('1') )
