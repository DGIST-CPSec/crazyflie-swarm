import time
import datetime
import os

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.positioning.position_hl_commander import PositionHlCommander

# 리더의 URI
leader_uri = 'radio://0/80/2M/E7E7E7E701'

def initialize(scf):
    scf.cf.param.request_update_of_all_params()
    scf.cf.param.set_value('kalman.resetEstimation', '1')
    time.sleep(0.1)
    scf.cf.param.set_value('kalman.resetEstimation', '0')
    print('[INIT]: kalman prediction reset')
    scf.cf.param.set_value('health.startPropTest', '1') # propeller test before flight
    time.sleep(5)
    print('[INIT]: initialization complete')

def mission_phlc(leader_cf, code, pos):
    takeoff_height = 1.0

    leader_phlc = PositionHlCommander(leader_cf, x=pos[0], y=pos[1], z=pos[2])

    leader_phlc.take_off(takeoff_height, 1.0)
    time.sleep(5)
    print('[MISSION]: takeoff complete')

    leader_phlc.set_default_height(1.0)
    leader_phlc.set_default_velocity(0.5)
    leader_phlc.set_landing_height(0.0)

    if code == 1: # takeoff->up->down->land
        leader_phlc.up(0.5)
        time.sleep(4)
        leader_phlc.down(0.5)
        time.sleep(4)
    elif code == 2: # linear round trip
        leader_phlc.forward(1)
        time.sleep(4)
        leader_phlc.back(1)
        time.sleep(4)
    elif code == 3: # triangular round trip
        leader_phlc.go_to(0.0, 1.2)
        time.sleep(4)
        leader_phlc.go_to(-1.2, 1.2)
        time.sleep(4)
        leader_phlc.go_to(0.0, 0.0)
        time.sleep(4)
    elif code == 4: # square round trip
        leader_phlc.go_to(0.6, 0.6)
        time.sleep(3)
        leader_phlc.go_to(0.6, -0.6)
        time.sleep(3)
        leader_phlc.go_to(-0.6, -0.6)
        time.sleep(3)
        leader_phlc.go_to(-0.6, 0.6)
        time.sleep(3)
        leader_phlc.go_to(0.0, 0.0)
        time.sleep(3)
    elif code == 5: # circular round trip
        with MotionCommander(leader_cf, default_height=takeoff_height) as leader_mc:
            leader_mc.circle_left(0.5, 0.4)
            time.sleep(10)
    else:
        time.sleep(5) # up-down

    print('[MISSION]: mission command complete')
    leader_phlc.land()
    print('[MISSION]: landing')

def main():
    now = datetime.datetime.now()
    missNo = int(input('Mission type:\n[0] Blink\t[1] In-position\t[2] Line\t[3] Triangle\t[4] Square\t[5] Circle\t[6] Up-down\n>> '))
    init_pos = list(map(int, input('Start position of leader drone (x, y, z in meters):\n>> ').split()))

    cflib.crtp.init_drivers()

    with SyncCrazyflie(leader_uri, cf=Crazyflie(rw_cache='./cache')) as leader_cf:
        try:
            initialize(leader_cf)
            mission_phlc(leader_cf, missNo, pos=init_pos)

            print('[MAIN]: mission complete. Rebooting...')
        except KeyboardInterrupt:
            print('\n\n[MAIN]: EMERGENCY STOP TRIGGERED\n')


if __name__ == '__main__':
    main()
