import time, datetime, os, random, logging, math

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
    'radio://0/80/2M/E7E7E7E70A',
    'radio://0/80/2M/E7E7E7E70B',
    'radio://0/80/2M/E7E7E7E70C',
    'radio://0/80/2M/E7E7E7E70D',
    'radio://0/80/2M/E7E7E7E70E',
]

psws = [
    PowerSwitch(drones[0]),
    PowerSwitch(drones[1]),
    PowerSwitch(drones[2]),
    PowerSwitch(drones[3]),
    PowerSwitch(drones[4]),
]

arguments = {
    drones[0] : [0],
    drones[1] : [1],
    drones[2] : [2],
    drones[3] : [3],
    drones[4] : [4],
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
        scfs[i].close_link()

def random_position():
    pos = [-2,-1.5, -1, -0.5, 0, 0.5, 1, 1.5, 2]
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

def calculate_distance(p1, p2):
    diff = [0, 0, 0]
    diff[0] = p1[0] - p2[0]
    diff[1] = p1[1] - p2[1]
    diff[2] = p1[2] - p2[2]
    return math.sqrt((diff[0] * diff[0]) + (diff[1] * diff[1]) + (diff[2] * diff[2]))

def find_closest_target(start_position, targets_position):
    min_distance = None
    closest_index = 0
    for index, target in enumerate(targets_position):
        dist = calculate_distance(start_position, target)
        if min_distance is None or dist < min_distance:
            min_distance = dist
            closest_index = index
    
    return targets_position[closest_index]

def mission(scf: SyncCrazyflie, posNo):
    takeoff_height = 1.0
    coordinate = coordinate_generator()  # Generate individual coordinate list for each drone
    phlc = PositionHlCommander(scf, 
                               x=coordinate[posNo][0], 
                               y=coordinate[posNo][1], 
                               z=0)
    phlc.take_off(takeoff_height, 1.0)
    time.sleep(5)
    print(f'[{scf.cf.link_uri}]: takeoff complete')
    phlc.set_default_velocity(0.5)
    phlc.set_landing_height(0.0)
    for i in range(5):
        coordinate = coordinate_generator()  # Generate new coordinates for each waypoint
        phlc.go_to(coordinate[posNo][0], coordinate[posNo][1], coordinate[posNo][2])
        time.sleep(5)
    phlc.land()




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
