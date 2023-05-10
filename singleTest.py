# This file does test for single-swarm, logging, with multiple possible options of movements
# Based on two official documents:
#     https://www.bitcraze.io/documentation/repository/crazyflie-lib-python/master/user-guides/sbs_motion_commander/
#     https://www.bitcraze.io/documentation/repository/crazyflie-lib-python/master/user-guides/sbs_swarm_interface/

import time, datetime
from threading import Event

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper
from cflib.utils.power_switch import PowerSwitch
from cflib.crazyflie.localization import Localization as cflc
from cflib.positioning.position_hl_commander import PositionHlCommander


URI = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E705')
deck_attached_event = Event()


def initialize(scf):
    scf.cf.param.request_update_of_all_params()
    scf.cf.param.set_value('kalman.resetEstimation', '1')
    time.sleep(0.1)
    scf.cf.param.set_value('kalman.resetEstimation', '0')
    print('[INIT]: kalman prediction reset')
    scf.cf.param.set_value('health.startPropTest', '1') # propeller test before flight
    time.sleep(5)
    print('[INIT]: initialization complete')


def log_data(timestamp, data, logconf):
    dataAsList = list(map(str, [str(timestamp/1000), 
                                data['kalman.stateX'], data['kalman.stateY'], data['kalman.stateZ'], 
                                data['acc.x'], data['acc.y'], data['acc.z']
                                ]))
    logFile.write(','.join(dataAsList)+"\n")

def mission_relative(scf, code):
    takeoff_height = 1.0
    if code == 0:
        time.sleep(3)
        print('[MISSION]: begin to blink')
        for i in range(20):
            scf.cf.param.set_value('led.bitmask', 255)
            time.sleep(0.5)
            scf.cf.param.set_value('led.bitmask', 0)
            time.sleep(0.5)
    else:
        hlcomm = scf.cf.high_level_commander
        hlcomm.takeoff(takeoff_height, 1.0)
        time.sleep(5)
        print('[MISSION]: takeoff complete')

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
            hlcomm.go_to( 0.7,  0.7, 0, 0, 3.0, relative=True)
            time.sleep(4)
            hlcomm.go_to(-0.7, -0.7, 0, 0, 3.0, relative=True)
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
            time.sleep(6) # up-down
            
        print('[MISSION]: mission command complete')
        hlcomm.land(0, 3)
        print('[MISSION]: landing')


def mission_absolute(scf, code):
    takeoff_height = 1.0
    if code == 0:
        time.sleep(3)
        print('[MISSION]: begin to blink')
        for i in range(20):
            scf.cf.param.set_value('led.bitmask', 255)
            time.sleep(0.5)
            scf.cf.param.set_value('led.bitmask', 0)
            time.sleep(0.5)
    else:
        hlcomm = scf.cf.high_level_commander
        hlcomm.takeoff(takeoff_height, 1.0)
        time.sleep(5)
        print('[MISSION]: takeoff complete')
        
        if code == 1: # rotate in-place
            hlcomm.go_to(0.0, 0.0, 1.0,   90, 3.0, relative=False)
            time.sleep(4)
            hlcomm.go_to(0.0, 0.0, 1.0,  180, 3.0, relative=False)
            time.sleep(4)
            hlcomm.go_to(0.0, 0.0, 1.0,   90, 3.0, relative=False)
            time.sleep(4)
            hlcomm.go_to(0.0, 0.0, 1.0,    0, 3.0, relative=False)
            time.sleep(4)
            
        elif code == 2: # linear round trip
            hlcomm.go_to( 0.7,  0.7, 1.0, 0, 3.0, relative=False)
            time.sleep(4)
            hlcomm.go_to( 0.0,  0.0, 1.0, 0, 3.0, relative=False)
            time.sleep(4)

        elif code == 3: # triangular round trip
            hlcomm.go_to( 0.0,  0.6, 1.0, 0, 3.0, relative=False)
            time.sleep(4)
            hlcomm.go_to( 0.4, -0.2, 1.0, 0, 3.0, relative=False)
            time.sleep(4)
            hlcomm.go_to(-0.4, -0.2, 1.0, 0, 3.0, relative=False)
            time.sleep(4)
            hlcomm.go_to( 0.0,  0.6, 1.0, 0, 3.0, relative=False)
            time.sleep(4)
            hlcomm.go_to( 0.0,  0.0, 1.0, 0, 3.0, relative=False)
            time.sleep(4)
            
        elif code == 4: # square round trip
            hlcomm.go_to(  0.5, 0.0, 1.0, 0, 3.0, relative=False)
            time.sleep(4)
            hlcomm.go_to(  0.5, 0.5, 1.0, 0, 3.0, relative=False)
            time.sleep(4)
            hlcomm.go_to(  0.0, 0.5, 1.0, 0, 3.0, relative=False)
            time.sleep(4)
            hlcomm.go_to(  0.0, 0.0, 1.0, 0, 3.0, relative=False)
            time.sleep(4)

        elif code == 5: # circular round trip
            with MotionCommander(scf, default_height=takeoff_height) as mc:
                mc.circle_left(0.5, 0.4)
                time.sleep(10)

        else:
            time.sleep(6) # up-down
            
        print('[MISSION]: mission command complete')
        hlcomm.land(0, 3)
        print('[MISSION]: landing')


