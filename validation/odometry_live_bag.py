"""Capture the corrected installed ROS node while the full real bag plays."""
import json
import math
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rclpy
from nav_msgs.msg import Odometry
from rosgraph_msgs.msg import Clock
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data

ROOT=Path(__file__).resolve().parents[1]
RESULTS=Path(os.environ.get("ITU_RESULTS",str(ROOT/"validation")))


def main():
    with sqlite3.connect(str(ROOT/"iturover_odometry_assignment_ros2/rosbag/scenario/scenario_0.db3")) as conn:
        first,last=conn.execute("SELECT min(timestamp),max(timestamp) FROM messages").fetchone()
    first,last=first*1e-9,last*1e-9
    RESULTS.mkdir(exist_ok=True,parents=True)
    expected=json.loads((ROOT/"validation/bag_results.json").read_text())["odometry"]["solution_final_xy_m"]
    rclpy.init()
    node=Node("corrected_odometry_live_validation")
    samples=[]
    clock=[0.0]
    def receive(msg):
        stamp=msg.header.stamp.sec+msg.header.stamp.nanosec*1e-9
        if stamp>=first:
            q=msg.pose.pose.orientation
            samples.append({"stamp":stamp,"x":msg.pose.pose.position.x,"y":msg.pose.pose.position.y,
                            "yaw":2*math.atan2(q.z,q.w),"v":msg.twist.twist.linear.x})
    node.create_subscription(Odometry,"/odom",receive,100)
    node.create_subscription(Clock,"/clock",lambda m:clock.__setitem__(0,m.clock.sec+m.clock.nanosec*1e-9),qos_profile_sensor_data)
    with open(RESULTS/"odometry_live_launch.log","w") as log:
        process=subprocess.Popen(["ros2","launch","iturover_odometry_assignment","rosbag.launch.py","rate:=4.0"],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            end=time.monotonic()+80
            while clock[0]<last-.06 and time.monotonic()<end:
                rclpy.spin_once(node,timeout_sec=.02)
                assert process.poll() is None, "Launch exited unexpectedly"
            assert clock[0]>=last-.06, (clock[0],last)
            until=time.monotonic()+.3
            while time.monotonic()<until:
                rclpy.spin_once(node,timeout_sec=.01)
            assert len(samples)>500, len(samples)
            final=samples[-1]
            difference=math.hypot(final["x"]-expected[0],final["y"]-expected[1])
            assert difference<.7, (difference,final,expected)
            headings=np.unwrap([s["yaw"] for s in samples])
            total_turn=float(np.degrees(headings[-1]-headings[0]))
            assert 350<total_turn<370,total_turn
            assert math.hypot(final["x"],final["y"])<5
            report={"heading_source":"imu","orientation_policy":"assignment_q14",
                    "ros_distro":os.environ.get("ROS_DISTRO"),
                    "actual_ros_odom_messages":len(samples),"recorded_duration_s":last-first,
                    "playback_rate":4,"live_final_xy_m":[final["x"],final["y"]],
                    "offline_final_xy_m":expected,"live_vs_offline_endpoint_difference_m":difference,
                    "live_total_turn_deg":total_turn,"near_closed_route":True,
                    "note":"Actual ROS2 /odom output, not an offline-only rendering. No measured physical ground truth."}
            (RESULTS/"odometry_live_results.json").write_text(json.dumps(report,indent=2)+"\n")
            (RESULTS/"odometry_live_samples.json").write_text(json.dumps(samples)+"\n")
            fig,ax=plt.subplots(figsize=(8,7))
            ax.plot([s["x"] for s in samples],[s["y"] for s in samples],color="#1177cc",lw=2,label="Actual ROS2 /odom")
            ax.scatter([samples[0]["x"]],[samples[0]["y"]],label="Start",color="green")
            ax.scatter([final["x"]],[final["y"]],label="End",color="orange")
            ax.set(xlabel="x (m)",ylabel="y (m)",title="Corrected assignment: real ROS2 bag playback")
            ax.axis("equal");ax.grid(alpha=.3);ax.legend();fig.tight_layout()
            fig.savefig(RESULTS/"odometry_live.png",dpi=160)
            print(json.dumps(report,indent=2),flush=True)
        finally:
            if process.poll() is None:
                os.killpg(process.pid,signal.SIGINT)
                try: process.wait(timeout=6)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid,signal.SIGKILL);process.wait()
            node.destroy_node()
            if rclpy.ok():
                rclpy.shutdown()


if __name__=="__main__":
    main()
