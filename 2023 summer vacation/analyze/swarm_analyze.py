import pandas as pd
import numpy as np
import sys, os
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

df = pd.read_csv('18_02_26_swarm.csv', names=['timestamp', 'uri', 'x', 'y', 'z'], header=None) #Change File

starts = df.groupby('uri').first()['timestamp']
df['timestamp'] = df['timestamp'] - df['uri'].map(starts)
df['uri'] = df['uri'].str[-2:]
df.dropna(inplace=True)
df = df.pivot(index='timestamp', columns='uri', values=['x', 'y', 'z'])
df = df.interpolate(method='linear')

fig2 = plt.figure()
plt.subplots_adjust(left=0, right=1, bottom=0, top=1)
ax = fig2.add_subplot(111, projection='3d')

for uri in df.columns.get_level_values(1):
    ax.plot(df[('x', uri)], df[('y', uri)], df[('z', uri)])

ax.set_xlabel('x')
ax.set_ylabel('y')
ax.set_zlabel('z')

ax.set_xlim([-4.0, 4.0])
ax.set_ylim([-4.0, 4.0])
ax.set_zlim([0, 3.0])

xrange = np.linspace(-2.6, 2.6, 10)
yrange = np.linspace(-2.6, 2.6, 10)
zrange = np.linspace(0.0, 2.0, 10)
XR, YR = np.meshgrid(xrange, yrange)
XS, ZS = np.meshgrid(xrange, zrange)
ZR = 0 * XR + 0 * YR + 0
floor = ax.plot_surface(XR, YR, ZR, alpha=0.1, color='b')
ceili = ax.plot_surface(XR, YR, ZR + 2, alpha=0.1, color='b')
wall1 = ax.plot_surface(XS, 0 * XS + 2.6, ZS, alpha=0.1, color='r')
wall2 = ax.plot_surface(XS, 0 * XS - 2.6, ZS, alpha=0.1, color='r')
wall3 = ax.plot_surface(0 * XS + 2.6, XS, ZS, alpha=0.1, color='g')
wall4 = ax.plot_surface(0 * XS - 2.6, XS, ZS, alpha=0.1, color='g')
Xb = [-5.2, 5.2]
Yb = [-5.2, 5.2]
Zb = [0, 3.0]
for xb, yb, zb in zip(Xb, Yb, Zb):
    ax.plot([xb], [yb], [zb], 'w')

plt.show()
