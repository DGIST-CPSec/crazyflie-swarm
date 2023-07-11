import time
import datetime
import os
import math

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.positioning.position_hl_commander import PositionHlCommander
from cflib.crazyflie.log import LogConfig

# URI to the Crazyflie to connect to
leader_uri = 'radio://0/80/2M/E7E7E7E701'
follower_uri = 'radio://0/80/2M/E7E7E7E702'

follower_phlc = None

follower_x, follower_y, follower_z = 0, 0, 0  # Initialize follower drone's position

def initialize(scf):
    scf.cf.param.request_update_of_all_params()
    scf.cf.param.set_value('kalman.resetEstimation', '1')
    time.sleep(0.1)
    scf.cf.param.set_value('kalman.resetEstimation', '0')
    print('[INIT]: kalman prediction reset')
    scf.cf.param.set_value('health.startPropTest', '1')  # propeller test before flight
    time.sleep(5)
    print('[INIT]: initialization complete')

def position_callback(timestamp, data, logconf):
    leader_x = data['stateEstimate.x']
    leader_y = data['stateEstimate.y']
    leader_z = data['stateEstimate.z']
    print('Position: ({}, {}, {})'.format(leader_x, leader_y, leader_z))

    # 팔로워 드론과 리더 드론 사이의 방향 벡터를 계산합니다.
    direction_x = follower_x - leader_x
    direction_y = follower_y - leader_y
    direction_z = follower_z - leader_z

    # 방향 벡터를 정규화하여 단위 벡터를 구합니다.
    magnitude = math.sqrt(direction_x ** 2 + direction_y ** 2 + direction_z ** 2)
    unit_x = direction_x / magnitude
    unit_y = direction_y / magnitude
    unit_z = direction_z / magnitude

    # 팔로워 드론의 목표 위치를 리더 드론에서 일정 거리만큼 떨어진 위치로 설정합니다.
    target_x = leader_x + unit_x * 0.3
    target_y = leader_y + unit_y * 0.3
    target_z = leader_z + unit_z * 0.3
    follower_phlc.go_to(target_x, target_y, target_z)

def follower_position_callback(timestamp, data, logconf):
    global follower_x, follower_y, follower_z
    follower_x = data['stateEstimate.x']
    follower_y = data['stateEstimate.y']
    follower_z = data['stateEstimate.z']

logconf = LogConfig(name='Position', period_in_ms=100)
logconf.add_variable('stateEstimate.x', 'float')
logconf.add_variable('stateEstimate.y', 'float')
logconf.add_variable('stateEstimate.z', 'float')

# Create separate LogConfig for follower drone
follower_logconf = LogConfig(name='Follower Position', period_in_ms=100)
follower_logconf.add_variable('stateEstimate.x', 'float')
follower_logconf.add_variable('stateEstimate.y', 'float')
follower_logconf.add_variable('stateEstimate.z', 'float')

# Other parts of the code remain the same...



def mission_phlc(leader_cf, follower_cf, code, leader_pos, follower_pos):
    global follower_phlc
    takeoff_height = 1.0

    leader_phlc = PositionHlCommander(leader_cf, x=leader_pos[0], y=leader_pos[1], z=leader_pos[2])
    follower_phlc = PositionHlCommander(follower_cf, x=follower_pos[0], y=follower_pos[1], z=follower_pos[2])

    leader_phlc.take_off(takeoff_height, 1.0)
    follower_phlc.take_off(takeoff_height, 1.0)  # 팔로워 드론도 같이 이륙
    time.sleep(5)
    print('[MISSION]: takeoff complete')

    leader_phlc.set_default_height(1.0)
    follower_phlc.set_default_height(1.0)
    leader_phlc.set_default_velocity(0.5)
    follower_phlc.set_default_velocity(0.5)
    leader_phlc.set_landing_height(0.0)
    follower_phlc.set_landing_height(0.0)

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
            
    elif code == 6:  # "Z" shaped movement
        #Step 1: Drone moves forward while ascending
        leader_phlc.go_to(1.0, 0.0, 1.0)
        time.sleep(4)

        # Step 2: Drone moves backward while descending
        leader_phlc.go_to(-1.0, 0.0, 0.0)
        time.sleep(4)

    else:
        time.sleep(5) # up-down

    print('[MISSION]: mission command complete')
    leader_phlc.land()
    follower_phlc.land()
    print('[MISSION]: landing')

def main():
    now = datetime.datetime.now()
    missNo = int(input('Mission type:\n[0] Blink\t[1] In-position\t[2] Line\t[3] Triangle\t[4] Square\t[5] Circle\t[6] Up-down\n>> '))
    leader_init_pos = list(map(int, input('Start position of leader drone (x, y, z in meters):\n>> ').split()))
    follower_init_pos = list(map(int, input('Start position of follower drone (x, y, z in meters):\n>> ').split()))

    cflib.crtp.init_drivers()

    with SyncCrazyflie(leader_uri, cf=Crazyflie(rw_cache='./cache')) as leader_cf, \
         SyncCrazyflie(follower_uri, cf=Crazyflie(rw_cache='./cache')) as follower_cf:
        try:
            initialize(leader_cf)
            initialize(follower_cf)

            leader_cf.cf.log.add_config(logconf)
            logconf.data_received_cb.add_callback(position_callback)
            logconf.start()
            
            follower_cf.cf.log.add_config(follower_logconf)
            follower_logconf.data_received_cb.add_callback(follower_position_callback)
            follower_logconf.start()
            
            mission_phlc(leader_cf, follower_cf, missNo, leader_init_pos, follower_init_pos)

            print('[MAIN]: mission complete. Rebooting...')
        except KeyboardInterrupt:
            print('\n\n[MAIN]: EMERGENCY STOP TRIGGERED\n')

if __name__ == '__main__':
    main()
