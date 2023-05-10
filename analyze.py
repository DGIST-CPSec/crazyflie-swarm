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
ax[0,0].set_ylim([-2.6, 2.6])
ax[0,0].set_title('x')
ax[1,0].plot(df['timestamp'], df['y'])
ax[1,0].set_ylim([-2.6, 2.6])
ax[1,0].set_title('y')
ax[2,0].plot(df['timestamp'], df['z'])
ax[2,0].set_ylim([0, 2.5])
ax[2,0].set_title('z')
ax[0,1].plot(df['timestamp'], df['accX'])
ax[0,1].set_title('accX')
ax[1,1].plot(df['timestamp'], df['accY'])
ax[1,1].set_title('accY')
ax[2,1].plot(df['timestamp'], df['accZ'])
ax[2,1].set_title('accZ')

fig2 = plt.figure(figsize=(20,20))
ax = fig2.add_subplot(111, projection='3d')
ax.plot(df['x'], df['y'], df['z'], c='k')
ax.set_xlabel('x')
ax.set_ylabel('y')
ax.set_zlabel('z')

# AREA: set viewer's limit
ax.set_xlim([-4.0, 4.0])
ax.set_ylim([-4.0, 4.0])
ax.set_zlim([0, 3.0])

# AREA: Bounding box of expriment area
xrange = np.linspace(-2.6, 2.6, 10)
yrange = np.linspace(-2.6, 2.6, 10)
zrange = np.linspace( 0.0, 2.0, 10)
XR, YR = np.meshgrid(xrange, yrange)
XS, ZS = np.meshgrid(xrange, zrange)
ZR = 0*XR + 0*YR + 0
floor = ax.plot_surface(XR,       YR, ZR,   alpha=0.1, color='b')
ceili = ax.plot_surface(XR,       YR, ZR+2, alpha=0.1, color='b')
wall1 = ax.plot_surface(XS, 0*XS+2.6, ZS,   alpha=0.1, color='r')
wall2 = ax.plot_surface(XS, 0*XS-2.6, ZS,   alpha=0.1, color='r')
wall3 = ax.plot_surface(0*XS+2.6, XS, ZS,   alpha=0.1, color='g')
wall4 = ax.plot_surface(0*XS-2.6, XS, ZS,   alpha=0.1, color='g')
Xb = [-5.2, 5.2]
Yb = [-5.2, 5.2]
Zb = [0, 3.0]
for xb, yb, zb in zip(Xb, Yb, Zb):
   ax.plot([xb], [yb], [zb], 'w')

timestamp_length = len(df['timestamp'])
for i in range(1, len(df['x']), 10):
    ax.scatter(df['x'][i], df['y'][i], df['z'][i], color=plt.cm.hsv((i/timestamp_length)), marker='o')

# plot x-y, y-z, x-z
fig3, ax3 = plt.subplots(2, 2, figsize=(10, 10))
ax3[0,0].plot(df['x'], df['y'])
ax3[0,0].set_title('x-y')
ax3[1,0].plot(df['y'], df['z'])
ax3[1,0].set_title('y-z')
ax3[0,1].plot(df['x'], df['z'])
ax3[0,1].set_title('x-z')
ax3[0,0].set_xlim([-2.6, 2.6])
ax3[0,0].set_ylim([-2.6, 2.6])
ax3[1,0].set_xlim([-2.6, 2.6])
ax3[1,0].set_ylim([0, 2.5])
ax3[0,1].set_xlim([-2.6, 2.6])
ax3[0,1].set_ylim([0, 2.5])

plt.show()