def mission_phlc(scf, code):
    takeoff_height = 1.0
    if code == 0:
        time.sleep(3)
        print('[MISSION]: begin to blink')
        for i in range(20):
            scf.cf.param.set_value('led.bitmask', 255)
            time.sleep(0.5)
            scf.cf.param.set_value('led.bitmask', 0)
            time.sleep(0.5)
    else:
        phlc = PositionHlCommander(scf)
        phlc.take_off(takeoff_height, 1.0)
        time.sleep(5)
        print('[MISSION]: takeoff complete')
        # DEFAULT = 1.0
        phlc.set_default_height(1.0)
        phlc.set_default_velocity(0.5)
        phlc.set_landing_height(0.0)
        if code == 1: # takeoff->up->down->land
            # phlc.go_to(0.0, 0.0, 1.0)
            # time.sleep(4)
            phlc.up(0.5)
            time.sleep(4)
            phlc.down(0.5)
            time.sleep(4)
            
        elif code == 2: # linear round trip
            phlc.forward(0.5)
            time.sleep(4)
            phlc.back(0.5)
            time.sleep(4)

        elif code == 3: # triangular round trip
            phlc.go_to( 0.4, 0.2)
            time.sleep(4)
            phlc.go_to(-0.4, 0.2)
            time.sleep(4)
            phlc.go_to( 0.0,-0.4)
            time.sleep(4)

        elif code == 4: # square round trip
            phlc.go_to( 0.5, 0.0)
            time.sleep(4)
            phlc.go_to( 0.5, 0.5)
            time.sleep(4)
            phlc.go_to( 0.0, 0.5)
            time.sleep(4)
            phlc.go_to( 0.0, 0.0)
            time.sleep(4)

        elif code == 5: # circular round trip
            with MotionCommander(scf, default_height=takeoff_height) as mc:
                mc.circle_left(0.5, 0.4)
                time.sleep(10)

        else:
            time.sleep(6) # up-down
            
        print('[MISSION]: mission command complete')
        phlc.land()
        print('[MISSION]: landing')



if __name__ == '__main__':
    now = datetime.datetime.now()
    comm_type = int(input('Command Type: \t[1]Relative \t[2]Absolute \t[3]PHLComm'))
    missNo    = int(input('Mission type: \t[0]Blink \t[1]In-position \t[2]Line \t[3]Triangle \t[4]Square \t[5]Circle \t[6]Up-down'))
    logFile = open('./log/'+str(now)[5:19]+'_'+str(comm_type)+str(missNo)+'.csv', 'w')
    cflib.crtp.init_drivers()

    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
        try:
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

            # AREA: actual execution of mission
            logconf.start()
            if comm_type == 1:
                mission_relative(scf, missNo)
            elif comm_type == 2:
                mission_absolute(scf, missNo)
            elif comm_type == 3:
                mission_phlc(scf, missNo)
            else:
                print('[ERROR]: invalid communication type')
            # <- NOTE: You should change mission in the function, NOT HERE!!
            logconf.stop()
            logFile.close()
            PowerSwitch.reboot_to_bootloader()  # FIXME: added, may not be working properly.

        except KeyboardInterrupt:
            cflc.send_emergency_stop()          # FIXME: added, may not be working properly.
            scf.cf.high_level_commander.stop()
            print('EMERGENCY STOP TRIGGERED')
            PowerSwitch.platform_power_down()   # FIXME: added, may not be working properly.
            logFile.close()