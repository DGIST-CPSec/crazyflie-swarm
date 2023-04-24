import logging
import time

import cflib.crtp
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander

URI = 'radio://0/80/2M/E7E7E7E701'

logging.basicConfig(level=logging.ERROR)


if __name__ == '__main__':
    cflib.crtp.init_drivers(enable_debug_driver=False)

    with SyncCrazyflie(URI) as scf:
        with MotionCommander(scf, default_height=0.2) as mc:
            print('Taking off!')
            time.sleep(2)
            for i in range(1):

                mc.turn_right(90)
                time.sleep(1)
                mc.turn_left(90)
                time.sleep(1)
                mc.up(0.2)
                time.sleep(1)
                mc.forward(0.5)
                time.sleep(1)
                mc.back(0.5)
                time.sleep(3)
                mc.down(0.4)
                time.sleep(1)
