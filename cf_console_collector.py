# collect console printf strings from crazyflie.console
import time, datetime, os
# from threading import Event
from cflib.crazyflie import Crazyflie
# from cflib.crazyflie.console import Console as cf_console
from cflib.utils import uri_helper
# from cflib.utils.power_switch import PowerSwitch as pswtch
import cflib.crtp
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crtp import pcap as crtp_pcap

URI = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E70A')
execdate = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
logat = os.path.join('./collected', execdate+'.txt')

class ConsoleCollector:
    def __init__(self, URI):
        self.logf = open(logat, 'w')
        self.scf = SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache'))
        print('[INFO]: Connecting to %s' % URI)
        self.scf.open_link()
        print('Connected!')
        self._cf = self.scf.cf
        self._cf.console.receivedChar.add_callback(self._log_console)
        # self._cf.open_link(URI)
        # self.initialize(self.scf)

    def _log_console(self, txt):
        self.logf.write(txt)

    def initialize(self, scf):
        print('initializing...')
        scf.param.request_update_of_all_params()
        scf.cf.param.set_value('kalman.resetEstimation', '1')
        time.sleep(0.1)
        scf.cf.param.set_value('kalman.resetEstimation', '0')
        print('[INIT]: kalman prediction reset')
        scf.cf.param.set_value('health.startPropTest', '1') # propeller test before flight
        time.sleep(5)
        print('[INIT]: initialization complete')

    def terminate(self):
        self.scf.close_link()
        self.logf.close()
        print('[INFO]: Console log terminated')



if __name__ == '__main__':
    # print('whatever just started')
    cflib.crtp.init_drivers() 
    cc = ConsoleCollector(URI)
    print('[INFO]: Starting console log')
    time.sleep(10)
    print('[INFO]: Stopping console log')
    cc.terminate()
    # pswtch.platform_power_down()
