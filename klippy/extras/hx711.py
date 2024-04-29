import logging
from . import bus
import struct

HX711_CHIP_ADDR = 0x48
HX711_I2C_SPEED = 100000
HX711_REG_ADDR = 0x00
HX711_REG_LEN = 4

HX711_MIN_REPORT_TIME = .5
HX711_REPORT_TIME = .8

class HX711:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.name = config.get_name().split()[-1]
        self.reactor = self.printer.get_reactor()
        self.i2c = bus.MCU_I2C_from_config(config, HX711_CHIP_ADDR, HX711_I2C_SPEED)
        self.mcu = self.i2c.get_mcu()
        self.report_time = config.getfloat('hx711_report_time', HX711_REPORT_TIME, minval=HX711_MIN_REPORT_TIME)
        self.pressure = 0.0
        self.sample_timer = self.reactor.register_timer(self._sample_hx711)
        self.printer.add_object("hx711 " + self.name, self)
        self.printer.register_event_handler("klippy:connect", self.handle_connect)

    def handle_connect(self):
        self._init_hx711()
        self.reactor.update_timer(self.sample_timer, self.reactor.NOW)

    def setup_callback(self, cb):
        self._callback = cb

    def get_report_time_delta(self):
        return self.report_time

    def _init_hx711(self):
        try:
            prodid = self.read_register('PRODID', 1)[0]
            logging.info("hx711: CHIP ID %#x" % prodid)
        except:
            pass

    def _sample_hx711(self, eventtime):
        try:
            sample = self.readValue()
            self.pressure = self.convertToFloat(sample)
        except Exception:
            logging.exception("hx711: Error reading value")
            self.pressure = 0.0
            return self.reactor.NOW
        
        measured_time = self.reactor.monotonic()
        self._callback(self.msu.estimated_print_time(measured_time), self.pressure)
        return measured_time + self.report_time

    def readValue(self):
        params = self.i2c.i2c_read(HX711_REG_ADDR, HX711_REG_LEN)
        return bytearray(params['response'])

    def convertToFloat(self, sample):
        return struct.unpack('f', sample)[0]


def load_config(config):
    pheaters = config.get_printer().load_object(config, "heaters")
    pheater.add_sensor_factory("HX711", HX711)
