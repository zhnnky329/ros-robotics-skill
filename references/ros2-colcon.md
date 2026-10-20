# ROS 2 Colcon 工作流

## 适用场景

- 包使用 `ament_cmake` 或 `ament_python`
- 工作区使用 `colcon build`
- 任务涉及 QoS、参数声明、Lifecycle 或安装规则

## 安全默认流程

先确认目标配对：Ubuntu 24.04 + Jazzy，或 Ubuntu 22.04 + Humble。检测器按 `--ros-distro` → `ROS_DISTRO` → `/opt/ros/*/setup.bash` 唯一安装选择；多个安装、未安装或不支持的版本不会自动回退。`ROS_DISTRO` 只是环境线索，不能证明 OS、依赖或 overlay 匹配。

以下 Bash 示例在工作区根目录、未加载其他发行版的新终端执行。`ROS_TARGET_DISTRO` 是显式选择；不要依赖尚未 source 时可能为空的 `ROS_DISTRO`：

```bash
ROS_TARGET_DISTRO=jazzy  # Ubuntu 22.04 + Humble 改为 humble
source "/opt/ros/${ROS_TARGET_DISTRO}/setup.bash"
rosdep install --from-paths src --ignore-src --rosdistro "$ROS_TARGET_DISTRO" -r -y
colcon build
source install/setup.bash
colcon test
colcon test-result --verbose
```

若 setup 不存在，先安装目标 ROS 或确认源码安装的实际 underlay 路径，不继续构建。检测脚本只生成标准安装命令，不检查 Ubuntu 版本或执行命令。切换发行版时用独立工作区/构建目录，避免复用旧 `build/`、`install/`、`log/`。

## 核心检查点

- `package.xml format="3"` 依赖是否完整
- `ament_package()` 是否保留在正确位置
- `launch/`、`config/`、`urdf/`、`rviz/` 是否有安装规则
- QoS、参数声明、命名空间、`use_sim_time` 是否处理正确

## 常见调试命令

```bash
ros2 topic list
ros2 topic info /topic_name
ros2 node list
ros2 node info /node_name
ros2 param list
ros2 doctor
```

## 官方参考

- Jazzy 安装与环境：<https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html>
- Humble 安装与环境：<https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html>
- Jazzy `colcon`：<https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Colcon-Tutorial.html>
- Jazzy `rosdep`：<https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Rosdep.html>
- ROS 2 `colcon`：<https://docs.ros.org/en/humble/Tutorials/Beginner-Client-Libraries/Colcon-Tutorial.html>
- `rosdep`：<https://docs.ros.org/en/humble/Tutorials/Intermediate/Rosdep.html>
- REP-149：<https://www.ros.org/reps/rep-0149.html>
