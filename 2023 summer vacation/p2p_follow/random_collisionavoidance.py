import time, datetime, os, logging, random
from math import sqrt

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper
from cflib.utils.power_switch import PowerSwitch
from cflib.positioning.position_hl_commander import PositionHlCommander

from cflib.crazyflie.swarm import Swarm, CachedCfFactory

drones = [
    'radio://0/80/2M/E7E7E7E701',
    'radio://0/80/2M/E7E7E7E704',
    'radio://0/80/2M/E7E7E7E70C',
    'radio://0/80/2M/E7E7E7E705',
    'radio://0/80/2M/E7E7E7E702',
]

psws = [
    PowerSwitch(drones[0]),
    PowerSwitch(drones[1]),
    PowerSwitch(drones[2]),
    PowerSwitch(drones[3]),
    PowerSwitch(drones[4]),
]

initialPos = [
    [0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0],
    [1.0, -1.0, 0.0],
    [0.0, -1.0, 0.0],
    [-1.0, -1.0, 0.0],
    [-1.0, 0.0, 0.0],
]

moveDelta = [
    [+1.0, 0.0, 0.0],
    [0.0, -1.0, 0.0],
    [-1.0, 0.0, 0.0],
    [-1.0, 0.0, 0.0],
    [0.0, +1.0, 0.0],
    [+1.0, 0.0, 0.0],
]

missNo = int(input('Mission type: \n - [0]Blink \n - [1]In-position \n - [2]Line \n - [6]Up-down\n >>'))

arguments = {
    drones[0] : [0, missNo],
    drones[1] : [1, missNo],
    drones[2] : [2, missNo],
    drones[3] : [3, missNo],
    drones[4] : [4, missNo],
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
	
def log_stab_callback(uri, timestamp, data, log_conf):
        x = float(data['kalman.stateX'])
        y = float(data['kalman.stateY'])
        z = float(data['kalman.stateZ'])
        logFile.write(str(timestamp)+','+str(uri)+','+str(x)+','+str(y)+','+str(z)+'\n')

def simple_log_async(scf):
    lg_vars = {
        'kalman.stateX': 'float',
        'kalman.stateY': 'float',
        'kalman.stateZ': 'float'
    }

    lg_stab = LogConfig(name='Position', period_in_ms=100)
    for key in lg_vars:
        lg_stab.add_variable(key, lg_vars[key])

    cf = scf.cf
    cf.log.add_config(lg_stab)
    lg_stab.data_received_cb.add_callback(lambda t, d, l: log_stab_callback(cf.link_uri, t, d, l))
    lg_stab.start()

def triggerRestart():
    for i in range(len(drones)):
        psws[i].reboot_to_fw()
        print('[MAIN]: EMERGENCY STOP TRIGGERED\n[' + str(hex(psws[i].address[4])) + ']: Restarting...')
        psws[i].close_link()

def random_position():
    pos = [-2, -1.5, -1, -0.5, 0, 0.5, 1, 1.5, 2]
    height = [0.5, 1, 1.5, 2]
    x = random.choice(pos)
    y = random.choice(pos)
    z = random.choice(height)
    return [x, y, z]

def coordinate_generator():
    pos = []
    for _ in range(5):
        pos.append(random_position())
    return pos

def calculate_distance(pos1, pos2):
    return sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2 + (pos1[2] - pos2[2])**2)

def mission(scf: SyncCrazyflie, posNo, code):
    takeoff_height = 1.0
    # logconf.start()
    if code == 0:
        time.sleep(3)
        print('[MISSION]: begin to blink')
        for i in range(20):
            scf.cf.param.set_value('led.bitmask', 255)
            time.sleep(0.5)
            scf.cf.param.set_value('led.bitmask', 0)
            time.sleep(0.5)
    else:
        phlc = PositionHlCommander(scf, 
                                x = initialPos[posNo][0], 
                                y = initialPos[posNo][1], 
                                z = initialPos[posNo][2]
                                )
        phlc.take_off(takeoff_height, 1.0)
        time.sleep(5)
        print(f'[{scf.cf.link_uri}]: takeoff complete')
        phlc.set_default_height(takeoff_height)
        phlc.set_default_velocity(0.5)
        phlc.set_landing_height(0.0)

        if code == 1:
            phlc.up(0.5)
            time.sleep(3)
            phlc.down(0.5)
            time.sleep(3)

        elif code == 2:
            phlc.forward(1)
            time.sleep(4)
            phlc.back(1)
            time.sleep(4)

        elif code == 3:
            position = posNo
            phlc.move_distance(
                moveDelta[position][0], 
                moveDelta[position][1], 
                moveDelta[position][2])
            time.sleep(1.5)
            phlc.move_distance(
                -moveDelta[position][0], 
                -moveDelta[position][1], 
                -moveDelta[position][2])
            time.sleep(1.5)

        elif code == 4:
            # 코드 검증이 필요함
            position = posNo
            for i in range(6):
                phlc.move_distance(
                    moveDelta[position][0], 
                    moveDelta[position][1], 
                    moveDelta[position][2])
                time.sleep(1)
                position = (position+1)%6

        elif code == 5:
            phlc = PositionHlCommander(scf)
            phlc.take_off(takeoff_height, 1.0)
            time.sleep(5)
            print(f'[{scf.cf.link_uri}]: takeoff complete')
            phlc.set_default_height(takeoff_height)
            phlc.set_default_velocity(0.5)
            phlc.set_landing_height(0.0)

        for _ in range(6):
            pos_list = random_position()
            print(f'[{scf.cf.link_uri}]: Moving to random position:', pos_list)
            for other_scf in swarm:
                if other_scf != scf:
                    other_position = other_scf.position_hl[0]
                    distance = calculate_distance(pos_list, other_position)
                    if distance < 0.1:  # 10 cm (0.1 meter) minimum distance
                        print(f'[{scf.cf.link_uri}]: Too close to other drone, adjusting position')
                        pos_list = random_position()
                        break

            phlc.go_to(pos_list[0], pos_list[1], pos_list[2])
            time.sleep(5)

        else:
            time.sleep(6)
        print(f'[{scf.cf.link_uri}]: mission complete')
        phlc.land()
        print(f'[{scf.cf.link_uri}]: landing')
    

if __name__ == '__main__':
    now = datetime.datetime.now()
    cflib.crtp.init_drivers(enable_debug_driver=False) # initialize drivers
    factory = CachedCfFactory(rw_cache='./cache')

    logpath ='./log/'+str(now)[5:10]+'/' 
    if not os.path.exists(logpath):
        os.mkdir(logpath)

    logFile = open('./log/'
                   +str(now)[5:10]+'/'
                   +str(now)[11:19]+'_swarm'+'.csv', 'w')

    with Swarm(drones, factory=factory) as swarm:
        print("Connected to Swarm CFs")
        swarm.parallel_safe(simple_log_async)

        try :
            swarm.parallel(mission, args_dict=arguments)
        except KeyboardInterrupt:
            logger.error('KeyboardInterrupt detected, triggering restart.')
            triggerRestart()
