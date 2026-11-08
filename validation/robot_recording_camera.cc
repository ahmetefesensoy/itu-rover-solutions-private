// Rendering-only Gazebo client plugin: frame the existing simulated robot.
// This plugin does not write physics state, poses, or velocity commands.
#include <cmath>
#include <iostream>
#include <gazebo/gazebo.hh>
#include <gazebo/gui/GuiIface.hh>
#include <gazebo/rendering/rendering.hh>

namespace gazebo {
class RobotRecordingCamera : public SystemPlugin {
 public:
  void Load(int, char **) override {
    connection = event::Events::ConnectPreRender([this]() { FrameRobot(); });
  }
 private:
  void FrameRobot() {
    auto camera = gui::get_active_camera();
    if (!camera || !camera->Initialized() || !camera->GetScene()) return;
    auto robot = camera->GetScene()->GetVisual("turtlebot3_burger::base_link");
    if (!robot) robot = camera->GetScene()->GetVisual("turtlebot3_burger");
    if (!robot) return;
    const auto target = robot->WorldPose().Pos() + ignition::math::Vector3d(0, 0, 0.10);
    // Keep an invariant world-frame viewing direction while the robot turns.
    // The actual robot remains near the center and its orientation is visible.
    // A high angle avoids the corridor wall occluding the low robot chassis.
    const ignition::math::Vector3d offset(0.30, -0.30, 1.80);
    const auto position = target + offset;
    const double yaw = std::atan2(-offset.Y(), -offset.X());
    const double pitch = std::atan2(offset.Z(), std::hypot(offset.X(), offset.Y()));
    camera->SetWorldPose(ignition::math::Pose3d(position, ignition::math::Quaterniond(0, pitch, yaw)));
    camera->SetHFOV(ignition::math::Angle(0.55));
    if (!reported) {
      std::cerr << "Recording camera locked on " << robot->Name() << " at " << target << std::endl;
      reported = true;
    }
  }
  bool reported = false;
  event::ConnectionPtr connection;
};
GZ_REGISTER_SYSTEM_PLUGIN(RobotRecordingCamera)
}
