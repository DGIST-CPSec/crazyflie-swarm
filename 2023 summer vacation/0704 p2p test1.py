import time
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.utils import uri_helper

# 드론 URI 정의
leader_uri = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E70A')
follower_uri = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E70B')

def takeoff(cf):
    cf.commander.send_hover_setpoint(0, 0, 0, 0.5)  # 드론을 이륙시키는 명령
    time.sleep(3)

def land(cf):
    cf.commander.send_hover_setpoint(0, 0, 0, 0)  # 드론을 착륙시키는 명령
    time.sleep(3)

def follow_leader(follower_cf, leader_cf):
    # 리더 드론의 위치 정보를 받아와서 팔로워 드론을 제어하는 로직 구현
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
        # 리더 드론을 전진하도록 명령
        cf.commander.send_hover_setpoint(0.2, 0, 0, 0.5)  # x축 방향으로 0.2m/s로 전진
        time.sleep(0.1)

    # 움직임이 끝나면 호버링 상태로 유지
    cf.commander.send_hover_setpoint(0, 0, 0, 0)

def main():
    cflib.crtp.init_drivers()  # 드라이버 초기화

    with Crazyflie(rw_cache='./cache') as leader_cf, Crazyflie(rw_cache='./cache') as follower_cf:
        leader_cf.open_link(leader_uri)  # 리더 드론에 연결
        follower_cf.open_link(follower_uri)  # 팔로워 드론에 연결
        leader_cf.param.set_value('kalman.initialX', 0.0)
        leader_cf.param.set_value('kalman.initialY', 0.0)
        leader_cf.param.set_value('kalman.initialZ', 0.0)

        follower_cf.param.set_value('kalman.initialX', 0.0)
        follower_cf.param.set_value('kalman.initialY', -1.0)
        follower_cf.param.set_value('kalman.initialZ', 0.0)
        takeoff(leader_cf)  # 리더 드론 이륙
        takeoff(follower_cf)  # 팔로워 드론 이륙

        # 리더 드론을 전진시키기
        move_duration = 10  # 10초 동안 전진하도록 설정
        move_leader(leader_cf, move_duration)

        # 일정 시간 동안 리더 드론을 따라가기
        follow_duration = 10  # 10초 동안 리더 드론을 따라가도록 설정
        start_time = time.time()

        while time.time() - start_time < follow_duration:
            follow_leader(follower_cf, leader_cf)
            time.sleep(0.1)

        land(leader_cf)  # 리더 드론 착륙
        land(follower_cf)  # 팔로워 드론 착륙

if __name__ == '__main__':
    main()
