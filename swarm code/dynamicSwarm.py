import time
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.high_level_commander import HighLevelCommander
from cflib.utils.power_switch import PowerSwitch
from cflib.crazyflie.syncLogger import SyncLogger

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
    # 01
    [ 0.0,  0.0,  0.0],
    # 02                03
    [-0.5, -0.5,  0.0], [ 0.5, -0.5,  0.0],
    # 04                05                  0A
    [-1.0, -1.0,  0.0], [ 0.0, -1.0,  0.0], [ 1.0, -1.0,  0.0],
    # 0B                0C                  0D                  0E
    [-1.5, -1.5,  0.0], [-0.5, -1.5,  0.0], [ 0.5, -1.5,  0.0], [ 1.5, -1.5,  0.0],
]

# def get_next_position(leader, distance):
#     """ calculates next position of follower drones """
#     ret = []
#     for i in range(len(drones)):
#         retpos = []
#         retpos.append(leader[0] + distance[i][0])
#         retpos.append(leader[1] + distance[i][1])
#         retpos.append(max(0, leader[2] + distance[i][2]))
#         ret.append(retpos)
#     return ret

def order_follow(timestamp, data, logconf):
    print(timestamp,":", data)
    # leader = [data['kalman.stateX'], data['kalman.stateY'], data['kalman.stateZ']]
    for i in range(len(drones)):
        retpos = []
        retpos.append(leader[0] + distance[i][0])
        retpos.append(leader[1] + distance[i][1])
        retpos.append(max(0, leader[2] + distance[i][2]))
        hlcs[i].go_to(retpos[0], retpos[1], retpos[2], 0, 0.1, relative=False)
        # print("drone", i, "go to", retpos)
    # newpos = get_next_position(leader=pos_leader, distance=distance)
    # go to next calculated position
    # for i in range(0, len(drones)):
        # hlcs[i].go_to(newpos[i][0], newpos[i][1], newpos[i][2], 0, 0.1, relative=False)
    time.sleep(0.1)
    # print("\n\n")


def leader_mission(scf, code):
    lhlc = scf.cf.high_level_commander
    print("in leader mission", code)
    if code == 1: # takeoff->up->down->land
        lhlc.go_to(0, 0, 0.3, 0, 3, relative=True)
        print("goto sent")
        time.sleep(3)
        print("sleep done")
        lhlc.go_to(0, 0,-0.3, 0, 3, relative=True)
        print("goto sent")
        time.sleep(3)
        print("sleep done")
        
    elif code == 2: # forward-backward round trip
        lhlc.go_to( 0.5, 0.0, 0.0, 0, 3, relative=True)
        time.sleep(3)
        lhlc.go_to(-0.5, 0.0, 0.0, 0, 3, relative=True)
        time.sleep(3)

    elif code == 3: # left-right round trip
        lhlc.go_to(0.0, 0.5, 0.0, 0, 3, relative=True)
        time.sleep(3)
        lhlc.go_to(0.0,-0.5, 0.0, 0, 3, relative=True)
        time.sleep(3)

    elif code == 4: # square round trip
        lhlc.go_to( 0.4,  0.4, 0, 0, 3, relative=True)
        time.sleep(3)
        lhlc.go_to( 0.4, -0.4, 0, 0, 3, relative=True)
        time.sleep(3)
        lhlc.go_to(-0.4, -0.4, 0, 0, 3, relative=True)
        time.sleep(3)
        lhlc.go_to(-0.4,  0.4, 0, 0, 3, relative=True)
        time.sleep(3)
        lhlc.go_to( 0.0,  0.0, 0, 0, 3, relative=True)
        time.sleep(3)
    else:
        # lhlc.go_to(0,0,0,0,3, relative=True) # hold
        time.sleep(3)
        
    print('[LEADER]: mission command complete')

def synchronous_mission(scf, logconf):
    with SyncLogger(scf, logconf) as logger:
        for log_entry in logger:
            timestamp = log_entry[0]
            data = log_entry[1]
            # print(timestamp,":", data['kalman.stateX'], data['kalman.stateY'], data['kalman.stateZ'])
            order_follow(timestamp, data, logconf)
            break

def asynchronous_mission(scf, logconf, mission_code):
    try:
        cf = scf.cf
        cf.log.add_config(logconf)
        logconf.data_received_cb.add_callback(order_follow)
        logconf.start()
        print('logconf start')
        leader_mission(scf, mission_code)
        logconf.stop()
        print('logconf stop')
    except KeyboardInterrupt:
        triggerRestart()

def triggerRestart():
    for i in range(len(drones)):
        psws[i].reboot_to_fw()
        print('[MAIN]: EMERGENCY STOP TRIGGERED\n['+str(hex(psws[i].address[4]))+']: Restarting...')
        scfs[i].close_link()

if __name__ == '__main__':
    try:
        cflib.crtp.init_drivers()
        print("initialized")

        scfs = [SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) for uri in drones]
        for i in range(len(scfs)):
            scfs[i].open_link()
            # psws[i].reboot_to_fw()
            print("[SWARM] opened link: ", scfs[i].cf.link_uri)

        hlcs = [scf.cf.high_level_commander for scf in scfs]

        mission = int(input('Enter mission code: [1] up-down, [2] forward-backward, [3] left-right, [4] square, [0] hold: \n>>> '))
        logconf = LogConfig(name='Position', period_in_ms=100)
        # DANGER: follow calculation in every 10 ms may be too fast: 
        # slow down if not working well
        logconf.add_variable('kalman.stateX', 'float')
        logconf.add_variable('kalman.stateY', 'float')
        logconf.add_variable('kalman.stateZ', 'float')
        leader_scf = scfs[0]

        print('[MAIN]: starting mission')
        # hlcs[0].takeoff(1.0, 3.0)
        for drone in hlcs:
            drone.takeoff(0.5, 3.0)
        time.sleep(3)
        print('[MISSION]: takeoff complete')

        asynchronous_mission(leader_scf, logconf, mission)
        for drone in hlcs:
            drone.land(0.0, 2.0)
        # hlcs[0].land(0.0, 2.0)
        time.sleep(10)
        for i in range(len(psws)):
            psws[i].reboot_to_fw()
            scfs[i].close_link()
        print("[MAIN]: MISSION COMPLETE\n")

    
    except KeyboardInterrupt:
        # print('\nYou should turn the drones back on to resume experiment.\n')
        # close logger
        triggerRestart()
        
