import seaborn as sns
from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np
import pandas as pd
import sys, os

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

print(df.describe())

lc = LineCollection(np.array(df['x']), cmap=plt.get_cmap('jet'))
lc.set_array(df['timestamp'])

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.add_collection(lc)
ax.set_xlabel('x')
ax.set_ylabel('y')
ax.set_zlabel('z')

plt.show()