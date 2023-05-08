# import log.csv file and analyze
# each row is a timestamp, x, y, z, roll, pitch, yaw

import pandas as pd
import numpy as np
import sys, os
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D



try:
    fName = sys.argv[1]
except:
    logFiles = os.listdir('./log')
    logFiles.sort(reverse=True)
    for i, logName in enumerate(logFiles):
        print(i,":", logName)
    fName = logFiles[int(input('log file number?: '))]

df = pd.read_csv('./log/'+fName, header=None, names=['timestamp', 'x', 'y', 'z', 'accX', 'accY', 'accZ'])
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
ax[0,1].plot(df['timestamp'], df['accX'])
ax[0,1].set_title('accX')
ax[1,1].plot(df['timestamp'], df['accY'])
ax[1,1].set_title('accY')
ax[2,1].plot(df['timestamp'], df['accZ'])
ax[2,1].set_title('accZ')


fig2 = plt.figure()

max_range = np.array([df['x'].max() - df['x'].min(), df['y'].max() - df['y'].min(), df['z'].max() - df['z'].min()]).max()
Xb = 0.5*max_range*np.mgrid[-1:2:2,-1:2:2,-1:2:2][0].flatten() + 0.5*(df['x'].max()+df['x'].min())
Yb = 0.5*max_range*np.mgrid[-1:2:2,-1:2:2,-1:2:2][1].flatten() + 0.5*(df['y'].max()+df['y'].min())
Zb = 0.5*max_range*np.mgrid[-1:2:2,-1:2:2,-1:2:2][2].flatten() + 0.5*(df['z'].max()+df['z'].min())

ax = fig2.add_subplot(111, projection='3d')
ax.plot(df['x'], df['y'], df['z'])
ax.set_xlabel('x')
ax.set_ylabel('y')
ax.set_zlabel('z')
# ax.plot([-2.6, -2.6, 2.6, 2.6, -2.6, -2.6, 2.6, 2.6], [-2.6, 2.6, 2.6, -2.6, -2.6, 2.6, 2.6, -2.6], [0, 0, 0, 0, 2.0, 2.0, 2.0, 2.0])
# Comment or uncomment following both lines to test the fake bounding box:
for xb, yb, zb in zip(Xb, Yb, Zb):
   ax.plot([xb], [yb], [zb], 'w')


# plot x-y, y-z, x-z
fig3, ax3 = plt.subplots(2, 2, figsize=(10, 10))
ax3[0,0].plot(df['x'], df['y'])
ax3[0,0].set_title('x-y')
ax3[1,0].plot(df['y'], df['z'])
ax3[1,0].set_title('y-z')
ax3[0,1].plot(df['x'], df['z'])
ax3[0,1].set_title('x-z')

plt.show()
