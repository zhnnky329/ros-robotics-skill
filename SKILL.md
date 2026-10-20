---
name: ros-robotics
description: 面向 Ubuntu 24.04 + ROS 2 Jazzy 和 Ubuntu 22.04 + ROS 2 Humble 的 ROS 2 工程与 RoboMaster 哨兵自主导航开发 skill。用于 ament/colcon 工作区、底盘与 MCU 通信、URDF/TF、IMU/雷达/里程计、SLAM、定位、自定义规划控制、可选 Navigation2、ros2_control、QoS、rosbag2、仿真和实车联调；适配 Codex 与 Claude Code。
---

# ROS Robotics

## 环境边界

- 维护 Ubuntu 24.04 + ROS 2 Jazzy 与 Ubuntu 22.04 + ROS 2 Humble 两组目标环境；先确认实际 OS、发行版与安装路径，不将目标支持等同于运行验证。
- 只使用 `ament_cmake`、`ament_python` 与 `colcon` 工作流。
- 优先服务 RoboMaster 哨兵自主导航，同时保留相关 ROS 2 通用能力。
- 将 Nav2 视为可选框架；仅在用户选用或仓库已依赖 Nav2 时读取其专用资料，不默认引入 Nav2、AMCL、Costmap 或行为树。
- 对自定义规划控制系统（如基于 SUPER/SANDO 的集成），先确认现有架构与 ROS 接口；不据此假定上游框架已兼容 Jazzy。
- 不处理上述环境边界之外的工作流。

## 工作顺序

1. 运行 `python3 scripts/detect_ros_workspace.py <workspace-path>` 识别工作区、包类型和发行版。显式目标用 `--ros-distro jazzy` 或 `--ros-distro humble`；选择顺序为参数、`ROS_DISTRO`、`/opt/ros` 中唯一含 `setup.bash` 的安装。若有警告，先解决歧义、环境冲突或缺失 underlay，不猜测发行版。
2. 运行 `python3 scripts/check_ros_workspace_consistency.py <workspace-path>` 检查依赖与安装规则。
3. 明确导航框架、底盘运动学、下位机接口、传感器、定位来源和 TF 发布者。
4. 按问题加载最少必要的参考文件。
5. 小步修改，并给出构建、仿真或低速实车验证命令。

## 参考文件路由

- 构建与 package：`references/ros2-colcon.md`
- 模型与 TF：`references/robot-description-and-tf.md`
- 可选 Nav2 与 Costmap（仅限已选用 Nav2）：`references/navigation2.md`
- 控制与硬件接口：`references/ros2-control.md`
- MCU、串口与 CAN：`references/micro-ros-and-embedded.md`
- SLAM 与定位：`references/slam-mapping.md`
- DDS、QoS 与网络：`references/dds-qos-networking.md`
- rosbag2 与离线诊断：`references/rosbag-diagnostics.md`
- Gazebo 仿真：`references/gazebo-simulation.md`
- Lifecycle 与组件：`references/lifecycle-and-components.md`
- 自定义接口：`references/custom-interfaces.md`
- 多机器人与命名空间：`references/multi-robot.md`
- Docker：`references/docker-ros.md`
- Foxglove 与 PlotJuggler：`references/foxglove-visualization.md`
- 系统排障：`references/debug-playbooks.md`
- 审查清单：`references/review-checklist.md`

## 工程原则

- 按已确认发行版生成 source、apt 与 rosdep 命令；检测器只检查标准 `/opt/ros` 安装，不执行 source，也不验证 OS 或实际 ROS 运行。源码/自定义安装需先确认实际 setup 路径。
- 切换发行版时使用干净终端和独立工作区或构建目录，不混用 Humble/Jazzy 的 overlay、`build/`、`install/`、`log/`，不自动删除旧产物。
- 参考资料中的旧版 API、插件和参数片段须对照目标版本官方文档核实；Humble 链接和示例不是 Jazzy 兼容性证明。
- 先确认 `package.xml`、`CMakeLists.txt` 或 `setup.py` 一致，再改业务代码。
- 先检查 topic、频率、时间戳、单位、QoS 与 frame，再调整算法参数。
- 维护唯一且连续的 `map -> odom -> base_link` 主链，避免多个节点重复发布同一 TF。
- 区分差速与全向底盘；未确认运动学前，不套用速度与控制器模板。
- 逐段验证 `/cmd_vel`、指令仲裁、底盘下发、编码器反馈和 `/odom` 闭环。
- 对串口/CAN 实现校验、超时、重连、看门狗与失联停车。
- 现场问题优先录制 rosbag2，以数据复现，不凭感觉改参数。
- 实车验证从架空轮组或低速开始，明确急停方式，不自动执行危险运动命令。

## 输出要求

优先输出：

1. 工作区、包类型和系统链路判断。
2. 关键证据、缺失信息与明确假设。
3. 最小修改点及原因。
4. `colcon build`、测试、仿真或低速实车验证命令。
5. 分别列出静态检查、实际执行的测试及环境、未执行的 ROS 构建/仿真/实车验证项，不把 Python 测试通过写成 Jazzy 运行验证通过。
