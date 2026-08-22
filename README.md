# ROS Robotics Skill

一个面向 **Ubuntu 22.04、ROS 2 Humble 与 RoboMaster 哨兵自主导航开发** 的工程化 skill，支持 **Codex** 和 **Claude Code**。

它不是机器人控制程序，而是一套供 AI 编程助手使用的 ROS 2 工作流程、专题资料和静态检查工具，帮助 Agent 在修改代码前先建立可验证的问题链路。

## 目标环境

| 项目 | 支持范围 |
| --- | --- |
| 操作系统 | Ubuntu 22.04 |
| ROS | ROS 2 Humble |
| 构建系统 | `ament_cmake`、`ament_python`、`colcon` |
| Agent | Codex、Claude Code |
| 主要场景 | RoboMaster 哨兵自主导航、底盘与传感器联调 |

本仓库只维护上表所列环境与 Agent 的工作流。

## 解决的问题

- `package.xml`、`CMakeLists.txt`、安装规则不一致导致构建或运行失败。
- URDF/Xacro、TF、时间戳、frame 和传感器外参错误。
- LiDAR、IMU、编码器、里程计、SLAM 与定位链路不稳定。
- Nav2 已规划但 `/cmd_vel` 没有正确到达底盘。
- 差速与全向底盘配置混用，速度、角速度或坐标轴语义错误。
- 串口/CAN 下位机通信缺少校验、超时、重连或失联停车。
- QoS、DDS、Lifecycle、参数和命名空间问题。
- 现场问题缺少 rosbag2、日志和可复现证据。

## 工作流程

```text
识别 ROS 2 工作区
→ 检查依赖和资源安装规则
→ 明确底盘、传感器、定位与 TF 链路
→ 按问题读取最少必要资料
→ 小步修改
→ 构建、仿真或低速实车验证
```

## 安装

### 本地安装

```bash
git clone https://github.com/wzyn20051216/ros-robotics-skill.git
cd ros-robotics-skill

# 同时安装到当前设备上的 Codex 和 Claude Code
python3 scripts/install.py --target all --force
```

也可以只安装一个目标：

```bash
python3 scripts/install.py --target codex --force
python3 scripts/install.py --target claude --force
```

默认安装位置：

| Agent | 安装目录 |
| --- | --- |
| Codex | `~/.codex/skills/ros-robotics` |
| Claude Code | `~/.claude/skills/ros-robotics` |

卸载：

```bash
python3 scripts/install.py --target all --uninstall
```

### 一键安装

```bash
curl -fsSL https://raw.githubusercontent.com/wzyn20051216/ros-robotics-skill/main/install.sh | bash
```

一键安装默认自动识别本机已有的 Codex 和 Claude Code；也可以传入 `--target codex`、`--target claude` 或 `--target all`。

## 辅助工具

### 识别 ROS 2 工作区

```bash
python3 scripts/detect_ros_workspace.py /path/to/workspace
python3 scripts/detect_ros_workspace.py /path/to/workspace --json
```

识别 `ament_cmake`、`ament_python` 和未知包，并给出 ROS 2 Humble/colcon 建议命令。

### 检查依赖和安装规则

```bash
python3 scripts/check_ros_workspace_consistency.py /path/to/workspace
```

检查 CMake 与 `package.xml` 依赖、可执行目标安装、launch/config/URDF 等资源安装、launch 引用、YAML 语法和 Python package 数据文件。

### 检查 URDF/Xacro 与 TF 树

```bash
python3 scripts/check_tf_tree.py /path/to/robot.urdf
python3 scripts/check_tf_tree.py /path/to/robot.urdf.xacro --json
```

检查重复 link/joint、多根、悬挂 link、父子关系和循环依赖。

## 专题资料

- ROS 2 构建：`references/ros2-colcon.md`
- URDF/Xacro/TF：`references/robot-description-and-tf.md`
- Navigation2：`references/navigation2.md`
- `ros2_control`：`references/ros2-control.md`
- MCU、串口、CAN、micro-ROS：`references/micro-ros-and-embedded.md`
- SLAM 与定位：`references/slam-mapping.md`
- DDS/QoS/网络：`references/dds-qos-networking.md`
- rosbag2 与诊断：`references/rosbag-diagnostics.md`
- Gazebo 仿真：`references/gazebo-simulation.md`
- Lifecycle 与组件：`references/lifecycle-and-components.md`
- 自定义接口：`references/custom-interfaces.md`
- 多机器人：`references/multi-robot.md`
- Docker：`references/docker-ros.md`
- Foxglove/PlotJuggler：`references/foxglove-visualization.md`
- 排障流程：`references/debug-playbooks.md`
- 审查清单：`references/review-checklist.md`

## 最小 ROS 2 示例

`examples/minimal_ws/` 包含一个可用 `colcon` 构建的 `ament_cmake` 示例：

- C++ talker/listener。
- launch 文件。
- 参数 YAML。
- 标准 `package.xml`、CMake 和安装规则。

```bash
source /opt/ros/humble/setup.bash
cd examples/minimal_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
ros2 launch minimal_demo demo.launch.py
```

## 开发验证

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
python3 scripts/validate_project.py
```

## 项目结构

```text
.
├── SKILL.md               # Agent 工作流程与参考路由
├── agents/openai.yaml     # Codex 展示信息
├── references/            # 按需加载的 ROS 2 专题资料
├── scripts/               # 检测、检查和双 Agent 安装器
├── tests/                 # Python 单元测试
├── examples/minimal_ws/   # 最小 ROS 2 示例
├── install.sh
└── README.md
```

## 适用边界

- 当前尚未加入 RoboMaster 专用参数模板或新诊断脚本。
- 底盘运动学、接口协议和传感器外参必须以真实硬件为准。
- 实车测试应先确认急停、超时停车和安全场地，再从低速开始。
