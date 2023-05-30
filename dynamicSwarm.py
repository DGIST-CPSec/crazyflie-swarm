import time, datetime, os

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.high_level_commander import HighLevelCommander
from cflib.utils import uri_helper
from cflib.utils.power_switch import PowerSwitch
# from cflib.positioning.position_hl_commander import PositionHlCommander

from cflib.crazyflie.swarm import Swarm, CachedCfFactory

drones = [
    'radio://0/80/2M/E7E7E7E701',
    'radio://0/80/2M/E7E7E7E702',
    'radio://0/80/2M/E7E7E7E703',
    'radio://0/80/2M/E7E7E7E704',
    'radio://0/80/2M/E7E7E7E705',
    'radio://0/80/2M/E7E7E7E70A',
    'radio://0/80/2M/E7E7E7E70B',
    'radio://0/80/2M/E7E7E7E70C',
    'radio://0/80/2M/E7E7E7E70D',
    'radio://0/80/2M/E7E7E7E70E',
]


psws = [PowerSwitch(uri) for uri in drones]

leader = [0.0, 1.0, 0.0]

distance = [
    [+0.0, +0.0,  0.0],
    [-0.5, -0.5, -0.3], [+0.5, -0.5, -0.3],
    [-1.0, -1.0, -0.6], [+0.0, -1.0, -0.6], [+1.0, -1.0, -0.6],
    [-1.5, -1.5, -0.9], [-0.5, -1.5, -0.9], 
    [+0.5, -1.5, -0.9], 
    [+1.5, -1.5, -0.9],
]

# factory = Factory()

# scfs = [factory.construct(uri) for uri in drones]



def get_next_position(leader, distance):
    """ calculates next position of follower drones """
    return [[sum(x) for x in zip(leader, distance[i])] for i in range(len(drones))]

def order_follow(timestamp, data, logconf):
    print(timestamp,":", data['kalman.stateX'], data['kalman.stateY'], data['kalman.stateZ'])
    pos_leader = [data['kalman.stateX'], data['kalman.stateY'], data['kalman.stateZ']]
    newpos = get_next_position(leader=pos_leader, distance=distance)
    # go to next calculated position
    for i in range(1, len(drones)):
        hlcs[i].go_to(newpos[i][0], newpos[i][1], newpos[i][2], 0, 0.01)
        pass
    pass


def leader_mission(scf, code, pos):
    takeoff_height = 1.6
    lhlc = scf.cf.high_level_commander
    # lhlc.take_off(takeoff_height, 2.0)
    time.sleep(5)
    print('[MISSION]: takeoff complete')
    # DEFAULT = 1.0
    # phlc.set_default_height(1.0)
    # phlc.set_default_velocity(0.5)
    # phlc.set_landing_height(0.0)
    if code == 1: # takeoff->up->down->land
        lhlc.go_to(0, 0, 0.5, 0, 2, relative=True)
        time.sleep(3)
        lhlc.go_to(0, 0,-0.5, 0, 2, relative=True)
        time.sleep(3)
        
    elif code == 2: # forward-backward round trip
        lhlc.go_to( 0.5, 0.0, 0.0, 0, 2, relative=True)
        time.sleep(4)
        lhlc.go_to(-0.5, 0.0, 0.0, 0, 2, relative=True)
        time.sleep(4)

    elif code == 3: # left-right round trip
        lhlc.go_to(0.0, 0.5, 0.0, 0, 2, relative=True)
        time.sleep(4)
        lhlc.go_to(0.0,-0.5, 0.0, 0, 2, relative=True)
        time.sleep(4)

    elif code == 4: # square round trip
        lhlc.go_to( 0.4,  0.4, 0, 0, 2, relative=True)
        time.sleep(3)
        lhlc.go_to( 0.4, -0.4, 0, 0, 2, relative=True)
        time.sleep(3)
        lhlc.go_to(-0.4, -0.4, 0, 0, 2, relative=True)
        time.sleep(3)
        lhlc.go_to(-0.4,  0.4, 0, 0, 2, relative=True)
        time.sleep(3)
        lhlc.go_to( 0.0,  0.0, 0, 0, 2, relative=True)
        time.sleep(3)

    else:
        time.sleep(5) # up-down
        
    print('[MISSION]: mission command complete')
    lhlc.land()
    print('[MISSION]: landing')



if __name__ == '__main__':
    try:
        # DANGER: follow calculation in every 10 ms may be too fast: 
        cflib.crtp.init_drivers()
        print("initialized")

        scfs = [SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) for uri in drones]
        for scf in scfs:
            scf.open_link()
            print("opened link: ", scf.cf.link_uri)

        hlcs = [scf.cf.high_level_commander for scf in scfs]
        # slow down if not working well
        mission = int(input('Enter mission code: [1] up-down, [2] forward-backward, [3] left-right, [4] square'))
        logconf = LogConfig(name='Position', period_in_ms=10)
        logconf.add_variable('kalman.stateX', 'float')
        logconf.add_variable('kalman.stateY', 'float')
        logconf.add_variable('kalman.stateZ', 'float')
        leader_scf = scfs[0]
        leader_scf.cf.log.add_config(logconf)
        logconf.data_received_cb.add_callback(order_follow)
        print('[MAIN]: starting mission')
        logconf.start()
        for drone in hlcs:
            drone.takeoff(1.0, 2.0)
        leader_mission(leader_scf, mission, pos=leader)
        logconf.stop()
        for psw in psws:
            psw.reboot_to_fw()
        print("[MAIN]: MISSION COMPLETE\n")
    
    except KeyboardInterrupt:
        for i in range(len(drones)):
            psws[i].platform_power_down()
            print('\n\n[MAIN]: EMERGENCY STOP TRIGGERED\n['+str(hex(psws[i].address[4]))+']: SHUTDOWN\n')
        print('\nYou should turn the drones back on to resume experiment.\n')
        # close logger