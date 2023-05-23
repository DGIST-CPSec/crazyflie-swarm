# This file does test for single-swarm, logging, with multiple possible options of movements
# Based on two official documents:
#     https://www.bitcraze.io/documentation/repository/crazyflie-lib-python/master/user-guides/sbs_motion_commander/
#     https://www.bitcraze.io/documentation/repository/crazyflie-lib-python/master/user-guides/sbs_swarm_interface/

import time, datetime, os

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper
from cflib.utils.power_switch import PowerSwitch
from cflib.positioning.position_hl_commander import PositionHlCommander
from cflib.utils.power_switch import PowerSwitch


drone_addr = 'radio://0/80/2M/E7E7E7E701'
URI = uri_helper.uri_from_env(default=drone_addr)
psw = PowerSwitch(uri=drone_addr)


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

def mission_phlc(scf, code, pos):
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
        phlc = PositionHlCommander(scf, x = pos[0], y= pos[1], z = pos[2])
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
            phlc.forward(1)
            time.sleep(4)
            phlc.back(1)
            time.sleep(4)

        elif code == 3: # triangular round trip
            phlc.go_to( 0.0, 1.2)
            time.sleep(4)
            phlc.go_to(-1.2, 1.2)
            time.sleep(4)
            phlc.go_to( 0.0, 0.0)
            time.sleep(4)

        elif code == 4: # square round trip
            phlc.go_to( 0.6,  0.6)
            time.sleep(3)
            phlc.go_to( 0.6, -0.6)
            time.sleep(3)
            phlc.go_to(-0.6, -0.6)
            time.sleep(3)
            phlc.go_to(-0.6,  0.6)
            time.sleep(3)
            phlc.go_to( 0.0,  0.0)
            time.sleep(3)

        elif code == 5: # circular round trip
            with MotionCommander(scf, default_height=takeoff_height) as mc:
                mc.circle_left(0.5, 0.4)
                time.sleep(10)

        else:
            time.sleep(5) # up-down
            
        print('[MISSION]: mission command complete')
        phlc.land()
        print('[MISSION]: landing')


if __name__ == '__main__':
    now = datetime.datetime.now()
    missNo    = int(input('Mission type: \n[0]Blink \t[1]In-position \t[2]Line \t[3]Triangle \t[4]Square \t[5]Circle \t[6]Up-down\n >>'))
    init_pos = list(map(int, input('start position- x, y, z (m) >> ').split(' ')))
    miss_type = ['NO', 'UD', 'LR', 'TR', 'SQ', 'CR', 'TO']
    # Mission Codes:
    # 0: NOOP just blink
    # 1: UPDN up-down
    # 2: LINE linear
    # 3: TRIA triangular
    # 4: SQUA square
    # 5: CIRC circular
    # 6: TAKO takeoff only
    logpath ='./log/'+str(now)[5:10]+'/' 
    if not os.path.exists(logpath):
        os.mkdir(logpath)
    
    logFile = open('./log/'
                   +str(now)[5:10]+'/'
                   +str(now)[11:19]+'_drone'+str(drone_addr[-2:])+'_'+miss_type[missNo]+'.csv', 'w')
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
            mission_phlc(scf, missNo, pos=init_pos)
            # <- NOTE: You should change mission in the function, NOT HERE!!
            logconf.stop()
            logFile.close()
            print('[MAIN]: mission complete. Rebooting...')
            psw.reboot_to_fw()

        except KeyboardInterrupt:
            psw.platform_power_down()
            print('\n\n[MAIN]: EMERGENCY STOP TRIGGERED\n['+str(hex(psw.address[4]))+']: SHUTDOWN\n')
            logFile.close()