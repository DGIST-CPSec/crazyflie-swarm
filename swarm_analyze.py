
import pandas as pd
import numpy as np
import sys, os
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

try:
    fName = sys.argv[1]
except:
    date = input('date? (e.g. 05-23): ')
    logFiles = os.listdir('./log/'+date)
    logFiles.sort(reverse=True)
    for i, logName in enumerate(logFiles):
        print(i,":", logName)
    fName = logFiles[int(input('log file number?: '))]

df = pd.read_csv('./log/'+date+'/'+fName, header=None, 
                    names=['timestamp', 
                            'x1', 'y1', 'z1', 
                            'x2', 'y2', 'z2', 
                            'x3', 'y3', 'z3', 
                            'x4', 'y4', 'z4', 
                            'x5', 'y5', 'z5', ])
df['timestamp'] = df['timestamp'] - df['timestamp'].iloc[0]
df['x2'] = df['x1']+0.1
df['y2'] = df['y1']+0.1
df['z2'] = df['z1']+0.1
df['x3'] = df['x1']+0.3
df['y3'] = df['y1']+0.3
df['z3'] = df['z1']+0.3
df['x4'] = df['x1']-0.3
df['y4'] = df['y1']-0.3
df['z4'] = df['z1']-0.3
df['x5'] = df['y1']
df['y5'] = df['z1']
df['z5'] = df['x1']


# AREA: Bounding box of expriment area
fig2 = plt.figure()
plt.subplots_adjust(left=0, right=1, bottom=0, top=1)
ax = fig2.add_subplot(111, projection='3d')
ax.plot(df['x1'], df['y1'], df['z1'], c='r')
ax.plot(df['x2'], df['y2'], df['z2'], c='g')
ax.plot(df['x3'], df['y3'], df['z3'], c='b')
ax.plot(df['x4'], df['y4'], df['z4'], c='c')
ax.plot(df['x5'], df['y5'], df['z5'], c='m')

ax.set_xlabel('x')
ax.set_ylabel('y')
ax.set_zlabel('z')

# AREA: set viewer's limit
ax.set_xlim([-4.0, 4.0])
ax.set_ylim([-4.0, 4.0])
ax.set_zlim([0, 3.0])

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

plt.show()