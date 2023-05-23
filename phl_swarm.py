import time, datetime, os

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
    [2.0, 1.0, 0.0],
    [1.0, 1.0, 0.0],
    [0.0, 1.0, 0.0],
]

moveDelta = [
    [+1.0, 0.0, 0.0],
    [+1.0, 0.0, 0.0],
    [0.0, +1.0, 0.0],
    [-1.0, 0.0, 0.0],
    [-1.0, 0.0, 0.0],
    [0.0, -1.0, 0.0],
]

missNo    = int(input('Mission type: \n - [0]Blink \n - [1]In-position \n - [2]Line \n - [6]Up-down\n >>'))

arguments = {
    drones[0] : [0, missNo],
    drones[1] : [1, missNo],
    drones[2] : [2, missNo],
    drones[3] : [3, missNo],
    drones[4] : [4, missNo],
}

# def log_data(timestamp, data, logFile):
#     dataAsList = list(map(str, [str(timestamp/1000), 
#                                 data['kalman.stateX'], data['kalman.stateY'], data['kalman.stateZ'], 
#                                 data['acc.x'], data['acc.y'], data['acc.z']
#                                 ]))
#     logFile.write(','.join(dataAsList)+"\n")

miss_type = ['NO', 'UD', 'LR', 'TR', 'SQ', 'CR', 'TO']
drone_ID = ['0A', '0B', '0C', '0D', '0E']


def mission(scf: SyncCrazyflie, posNo, code):
    # logFile = open('./swarm/'
    #                 +str(now)[5:10]+'/'
    #                 +str(now)[11:19]+'_'+drone_ID[posNo]+'_'+miss_type[code]+'.csv', 'w')
    try:
        # logFile = open('./swarm/'+str(now)[5:19]+'_mission'+str(missNo)+'_'+scf.cf.link_uri+'.csv', 'w')
        # logconf = LogConfig(name='Position', period_in_ms=10)
        # logconf.add_variable('kalman.stateX', 'float')
        # logconf.add_variable('kalman.stateY', 'float')
        # logconf.add_variable('kalman.stateZ', 'float')
        # logconf.add_variable('acc.x', 'float')
        # logconf.add_variable('acc.y', 'float')
        # logconf.add_variable('acc.z', 'float')
        # scf.cf.log.add_config(logconf)
        # logconf.data_received_cb.add_callback(log_data)

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

            else:
                time.sleep(6)
            print(f'[{scf.cf.link_uri}]: mission complete')
            phlc.land()
            print(f'[{scf.cf.link_uri}]: landing')
        # logconf.stop()
        # logFile.close()
    except KeyboardInterrupt:
        scf.cf.high_level_commander.stop()
        print('EMERGENCY STOP TRIGGERED')
        # logFile.close()

if __name__ == '__main__':
    now = datetime.datetime.now()
    cflib.crtp.init_drivers()
    factory = CachedCfFactory(rw_cache='./cache')

    with Swarm(drones, factory=factory) as swarm:
        print("Connected to Swarm CFs")
        """ swarm.reset_estimators()
        print('Estimators reset') """
        # logpath ='./swarm/'+str(now)[5:10]+'/' 
        # if not os.path.exists(logpath):
            # os.mkdir(logpath)
        swarm.parallel_safe(mission, args_dict=arguments)

