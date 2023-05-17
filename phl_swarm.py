import time, datetime

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
initialPos = [
    [0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0],
    [2.0, 0.0, 0.0],
    [0.0, 1.0, 0.0],
    [1.0, 1.0, 0.0],
]

missNo    = int(input('Mission type: \n[0]Blink \t[1]In-position \t[2]Line \t[6]Up-down\n >>'))

arguments = {
    drones[0] : [initialPos[0], missNo],
    drones[1] : [initialPos[1], missNo],
    drones[2] : [initialPos[2], missNo],
    drones[3] : [initialPos[3], missNo],
    drones[4] : [initialPos[4], missNo],
}

""" def log_data(timestamp, data, logconf):
    dataAsList = list(map(str, [str(timestamp/1000), 
                                data['kalman.stateX'], data['kalman.stateY'], data['kalman.stateZ'], 
                                data['acc.x'], data['acc.y'], data['acc.z']
                                ]))
    logFile.write(','.join(dataAsList)+"\n") """

def mission(scf: SyncCrazyflie, initPos, code):
    """ logFile = open('./swarm/'+str(now)[5:19]+'_mission'+str(missNo)+'_'+scf.cf.link_uri+'.csv', 'w')
    logconf = LogConfig(name='Position', period_in_ms=10)
    logconf.add_variable('kalman.stateX', 'float')
    logconf.add_variable('kalman.stateY', 'float')
    logconf.add_variable('kalman.stateZ', 'float')
    logconf.add_variable('acc.x', 'float')
    logconf.add_variable('acc.y', 'float')
    logconf.add_variable('acc.z', 'float')
    scf.cf.log.add_config(logconf)
    logconf.data_received_cb.add_callback(log_data) """

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
        phlc = PositionHlCommander(scf, x = initPos[0], y = initPos[1], z = initPos[2])
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
        else:
            time.sleep(6)
        print(f'[{scf.cf.link_uri}]: mission complete')
        phlc.land()
        print(f'[{scf.cf.link_uri}]: landing')
    pass

if __name__ == '__main__':
    now = datetime.datetime.now()
    cflib.crtp.init_drivers()
    factory = CachedCfFactory(rw_cache='./cache')

    with Swarm(drones, factory=factory) as swarm:
        print("Connected to Swarm CFs")
        swarm.reset_estimators()
        print('Estimators reset')
        swarm.parallel_safe(mission, args_dict=arguments)

