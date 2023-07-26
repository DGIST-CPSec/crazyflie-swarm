import time, datetime, os, random

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

def random_position():
    pos = [-2,-1.5, -1, -0.5, 0, 0.5, 1, 1.5, 2]
    height = [0.5, 1, 1.5, 2]
    x = random.choice(pos)
    y = random.choice(pos)
    z = random.choice(height)
    return [x, y, z]    

def mission(scf: SyncCrazyflie):
    coordinate = random_position()
    phlc = PositionHlCommander(scf, 
                                x = coordinate[0], 
                                y = coordinate[1], 
                                z = 0
                                )
    phlc.take_off
