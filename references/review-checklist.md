# ROS 机器人项目审查清单

## 构建与工作区

- 是否确认目标为 Ubuntu 24.04 + Jazzy 或 Ubuntu 22.04 + Humble，且实际 OS、ROS_DISTRO 与 setup 路径一致
- 是否解决检测器的发行版歧义/缺失警告，避免混用跨版本 overlay 与构建产物
- 是否识别 `ament_cmake` / `ament_python` 包并沿用 `colcon` 工作流
- `package.xml` 与 `CMakeLists.txt` / `setup.py` 是否一致

## 接口与消息

- topic / service / action 命名是否稳定
- 单位、字段语义、命名空间、remap 是否一致
- ROS 2 是否显式处理 QoS

## TF 与时间

- TF 是否单根
- 静态 TF 与动态 TF 是否分对
- 时间戳是否连续
- `frame_id` / `child_frame_id` 是否一致

## 传感器与底盘

- IMU 轴向、LiDAR frame、底盘运动学、编码器方向是否清晰
- 是否有失连保护和超时停车

## 导航与控制

- 是否确认实际导航架构，仅在已选用 Nav2 时检查其 Costmap、插件和行为树配置
- 定位、里程计、地图表示、规划与控制频率是否与机器人能力匹配
- `/cmd_vel` 链路是否真正闭环

## 嵌入式与总线

- 串口 / CAN 帧格式、校验、时间源是否明确
- 是否存在 ISR 阻塞、动态分配、无界循环、竞态访问

## 验证证据

- 是否分别记录静态检查、已执行测试及 OS/Python/ROS 环境、未执行的目标机验证
- 是否在目标发行版完成 rosdep、colcon 构建/测试、示例消息通信，再按项目验证 TF、QoS、仿真与底盘链路
