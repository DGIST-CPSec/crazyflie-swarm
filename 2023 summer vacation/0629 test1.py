import cflib.crtp
import logging
import time

from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.high_level_commander import HighLevelCommander
from cflib.utils.power_switch import PowerSwitch
from cflib.crazyflie.syncLogger import SyncLogger

drones = [
    'radio://0/80/2M/E7E7E7E70A',
    'radio://0/80/2M/E7E7E7E70D',
    'radio://0/80/2M/E7E7E7E70C',
]

psws = [PowerSwitch(uri) for uri in drones]

leader = [0.0, 1.0, 0.0]

distance = [
    # 01
    [ 0.0,  0.0,  0.0],
    # 02                03
    [-0.5, -0.5,  0.0], [ 0.5, -0.5,  0.0],
]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def order_follow(timestamp, data, logconf):
    leader = [data['kalman.stateX'], data['kalman.stateY'], data['kalman.stateZ']]
    logger.info(f'{timestamp} : {data}')
    print(timestamp, ":", data)
    for i in range(len(drones)):
        retpos = []
        retpos.append(leader[0] + distance[i][0])
        retpos.append(leader[1] + distance[i][1])
        retpos.append(max(0, leader[2] + distance[i][2]))
        hlcs[i].go_to(retpos[0], retpos[1], retpos[2], 0, 0.1, relative=False)
        print("drone", i, "go to", retpos)
    time.sleep(0.1)


def leader_mission(scf, code):
    lhlc = scf.cf.high_level_commander
    logger.info("In leader mission with code: %s", code)

    if code == 1:  # takeoff->up->down->land
        logger.info("Executing mission code 1")
        lhlc.go_to(0, 0, 0.3, 0, 3, relative=True)
        logger.info("Issued go_to command for takeoff")
        time.sleep(3)
        lhlc.go_to(0, 0, -0.3, 0, 3, relative=True)
        logger.info("Issued go_to command for landing")
        time.sleep(3)

    elif code == 2:  # forward-backward round trip
        logger.info("Executing mission code 2")
        lhlc.go_to(0.5, 0.0, 0.0, 0, 3, relative=True)
        logger.info("Issued go_to command for takeoff")
        time.sleep(3)
        lhlc.go_to(-0.5, 0.0, 0.0, 0, 3, relative=True)
        logger.info("Issued go_to command for landing")
        time.sleep(3)

    elif code == 3:  # left-right round trip
        lhlc.go_to(0.0, 0.5, 0.0, 0, 3, relative=True)
        time.sleep(3)
        lhlc.go_to(0.0, -0.5, 0.0, 0, 3, relative=True)
        time.sleep(3)

    elif code == 4:  # square round trip
        lhlc.go_to(0.4, 0.4, 0, 0, 3, relative=True)
        time.sleep(3)
        lhlc.go_to(0.4, -0.4, 0, 0, 3, relative=True)
        time.sleep(3)
        lhlc.go_to(-0.4, -0.4, 0, 0, 3, relative=True)
        time.sleep(3)
        lhlc.go_to(-0.4, 0.4, 0, 0, 3, relative=True)
        time.sleep(3)
        lhlc.go_to(0.0, 0.0, 0, 0, 3, relative=True)
        time.sleep(3)
    else:
        # lhlc.go_to(0,0,0,0,3, relative=True) # hold
        time.sleep(3)

    lhlc.stop()  # 이동 중지 명령 추가
    print('[LEADER]: mission command complete')

def synchronous_mission(scf, logconf):
    with SyncLogger(scf, logconf) as logger:
        for log_entry in logger:
            timestamp = log_entry[0]
            data = log_entry[1]
            # print(timestamp, ":", data['kalman.stateX'], data['kalman.stateY'], data['kalman.stateZ'])
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
    except KeyboardInterrupt:
        triggerRestart()
    finally:
        logconf.stop()
        print('logconf stop')

def triggerRestart():
    for i in range(len(drones)):
        psws[i].reboot_to_fw()
        print('[MAIN]: EMERGENCY STOP TRIGGERED\n[' + str(hex(psws[i].address[4])) + ']: Restarting...')
        scfs[i].close_link()

if __name__ == '__main__':
    try:
        cflib.crtp.init_drivers()
        logger.info("Drivers initialized")

        scfs = [SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) for uri in drones]
        hlcs = [scf.cf.high_level_commander for scf in scfs]

        for i in range(len(scfs)):
            scfs[i].open_link()
            logger.info("[SWARM] opened link: %s", scfs[i].cf.link_uri)
            print("[SWARM] opened link: ", scfs[i].cf.link_uri)

        mission = int(input('Enter mission code: [1] up-down, [2] forward-backward, [3] left-right, [4] square, [0] hold: \n>>> '))
        logconf = LogConfig(name='Position', period_in_ms=100)
        logconf.add_variable('kalman.stateX', 'float')
        logconf.add_variable('kalman.stateY', 'float')
        logconf.add_variable('kalman.stateZ', 'float')
        logconf.add_variable('pm.vbat', 'float') 
        leader_scf = scfs[0]

        print('[MAIN]: starting mission')
        for drone in hlcs:
            drone.takeoff(0.5, 3.0)
        logger.info("All drones issued takeoff command")
        time.sleep(5)
        print('[MISSION]: takeoff complete')

        asynchronous_mission(leader_scf, logconf, mission)
        land_drones()

        for drone in hlcs:
            drone.land(0.0, 2.0)
        logger.info("All drones issued land command")
        time.sleep(10)
        for scf in scfs:
            commander = scf.cf.commander
            commander.send_stop_setpoint()
        logger.info("All drones issued stop command")

        for i in range(len(psws)):
            psws[i].reboot_to_fw()
            scfs[i].close_link()
        logger.info("[MAIN]: MISSION COMPLETE\n")
        print("[MAIN]: MISSION COMPLETE\n")

    except KeyboardInterrupt:
        logger.error('KeyboardInterrupt detected, triggering restart.')
        triggerRestart()
