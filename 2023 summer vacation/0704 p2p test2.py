import time
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.utils import uri_helper

leader_uri = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E705')
follower_uri = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E701')

def takeoff(cf):
    cf.commander.send_hover_setpoint(0, 0, 0, 0.5)
    time.sleep(3)

def land(cf):
    cf.commander.send_hover_setpoint(0, 0, 0, 0)
    time.sleep(3)

def follow_leader(follower_cf, leader_cf):
    leader_position = leader_cf.state.kalman
    follower_cf.commander.send_hover_setpoint(
        leader_position[0],
        leader_position[1],
        leader_position[2],
        0.5
    )

def move_leader(cf, duration):
    start_time = time.time()

    while time.time() - start_time < duration:
        cf.commander.send_hover_setpoint(0.2, 0, 0, 0.5)
        time.sleep(0.1)

    cf.commander.send_hover_setpoint(0, 0, 0, 0)

def main():
    cflib.crtp.init_drivers()

    leader_cf = Crazyflie(rw_cache='./cache')
    follower_cf = Crazyflie(rw_cache='./cache')

    try:
        leader_cf.open_link(leader_uri)
        follower_cf.open_link(follower_uri)

        leader_cf.param.set_value('kalman.initialX', 0.0)
        leader_cf.param.set_value('kalman.initialY', 0.0)
        leader_cf.param.set_value('kalman.initialZ', 0.0)

        follower_cf.param.set_value('kalman.initialX', 0.0)
        follower_cf.param.set_value('kalman.initialY', -1.0)
        follower_cf.param.set_value('kalman.initialZ', 0.0)

        takeoff(leader_cf)
        takeoff(follower_cf)

        move_duration = 10
        move_leader(leader_cf, move_duration)

        follow_duration = 10
        start_time = time.time()

        while time.time() - start_time < follow_duration:
            follow_leader(follower_cf, leader_cf)
            time.sleep(0.1)

        land(leader_cf)
        land(follower_cf)

    finally:
        leader_cf.close_link()
        follower_cf.close_link()

if __name__ == '__main__':
    main()
