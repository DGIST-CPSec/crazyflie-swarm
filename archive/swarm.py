import time

import cflib.crtp
from cflib.crazyflie.swarm import CachedCfFactory
from cflib.crazyflie.swarm import Swarm
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.position_hl_commander import PositionHlCommander


def activate_led_bit_mask(scf: SyncCrazyflie):
    scf.cf.param.set_value('led.bitmask', 255)


def deactivate_led_bit_mask(scf: SyncCrazyflie):
    scf.cf.param.set_value('led.bitmask', 0)


def light_check(scf: SyncCrazyflie):
    activate_led_bit_mask(scf)
    time.sleep(2)
    deactivate_led_bit_mask(scf)
    time.sleep(2)


def take_off(scf: SyncCrazyflie):
    phlc = PositionHlCommander(scf)
    phlc.takeoff(1.0, 1.0)
    time.sleep(3)

def land(scf: SyncCrazyflie):
    phlc = PositionHlCommander(scf)
    phlc.land(0.0, 1.0)
    time.sleep(2)
    # phlc.stop()


def run_square_sequence(scf: SyncCrazyflie):
    box_size = 1.0
    flight_time = 3.0

    phlc = PositionHlCommander(scf)

    phlc.go_to(box_size, 0)
    time.sleep(flight_time)

    phlc.go_to(0, box_size)
    time.sleep(flight_time)

    phlc.go_to(-box_size, 0)
    time.sleep(flight_time)

    phlc.go_to(0, -box_size)
    time.sleep(flight_time)


uris = [
    'radio://0/80/2M/E7E7E7E705',
    'radio://0/80/2M/E7E7E7E704',
    'radio://0/80/2M/E7E7E7E703',
    'radio://0/80/2M/E7E7E7E702',
    # Add more URIs if you want more copters in the swarm
]

# The layout of the positions (1m apart from each other):
#   <------ 1 m ----->
#   0                1
#          ^              ^
#          |Y             |
#          |              |
#          +------> X    1 m
#                         |
#                         |
#   3               2     .


h = 1.0  # remain constant height similar to take off height
x0, y0 = +0.5, +0.5
x1, y1 = -0.5, -0.5

#    x   y   z  time
sequence0 = [
    (x1, y0),
    (x0, y1),
    (x0,  0),
]

sequence1 = [
    (x0, y0),
    (x1, y1),
    ( 0, y1),
]

sequence2 = [
    (x0, y1),
    (x1, y0),
    (x1,  0),
]

sequence3 = [
    (x1, y1),
    (x0, y0),
    (.0, y0),
]

seq_args = {
    uris[0]: [sequence0],
    uris[1]: [sequence1],
    uris[2]: [sequence2],
    uris[3]: [sequence3],
}


def run_sequence(scf: SyncCrazyflie, sequence):
    cf = scf.cf
    phlc = PositionHlCommander(scf)
    phlc.set_default_height(1.0)
    phlc.set_default_velocity(0.5)
    phlc.set_landing_height(0.0)

    for arguments in sequence:
        x, y, z = arguments[0], arguments[1], arguments[2]
        duration = arguments[3]
        print('Setting position {} to cf {}'.format((x, y, z), cf.link_uri))
        phlc.go_to(x, y)
        time.sleep( 3.0)


if __name__ == '__main__':
    cflib.crtp.init_drivers()
    factory = CachedCfFactory(rw_cache='./cache')
    with Swarm(uris, factory=factory) as swarm:
        print('Connected to  Crazyflies')

        swarm.reset_estimators()
        print('Estimators have been reset')

        swarm.parallel_safe(take_off)
        # swarm.parallel_safe(run_square_sequence)
        swarm.parallel_safe(run_sequence, args_dict=seq_args)
        swarm.parallel_safe(land)