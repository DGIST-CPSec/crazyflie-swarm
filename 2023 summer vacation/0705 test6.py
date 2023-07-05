import time
import datetime
import os

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper
from cflib.utils.power_switch import PowerSwitch

# 리더와 팔로워의 URI
leader_uri = 'radio://0/80/2M/E7E7E7E701'
follower_uri = 'radio://0/80/2M/E7E7E7E702'

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

def mission_phlc(leader_cf, follower_cf, code, pos, pos_follower):
    takeoff_height = 1.0
    if code == 0:
        time.sleep(3)
        print('[MISSION]: begin to blink')
        for i in range(20):
            leader_cf.cf.param.set_value('led.bitmask', 255)
            follower_cf.cf.param.set_value('led.bitmask', 255)
            time.sleep(0.5)
            leader_cf.cf.param.set_value('led.bitmask', 0)
            follower_cf.cf.param.set_value('led.bitmask', 0)
            time.sleep(0.5)
    else:
        leader_phlc = MotionCommander(leader_cf, x=pos[0], y=pos[1], z=pos[2])
        follower_phlc = MotionCommander(follower_cf, x=pos_follower[0], y=pos_follower[1], z=pos_follower[2])
        
        leader_phlc.take_off(takeoff_height, 1.0)
        follower_phlc.take_off(takeoff_height, 1.0)
        time.sleep(5)
        print('[MISSION]: takeoff complete')
        # DEFAULT = 1.0
        leader_phlc.set_default_height(1.0)
        leader_phlc.set_default_velocity(0.5)
        follower_phlc.set_default_height(1.0)
        follower_phlc.set_default_velocity(0.5)
        leader_phlc.set_landing_height(0.0)
        follower_phlc.set_landing_height(0.0)
        
        if code == 1: # takeoff->up->down->land
            leader_phlc.up(0.5)
            follower_phlc.up(0.5)
            time.sleep(4)
            leader_phlc.down(0.5)
            follower_phlc.down(0.5)
            time.sleep(4)
        elif code == 2: # linear round trip
            leader_phlc.forward(1)
            follower_phlc.forward(1)
            time.sleep(4)
            leader_phlc.back(1)
            follower_phlc.back(1)
            time.sleep(4)
        elif code == 3: # triangular round trip
            leader_phlc.go_to(0.0, 1.2)
            follower_phlc.go_to(0.0, 1.2)
            time.sleep(4)
            leader_phlc.go_to(-1.2, 1.2)
            follower_phlc.go_to(-1.2, 1.2)
            time.sleep(4)
            leader_phlc.go_to(0.0, 0.0)
            follower_phlc.go_to(0.0, 0.0)
            time.sleep(4)
        elif code == 4: # square round trip
            leader_phlc.go_to(0.6, 0.6)
            follower_phlc.go_to(-0.6, 0.6)
            time.sleep(3)
            leader_phlc.go_to(0.6, -0.6)
            follower_phlc.go_to(0.6, -0.6)
            time.sleep(3)
            leader_phlc.go_to(-0.6, -0.6)
            follower_phlc.go_to(0.6, -0.6)
            time.sleep(3)
            leader_phlc.go_to(-0.6, 0.6)
            follower_phlc.go_to(-0.6, 0.6)
            time.sleep(3)
            leader_phlc.go_to(0.0, 0.0)
            follower_phlc.go_to(0.0, 0.0)
            time.sleep(3)
        elif code == 5: # circular round trip
            with MotionCommander(leader_cf, default_height=takeoff_height) as leader_mc, \
                 MotionCommander(follower_cf, default_height=takeoff_height) as follower_mc:
                leader_mc.circle_left(0.5, 0.4)
                follower_mc.circle_left(0.5, 0.4)
                time.sleep(10)
        else:
            time.sleep(5) # up-down

        print('[MISSION]: mission command complete')
        leader_phlc.land()
        follower_phlc.land()
        print('[MISSION]: landing')

def main():
    now = datetime.datetime.now()
    missNo = int(input('Mission type:\n[0] Blink\t[1] In-position\t[2] Line\t[3] Triangle\t[4] Square\t[5] Circle\t[6] Up-down\n>> '))
    init_pos = list(map(int, input('Start position of leader drone (x, y, z in meters):\n>> ').split()))
    init_pos_follower = list(map(int, input('Start position of follower drone (x, y, z in meters):\n>> ').split()))

    miss_type = ['NO', 'UD', 'LR', 'TR', 'SQ', 'CR', 'TO']
    logpath = './log/' + str(now)[5:10] + '/'
    if not os.path.exists(logpath):
        os.makedirs(logpath)

    logFile = open(
        './log/' + str(now)[5:10] + '/' + str(now)[11:19] + '_drone' + str(drone_addr[-2:]) + '_' + miss_type[
            missNo] + '.csv', 'w')

    cflib.crtp.init_drivers()

    with SyncCrazyflie(leader_uri, cf=Crazyflie(rw_cache='./cache')) as leader_cf, \
         SyncCrazyflie(follower_uri, cf=Crazyflie(rw_cache='./cache')) as follower_cf:
        try:
            initialize(leader_cf)
            initialize(follower_cf)

            # AREA: set log config
            logconf_leader = LogConfig(name='Position', period_in_ms=10)
            logconf_leader.add_variable('kalman.stateX', 'float')
            logconf_leader.add_variable('kalman.stateY', 'float')
            logconf_leader.add_variable('kalman.stateZ', 'float')
            logconf_leader.add_variable('acc.x', 'float')
            logconf_leader.add_variable('acc.y', 'float')
            logconf_leader.add_variable('acc.z', 'float')
            leader_cf.cf.log.add_config(logconf_leader)
            logconf_leader.data_received_cb.add_callback(log_data)

            logconf_follower = LogConfig(name='Position', period_in_ms=10)
            logconf_follower.add_variable('kalman.stateX', 'float')
            logconf_follower.add_variable('kalman.stateY', 'float')
            logconf_follower.add_variable('kalman.stateZ', 'float')
            logconf_follower.add_variable('acc.x', 'float')
            logconf_follower.add_variable('acc.y', 'float')
            logconf_follower.add_variable('acc.z', 'float')
            follower_cf.cf.log.add_config(logconf_follower)
            logconf_follower.data_received_cb.add_callback(log_data)

            # AREA: actual execution of mission
            logconf_leader.start()
            logconf_follower.start()
            mission_phlc(leader_cf, follower_cf, missNo, pos=init_pos, pos_follower=init_pos_follower)
            # <- NOTE: You should change mission in the function, NOT HERE!!
            logconf_leader.stop()
            logconf_follower.stop()
            logFile.close()
            print('[MAIN]: mission complete. Rebooting...')
        except KeyboardInterrupt:
            print('\n\n[MAIN]: EMERGENCY STOP TRIGGERED\n')
            logFile.close()


if __name__ == '__main__':
    main()
