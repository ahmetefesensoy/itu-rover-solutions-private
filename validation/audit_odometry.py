"""Diagnose the bag's wheel conventions and orientation without changing defaults."""
import json
import math
from pathlib import Path
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from bag_evaluation import read_bag
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"iturover_odometry_assignment_ros2/src"))
from odometry_core import quaternion_yaw

samples=list(read_bag(ROOT/"iturover_odometry_assignment_ros2/rosbag/scenario/scenario_0.db3"))
t0=samples[0][1]
left=[];right=[];imu=[]
for topic,t,msg in samples:
    if "left_motors" in topic: left.append((t-t0,*msg.data))
    elif "right_motors" in topic: right.append((t-t0,*msg.data))
    else:
        q=msg.orientation
        imu.append((t-t0,quaternion_yaw(q.x,q.y,q.z,q.w),math.hypot(q.x,q.y,q.z,q.w)))
left,right,imu=map(np.array,(left,right,imu))
times=np.arange(0,samples[-1][1]-t0,.02)
li=np.clip(np.searchsorted(left[:,0],times,side="right")-1,0,len(left)-1)
ri=np.clip(np.searchsorted(right[:,0],times,side="right")-1,0,len(right)-1)
ii=np.clip(np.searchsorted(imu[:,0],times,side="right")-1,0,len(imu)-1)
ls,rs=left[li,1:].mean(axis=1),right[ri,1:].mean(axis=1)
v=(ls+rs)*.135*math.pi/60
w=(rs-ls)*.135*2*math.pi/60/.89
wheel_yaw=np.cumsum(w)*.02
imu_yaw=np.unwrap(imu[ii,1]);imu_yaw-=imu_yaw[0]
def integrate(yaw):
    return np.column_stack((np.cumsum(v*np.cos(yaw))*.02,np.cumsum(v*np.sin(yaw))*.02))
fig,axes=plt.subplots(2,2,figsize=(13,9))
axes[0,0].plot(left[:,0],left[:,1],label="Left front")
axes[0,0].plot(left[:,0],left[:,2],label="Left rear")
axes[0,0].plot(right[:,0],right[:,1],label="Right front")
axes[0,0].plot(right[:,0],right[:,2],label="Right rear")
axes[0,0].set(title="Recorded RPM",xlabel="Time (s)",ylabel="RPM")
axes[0,0].legend(fontsize=8)
axes[0,1].plot(times,np.degrees(wheel_yaw),label="Wheel model (track 0.890m)")
axes[0,1].plot(times,np.degrees(imu_yaw),label="Normalized recorded quaternion (flagged invalid)")
axes[0,1].set(title="Heading diagnostic",xlabel="Time (s)",ylabel="Unwrapped yaw (degrees)")
axes[0,1].legend(fontsize=8)
for ax,yaw,title in ((axes[1,0],wheel_yaw,"Current wheel-only model"),(axes[1,1],imu_yaw,"Diagnostic only: normalized IMU heading")):
    path=integrate(yaw)
    ax.plot(path[:,0],path[:,1]);ax.scatter([path[0,0]],[path[0,1]],color="green",label="Start")
    ax.scatter([path[-1,0]],[path[-1,1]],color="red",label="End")
    ax.axis("equal");ax.set(title=title,xlabel="x (m)",ylabel="y (m)");ax.legend()
for ax in axes.flat:ax.grid(alpha=.25)
fig.tight_layout()
fig.savefig(ROOT/"validation/odometry_audit.png",dpi=150)
metrics={"left_rpm_ranges":np.column_stack((left[:,1:].min(axis=0),left[:,1:].max(axis=0))).tolist(),
"right_rpm_ranges":np.column_stack((right[:,1:].min(axis=0),right[:,1:].max(axis=0))).tolist(),
"quaternion_norm_range":[float(imu[:,2].min()),float(imu[:,2].max())],
"wheel_total_yaw_deg":float(np.degrees(wheel_yaw[-1])),"diagnostic_imu_total_yaw_deg":float(np.degrees(imu_yaw[-1])),
"wheel_abs_turn_deg":float(np.degrees(abs(w).sum()*.02)),
"diagnostic_imu_abs_turn_deg":float(np.degrees(np.abs(np.diff(imu_yaw)).sum()))}
(ROOT/"validation/odometry_audit.json").write_text(json.dumps(metrics,indent=2)+"\n")
print(json.dumps(metrics,indent=2))
