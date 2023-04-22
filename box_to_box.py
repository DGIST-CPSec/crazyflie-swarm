#box_size_swarm

import time

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander

from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncLogger import SyncLogger

from cflib.crazyflie.swarm import CachedCfFactory
from cflib.crazyflie.swarm import Swarm


def activate_mellinger_controller(scf, use_mellinger):
    controller = 1
    if use_mellinger:
        controller = 2
    scf.cf.param.set_value('stabilizer.controller', controller)

def log_stab_callback(timestamp, data, logconf):
    print('[%d][%s]: %s' % (timestamp, logconf.name, data))

def simple_log_async(scf, logconf):
    cf = scf.cf
    cf.log.add_config(logconf)
    logconf.data_received_cb.add_callback(log_stab_callback)
    logconf.start()
    time.sleep(10)
    logconf.stop()

log_pos = LogConfig(name='Position', period_in_ms=10)
log_pos.add_variable('kalman.stateX', 'float')
log_pos.add_variable('kalman.stateY', 'float')
log_pos.add_variable('kalman.stateZ', 'float')
log_pos.add_variable('stabilizer.roll', 'float')
log_pos.add_variable('stabilizer.pitch', 'float')
log_pos.add_variable('stabilizer.yaw', 'float')

def run_shared_sequence(scf):
    activate_mellinger_controller(scf, False)

    box_size = 0.5
    flight_time = 2

    commander = scf.cf.high_level_commander

    commander.takeoff(1.0, 5.0)
    simple_log_async(scf, log_pos)

    # commander.go_to(box_size, 0, 0, 0, flight_time, relative=True)
    # time.sleep(flight_time)

    # commander.go_to(0, box_size, 0, 0, flight_time, relative=True)
    # time.sleep(flight_time)

    # commander.go_to(-box_size, 0, 0, 0, flight_time, relative=True)
    # time.sleep(flight_time)

    # commander.go_to(0, -box_size, 0, 0, flight_time, relative=True)
    # time.sleep(flight_time)

    commander.land(0.0, 5.0)
    time.sleep(5)

    commander.stop()


uris = {
    # 'radio://0/80/2M/E7E7E7E701',
    # 'radio://0/80/2M/E7E7E7E702',
    'radio://0/80/2M/E7E7E7E703',
    # 'radio://0/80/2M/E7E7E7E704',
    # 'radio://0/80/2M/E7E7E7E705',
    # Add more URIs if you want more copters in the swarm
}

if __name__ == '__main__':
    cflib.crtp.init_drivers()
    factory = CachedCfFactory(rw_cache='./cache')
    with Swarm(uris, factory=factory) as swarm:
        swarm.reset_estimators()
        swarm.parallel_safe(run_shared_sequence)