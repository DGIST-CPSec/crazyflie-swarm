# import log.csv file and analyze
# each row is a timestamp, x, y, z, roll, pitch, yaw

import pandas as pd
import numpy as np
import sys
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D



try:
    fName = sys.argv[1]
except:
    fName = input('log file name?: ')
df = pd.read_csv(fName, header=None, names=['timestamp', 'x', 'y', 'z', 'roll', 'pitch', 'yaw'])
df['timestamp'] = df['timestamp'] - df['timestamp'].iloc[0]

# summarize each rows
print(df.describe())

# plot x, y, z
fig, ax = plt.subplots(3, 2, figsize=(10, 10))
ax[0,0].plot(df['timestamp'], df['x'])
ax[0,0].set_title('x')
ax[1,0].plot(df['timestamp'], df['y'])
ax[1,0].set_title('y')
ax[2,0].plot(df['timestamp'], df['z'])
ax[2,0].set_title('z')
ax[0,1].plot(df['timestamp'], df['roll'])
ax[0,1].set_title('roll')
ax[1,1].plot(df['timestamp'], df['pitch'])
ax[1,1].set_title('pitch')
ax[2,1].plot(df['timestamp'], df['yaw'])
ax[2,1].set_title('yaw')

fig2 = plt.figure()
ax = fig2.add_subplot(111, projection='3d')
ax.plot(df['x'], df['y'], df['z'])
ax.set_xlabel('x')
ax.set_ylabel('y')
ax.set_zlabel('z')
plt.show()
