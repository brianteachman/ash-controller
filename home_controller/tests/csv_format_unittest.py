import unittest

def csv_format(device, system, state):
    ## Return csv formated string: "device,system,state"
    #  device: 0=Main, 1=Dining
    #  system: messaging=0, lighting=1, heating=2
    return str(device) + ',' + str(system) + ',' + str(state) # + '\n'

## -------------------------------------------------------------------------

class CanPassIntegersTest(unittest.TestCase):
    def test(self):
        pay_load = csv_format(1,0,1)
        self.assertEqual(pay_load, '1,0,1') # or '1,0,1\n'

class CanPassStringsTest(unittest.TestCase):
    def test(self):
        pay_load = csv_format('1','0','1')
        self.assertEqual(pay_load, '1,0,1')

# can (should) definitly be more extensive ...

## -------------------------------------------------------------------------

if __name__ == '__main__':
    ## 
    unittest.main()
