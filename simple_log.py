import logging
import time

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander

from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncLogger import SyncLogger

# URI to the Crazyflie to connect to
uri = 'radio://0/80/2M/E7E7E7E703'

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)

def simple_log(scf, logconf):

    with SyncLogger(scf, log_pos) as logger:

        for log_entry in logger:

            timestamp = log_entry[0]
            data = log_entry[1]
            logconf_name = log_entry[2]

            print('[%d][%s]: %s' % (timestamp, logconf_name, data))

            break
...
# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)

def log_stab_callback(timestamp, data, logconf):
    print('[%d][%s]: %s' % (timestamp, logconf.name, data))

def simple_log_async(scf, logconf):
    cf = scf.cf
    cf.log.add_config(logconf)
    logconf.data_received_cb.add_callback(log_stab_callback)
    logconf.start()
    time.sleep(20)
    logconf.stop()

def simple_log(scf, logconf):

    with SyncLogger(scf, log_pos) as logger:

        for log_entry in logger:

            timestamp = log_entry[0]
            data = log_entry[1]
            logconf_name = log_entry[2]

            print('[%d][%s]: %s' % (timestamp, logconf_name, data), file='output.log')

            break

if __name__ == '__main__':
    # Initialize the low-level drivers
    cflib.crtp.init_drivers()

    log_pos = LogConfig(name='Position', period_in_ms=10)
    log_pos.add_variable('kalman.stateX', 'float')
    log_pos.add_variable('kalman.stateY', 'float')
    log_pos.add_variable('kalman.stateZ', 'float')
    log_pos.add_variable('stabilizer.roll', 'float')
    log_pos.add_variable('stabilizer.pitch', 'float')
    log_pos.add_variable('stabilizer.yaw', 'float')

    with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
        # simple_connect()
        # simple_log_async(scf, lg_stab)
        with MotionCommander(scf, default_height=0.2) as mc:
            print('Taking off!')
            simple_log(scf, log_pos)
            time.sleep(2)
            for i in range(1):

                mc.turn_right(90)
                simple_log(scf, log_pos)

                time.sleep(1)
                mc.turn_left(90)
                simple_log(scf, log_pos)

                time.sleep(1)
                mc.up(0.2)
                simple_log(scf, log_pos)

                time.sleep(1)
                mc.forward(0.5)
                simple_log(scf, log_pos)

                time.sleep(1)
                mc.back(0.5)
                simple_log(scf, log_pos)

                time.sleep(3)
                mc.down(0.4)
                simple_log(scf, log_pos)

                time.sleep(1)