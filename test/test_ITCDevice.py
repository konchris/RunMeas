import os
import unittest
import visa
import pyvisa
import time
from queue import Queue
from datetime import datetime

from RunMeas.ITCDevice import ITCDevice, ITCMeasurementThread

DEVPATH = os.path.join(os.getcwd(), 'test', 'devices.yaml')
# DEVPATH = '/home/chris/Programming/github/RunMeas/test/devices.yaml'


class DeviceTestCase(unittest.TestCase):
    """Test the device class."""

    def setUp(self):
        rm = visa.ResourceManager('{}@sim'.format(DEVPATH))
        for resource_address in rm.list_resources():
            if 'GPIB' in resource_address and '24' in resource_address:
                self.itc01 = ITCDevice(resource_address)
                self.itc01.set_resource(rm.open_resource)

    def test_create_itc_device(self):
        rm = visa.ResourceManager('{}@sim'.format(DEVPATH))
        for resource_address in rm.list_resources():
            print(resource_address)
            if 'GPIB' in resource_address and '24' in resource_address:
                itc01 = ITCDevice(resource_address)
                itc01.set_resource(rm.open_resource)
        self.assertIsInstance(itc01.resource,
                              pyvisa.resources.gpib.GPIBInstrument)

    def test_device_has_gpib_resource(self):
        """Make sure the devices resource is a gpib resource."""
        self.assertIsInstance(self.itc01.resource,
                              pyvisa.resources.gpib.GPIBInstrument)

    def test_device_read_termination_character(self):
        "Make sure that the read termination character is a carriage return."
        self.assertEqual(self.itc01.resource.read_termination, '\r')

    def test_device_write_termination_character(self):
        "Make sure that the write termination character is a carriage return."
        self.assertEqual(self.itc01.resource.write_termination, '\r')

    def test_itc_identity(self):
        "Confirm the identity of the device"
        self.assertEqual(self.itc01.resource.query('V'), "ITC503")

    def test_read_tsorp(self):
        "Test reading from sorption pump sensor"
        self.assertEqual(self.itc01.get_tsorp(), ('TSorp', 249.2))

    def test_read_t1k(self):
        "Test reading from sorption pump sensor"
        self.assertEqual(self.itc01.get_t1k(), ('T1K', 7.0))

    def test_read_the3(self):
        "Test reading from sorption pump sensor"
        self.assertEqual(self.itc01.get_the3(), ('THe3', 7.0))

    def test_set_heater_sensor(self):
        "Test if setting the heater sensor to the sorption pump sensor worked"
        self.itc01._set_heater_to_tsrop()
        self.assertTrue(self.itc01.heater_set)
        self.assertEqual(self.itc01.get_heater_sensor(), "TSorp")

    def test_set_tsorp_setpoint(self):
        "Set the temperature the sorption pump should go to."
        self.itc01.set_setpoint(30)
        self.assertEqual(self.itc01.get_setpoint(), ('Setpoint', 30.0))

    def test_turn_on_auto_heat(self):
        "Turn the auto heat control on."
        self.itc01.auto_heat_on()
        self.assertTrue(self.itc01.auto_heat)
        self.assertEqual(self.itc01.get_auto_heat_status(), ('AutoHeat', "On"))

    def test_turn_off_auto_heat(self):
        "Turn the auto heat control off."
        self.itc01.auto_heat_off()
        self.assertFalse(self.itc01.auto_heat)
        self.assertEqual(self.itc01.get_auto_heat_status(),
                         ('AutoHeat', "Off"))

    def test_turn_auto_pid_on(self):
        "Turn on auto pid"
        self.itc01.auto_pid_on()
        self.assertEqual(self.itc01.get_auto_pid_status(), ('AutoPID', "On"))

    def test_turn_auto_pid_off(self):
        "Turn of auto pid"
        self.itc01.auto_pid_off()
        self.assertEqual(self.itc01.get_auto_pid_status(), ('AutoPID', "Off"))

    def test_set_heater_output(self):
        "Test setting heater output manually"
        self.itc01.set_heater_output(20)
        self.assertEqual(self.itc01.get_heater_output(),
                         ('HeaterOutput', 20.0))

    def test_get_all_temperatures(self):
        "Test getting all temperatures from all three sensors"
        (datetimestamp, TSorp, THe3, T1K) = self.itc01.get_all_temperatures()
        self.assertIsInstance(datetimestamp, datetime)
        self.assertEqual(TSorp, ('TSorp', 249.2))
        self.assertEqual(THe3, ('THe3', 7.000))
        self.assertEqual(T1K, ('T1K', 7.000))


class ThreadTestCase(unittest.TestCase):
    """Test the thread class."""

    def setUp(self):
        self.rm = visa.ResourceManager('{}@sim'.format(DEVPATH))
        for resource_address in self.rm.list_resources():
            if 'GPIB' in resource_address:
                self.itc01 = ITCDevice(resource_address)
                self.itc01.set_resource(self.rm.open_resource)

        self.delay = 0.4

        self.itc_thread = ITCMeasurementThread(self.itc01,
                                               ['TSorp', 'THe3', 'T1K'],
                                               delay=self.delay)

    def test_thread_has_queue(self):
        self.assertIsInstance(self.itc_thread.q, Queue)

    def test_thread_has_chan_list(self):
        self.assertIsInstance(self.itc_thread.chan_list, list)
        self.assertTrue(self.itc_thread.chan_list)

    def test_thread_start_stop(self):
        self.assertFalse(self.itc_thread.is_alive())
        self.itc_thread.start()
        self.assertTrue(self.itc_thread.is_alive())
        self.itc_thread.stop_thread()
        self.itc_thread.join()
        self.assertFalse(self.itc_thread.is_alive())

    def test_number_elements_in_queue(self):
        wait = 5
        self.assertTrue(self.itc_thread.q.empty())
        self.itc_thread.start()
        self.assertTrue(self.itc_thread.is_alive())
        time.sleep(wait*self.delay)
        self.assertFalse(self.itc_thread.q.empty())
        self.itc_thread.stop_thread()
        self.itc_thread.join()
        self.assertFalse(self.itc_thread.is_alive())
        self.assertFalse(self.itc_thread.q.empty())
        i = 0
        print(self.itc_thread.q.empty(), self.delay)
        while not self.itc_thread.q.empty() and i < 5:
            self.itc_thread.q.get()
            i += 1
        self.assertEqual(i, wait, 'Expected {w} and got only {eye}'.format(w=wait, eye=i))


if __name__ == "__main__":
    unittest.main()
