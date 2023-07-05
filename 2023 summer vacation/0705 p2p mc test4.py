import time
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.utils import uri_helper
from cflib.positioning.motion_commander import MotionCommander

leader_uri = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E701')
follower_uri = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E705')

def takeoff(cf):
    with MotionCommander(cf) as mc:
        mc.take_off(0.5)
        time.sleep(3)

def land(cf):
    with MotionCommander(cf) as mc:
        mc.land(0.0)
        time.sleep(3)

def follow_leader(follower_cf, leader_position):
    with MotionCommander(follower_cf) as mc:
        mc.go_to(
            leader_position[0],
            leader_position[1],
            leader_position[2],
            0.5
        )
        time.sleep(0.1)

def move_leader(cf, duration):
    with MotionCommander(cf) as mc:
        mc.forward(0.2)
        time.sleep(duration)

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

        move_duration = 5
        move_leader(leader_cf, move_duration)

        leader_position = leader_cf.state
        follow_duration = 10
        start_time = time.time()

        while time.time() - start_time < follow_duration:
            follow_leader(follower_cf, leader_position)
            time.sleep(0.1)

        land(leader_cf)
        land(follower_cf)

    finally:
        leader_cf.close_link()
        follower_cf.close_link()

if __name__ == '__main__':
    main()
