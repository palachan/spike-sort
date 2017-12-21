# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 10:40:00 2017

@author: Jeffrey_Taube
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D,proj3d

from matplotlib.widgets import LassoSelector
from matplotlib import path

fig=plt.figure()

a=np.random.normal(size=10000)
b=np.random.normal(size=10000)
c=np.random.normal(size=10000)
colors = np.zeros(10000)

ax1 = fig.add_subplot(121,projection='3d')
ax1.set_title('3d')
ax1.scatter(a,b,c,c=colors,picker=5)
#ax1.set_xlim([-1,1])
#ax1.set_ylim([-1,1])
ax1.set_aspect('equal')

# Empty array to be filled with lasso selector
ax2 = fig.add_subplot(122)
ax2.set_title('2d')
x2, y2, _ = proj3d.proj_transform(a, b, c, ax1.get_proj())
print x2, y2 
ax2.cla()
ax2.scatter(x2,y2,c=colors)
ax2.set_aspect('equal')
# Pixel coordinates
#pix = np.arange(10)
#xv, yv, zv = np.meshgrid(a, b, c)
pix = np.vstack((x2, y2)).T


def updateArray(colors, indices):
    colors[indices] = 1
    return colors

def onselect(verts):
    global colors, pix,x2,y2
    p = path.Path(verts)
    ind = p.contains_points(pix, radius=0)
    fig.canvas.draw_idle()
    colors=updateArray(colors,ind)
    ax2.cla()
    ax2.scatter(x2,y2,c=colors)
    ax1.cla()
    ax1.scatter(a,b,c,c=colors,picker=5)
    fig.canvas.draw_idle()

def onpick(event):
    global pix,x2,y2
    ind = event.ind
    x2, y2, _ = proj3d.proj_transform(a, b, c, ax1.get_proj())
    ax2.cla()
    ax2.scatter(x2,y2,c=colors)
    pix = np.vstack((x2,y2)).T

fig.canvas.mpl_connect('pick_event', onpick)

lasso = LassoSelector(ax2, onselect)

#