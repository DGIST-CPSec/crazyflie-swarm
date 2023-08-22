# collect console printf strings from crazyflie.console

import time, datetime
from threading import Event
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.console import Console as cf_console
from cflib.utils import uri_helper
from cflib.utils.power_switch import PowerSwitch as pswtch
import cflib.crtp
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie


URI = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E702')

class ConsoleCollector:
    def __init__(self, URI):
        # self._cf = Crazyflie(rw_cache='./cache')
        self.logf = open('console_collector.log', 'w')
        self.scf = SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache'))
        self.scf.open_link()
        self._cf = self.scf.cf
        # self._cf.open_link(URI)
        print('[INFO]: Connecting to %s' % URI)
        # self.initialize(self.scf)
        self._cf.console.receivedChar.add_callback(self._log_console)

    def _log_console(self, text):
        # self.log_file.write(text)
        # print(text, end='')
        self.logf.write(text)

    def initialize(self, scf):
        print('initializing...')
        scf.cf.param.request_update_of_all_params()
        scf.cf.param.set_value('kalman.resetEstimation', '1')
        time.sleep(0.1)
        scf.cf.param.set_value('kalman.resetEstimation', '0')
        print('[INIT]: kalman prediction reset')
        scf.cf.param.set_value('health.startPropTest', '1') # propeller test before flight
        time.sleep(5)
        print('[INIT]: initialization complete')

    def terminate(self):
        self.scf.close_link()



if __name__ == '__main__':
    cflib.crtp.init_drivers()
    # print('[INFO]: Connecting to %s' % URI)
    cc = ConsoleCollector(URI)
    print('[INFO]: Starting console log')
    time.sleep(10)
    print('[INFO]: Stopping console log')
    # ConsoleCollector.scf.close_link()
    cc.terminate()
    # pswtch.platform_power_down()
