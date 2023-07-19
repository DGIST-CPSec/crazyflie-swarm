import time
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie

# Light House Positioning 사용
from cflib.drivers import lighthouse

# 첫 번째 드론의 URI
uri_cf1 = 'radio://0/80/2M/E7E7E7E70A?rate_limit=100'

# 두 번째 드론의 URI
uri_cf2 = 'radio://0/80/2M/E7E7E7E701?rate_limit=100'

# Crazyflie 라이브러리 초기화
cflib.crtp.init_drivers(enable_debug_driver=False)

# 첫 번째 드론 제어 함수
def follow_drone():
    with SyncCrazyflie(uri_cf1) as scf1, SyncCrazyflie(uri_cf2) as scf2:
        cf1 = scf1.cf
        cf2 = scf2.cf
        
        # Light House Positioning 활성화
        lh.connect(scf1)
        lh.connect(scf2)
        
        # P2P 통신을 위해 주기적으로 두 번째 드론의 위치를 가져오기 위한 콜백 함수
        def position_callback(cf2, name, pos):
            # CF1의 위치를 가져와서 CF2의 위치로 이동 (높이는 1로 고정)
            cf1._simple_goto((pos[0], pos[1], 1))
            
        # 두 번째 드론의 위치를 주기적으로 감지하도록 콜백 설정
        cf2.position_estimator.add_callback(position_callback)
        
        # 두 번째 드론의 위치를 주기적으로 업데이트하도록 설정 (10ms 주기)
        cf2.position_estimator.start()
        
        # 첫 번째 드론 제어
        with MotionCommander(cf1) as mc1:
            # Light House Positioning 시작 (1초마다 드론들의 위치 업데이트)
            lh.start_positioning(1)
            
            # 두 번째 드론이 반복적으로 x와 y좌표를 (0, 0), (1, 0), (1, 1), (0, 1)으로 움직이도록 설정
            # 두 번째 드론의 움직임을 통해 첫 번째 드론이 따라다닙니다.
            for _ in range(4):
                # 두 번째 드론 이동
                cf2._simple_goto((0, 0, 1))  # (0, 0, 1)
                time.sleep(5)
                
                cf2._simple_goto((1, 0, 1))  # (1, 0, 1)
                time.sleep(5)
                
                cf2._simple_goto((1, 1, 1))  # (1, 1, 1)
                time.sleep(5)
                
                cf2._simple_goto((0, 1, 1))  # (0, 1, 1)
                time.sleep(5)
            
            # 통신 종료
            cf2.position_estimator.remove_callback(position_callback)
            cf2.position_estimator.stop()

# Main 함수
if __name__ == '__main__':
    try:
        follow_drone()
    except KeyboardInterrupt:
        pass
