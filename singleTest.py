# This file does test for single-swarm, logging, with multiple possible options of movements
# Based on two official documents:
#     https://www.bitcraze.io/documentation/repository/crazyflie-lib-python/master/user-guides/sbs_motion_commander/
#     https://www.bitcraze.io/documentation/repository/crazyflie-lib-python/master/user-guides/sbs_swarm_interface/

import logging
import sys
import time, datetime
from threading import Event

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper


URI = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E705')
deck_attached_event = Event()

DEFAULT_HEIGHT = 0.5
BOX_LIMIT = 0.5

def param_deck_flow(_, value_str):
    value = int(value_str)
    print(value)
    if value:
        print('Deck is attached!')
    else:
        print('Deck is NOT attached!')

def log_data(timestamp, data, logconf):
    dataAsList = list(map(str, [str(timestamp/1000), 
                                data['kalman.stateX'], data['kalman.stateY'], data['kalman.stateZ'], 
                                data['acc.x'], data['acc.y'], data['acc.z']
                                ]))
    logFile.write(','.join(dataAsList)+"\n")
    print('\t'.join(dataAsList))

def mission(scf, code):
    takeoff_height = 0.40
    if code == 0:
        for i in range(20):
            scf.cf.param.set_value('led.bitmask', 255)
            time.sleep(0.5)
            scf.cf.param.set_value('led.bitmask', 0)
            time.sleep(0.5)
    else:
        hlcomm = scf.cf.high_level_commander
        hlcomm.takeoff(takeoff_height, 3.0)
        time.sleep(4)
        if code == 1: # rotate in-place
            hlcomm.go_to(0.0, 0.0, 0.0,  180, 2.0, relative=True)
            time.sleep(4)
            hlcomm.go_to(0.0, 0.0, 0.0,  180, 3.0, relative=True)
            time.sleep(4)
            hlcomm.go_to(0.0, 0.0, 0.0, -180, 2.0, relative=True)
            time.sleep(4)
            hlcomm.go_to(0.0, 0.0, 0.0, -180, 3.0, relative=True)
            time.sleep(4)
            
        elif code == 2: # linear round trip
            hlcomm.go_to( 0.3,  0.3, 0, 0, 3.0, relative=True)
            time.sleep(4)
            hlcomm.go_to(-0.3, -0.3, 0, 0, 3.0, relative=True)
            time.sleep(4)

        elif code == 3: # triangular round trip
            hlcomm.go_to( 0.4,  0.2, 0, 0, 3.0, relative=True)
            time.sleep(4)
            hlcomm.go_to(-0.4,  0.2, 0, 0, 3.0, relative=True)
            time.sleep(4)
            hlcomm.go_to( 0.0, -0.4, 0, 0, 3.0, relative=True)
            time.sleep(4)
            pass
        elif code == 4: # square round trip
            hlcomm.go_to(  0.5,   0, 0, 0, 3.0, relative=True)
            time.sleep(4)
            hlcomm.go_to(    0, 0.5, 0, 0, 3.0, relative=True)
            time.sleep(4)
            hlcomm.go_to( -0.5,   0, 0, 0, 3.0, relative=True)
            time.sleep(4)
            hlcomm.go_to(    0,-0.5, 0, 0, 3.0, relative=True)
            time.sleep(4)

        elif code == 5: # circular round trip
            with MotionCommander(scf, default_height=takeoff_height) as mc:
                mc.circle_left(0.5, 0.4)
                time.sleep(10)

        else:
            time.sleep(6)
            
        hlcomm.land(0, 3)

def initialize(scf):
    scf.cf.param.request_update_of_all_params()
    scf.cf.param.set_value('health.startPropTest', '1') # propeller test before flight
    time.sleep(5)

    scf.cf.param.set_value('kalman.resetEstimation', '1')
    time.sleep(0.1)
    scf.cf.param.set_value('kalman.resetEstimation', '0')
    print('kalman prediction reset')


if __name__ == '__main__':
    now = datetime.datetime.now()
    logFile = open('./log/'+str(now)[:19]+'.csv', 'w')
    cflib.crtp.init_drivers()
    try:
        cflib.crtp.init_drivers()
        with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
            initialize(scf)

            # AREA: set log config
            logconf = LogConfig(name='Position', period_in_ms=10)
            logconf.add_variable('kalman.stateX', 'float')
            logconf.add_variable('kalman.stateY', 'float')
            logconf.add_variable('kalman.stateZ', 'float')
            logconf.add_variable('acc.x', 'float')
            logconf.add_variable('acc.y', 'float')
            logconf.add_variable('acc.z', 'float')
            scf.cf.log.add_config(logconf)

            logconf.data_received_cb.add_callback(log_data)

            # if not deck_attached_event.wait(timeout=5): <- FIXME: I don't know what does this mean, but it keeps failing~
            #     print('No flow deck found, aborting')
            #     sys.exit(1)

            # AREA: actual execution of mission
            logconf.start()
            mission(scf, 6) # <- NOTE> You should change mission in the function, NOT HERE!!
            logconf.stop()

        logFile.close()

    # at escape by Ctrl+C
    except KeyboardInterrupt:
        print('Interrupted by user')
        logFile.close()