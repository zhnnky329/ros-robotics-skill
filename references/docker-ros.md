# Docker 容器化 ROS 开发参考

## 第一原则

> Docker 解决的是环境一致性问题，不要把容器当虚拟机用。
> 把构建步骤写进 Dockerfile，而不是手动进容器装东西。

## 官方 ROS Docker 镜像

| 镜像 Tag | 内容 | 用途 |
|----------|------|------|
| `osrf/ros:humble-desktop` | Humble + RViz + 工具 | 开发、可视化 |
| `ros:humble-ros-base` | Humble 基础运行时 | Ubuntu 22.04 部署、CI |
| `osrf/ros:jazzy-desktop` | Jazzy + RViz + 工具 | Ubuntu 24.04 开发、可视化 |
| `ros:jazzy-ros-base` | Jazzy 基础运行时 | Ubuntu 24.04 部署、CI |

Tag 命名规则：`{distro}-{variant}`，variant 包括 `ros-core`（最小）、`ros-base`（基础）、`desktop`（完整）。

## 基础使用

```bash
export ROS_TARGET_DISTRO=jazzy  # Humble 项目改为 humble，所有阶段保持一致
# 启动 ROS 2 容器（host 网络模式最简单，DDS 发现无障碍）
docker run -it --rm --network host "osrf/ros:${ROS_TARGET_DISTRO}-desktop" bash

# 挂载本地工作区
docker run -it --rm --network host \
  -v ~/ros2_ws:/root/ros2_ws \
  "osrf/ros:${ROS_TARGET_DISTRO}-desktop" bash
```

## 多阶段构建 Dockerfile 模板

模板不预装 Nav2；依赖来自项目的 `package.xml`。构建时传 `--build-arg ROS_TARGET_DISTRO=humble` 可选择 Humble，默认 Jazzy。以下为分层骨架，运行阶段还需按项目安装运行时依赖；本文未验证镜像构建或设备联调。

```dockerfile
ARG ROS_TARGET_DISTRO=jazzy
# === 阶段 1: 基础依赖 ===
FROM ros:${ROS_TARGET_DISTRO}-ros-base AS base
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-colcon-common-extensions \
    && rm -rf /var/lib/apt/lists/*

# === 阶段 2: 编译 ===
FROM base AS build
WORKDIR /ros2_ws
COPY src/ src/
RUN apt-get update && rosdep update && \
    rosdep install --from-paths src --ignore-src --rosdistro "$ROS_DISTRO" -r -y && \
    rm -rf /var/lib/apt/lists/*
RUN . "/opt/ros/$ROS_DISTRO/setup.sh" && \
    colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release

# === 阶段 3: 运行时（只保留编译产物）===
FROM ros:${ROS_TARGET_DISTRO}-ros-base AS runtime
COPY --from=build /ros2_ws/install /ros2_ws/install
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["ros2", "launch", "my_robot", "bringup.launch.py"]
```

```bash
#!/bin/bash
# entrypoint.sh
set -e
source "/opt/ros/${ROS_DISTRO:?镜像未声明 ROS_DISTRO}/setup.bash"
source /ros2_ws/install/setup.bash
exec "$@"
```

## GUI 显示（X11 转发）

```bash
# Linux 主机
xhost +local:docker
docker run -it --rm --network host \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  --device /dev/dri:/dev/dri \
  "osrf/ros:${ROS_TARGET_DISTRO:?请先选择目标发行版}-desktop" rviz2
xhost -local:docker
```

## 开发容器 vs 部署容器

| 特性 | 开发容器 | 部署容器 |
|------|---------|---------|
| 源码 | Volume 挂载，实时编辑 | COPY 到镜像内 |
| 工具 | 安装 vim、gdb 等 | 最小化 |
| 构建 | 容器内 colcon build | 多阶段构建 |
| 运行 | `docker run -it` 交互 | `docker run -d` 后台 |

## docker-compose 多节点编排

先设置上面的 `ROS_TARGET_DISTRO`。`my_robot` 的包与 launch 名称是占位示例，SLAM 实现按项目选择；导航入口由项目提供，只有采用 Nav2 时才替换为其 bringup 并声明依赖。

```yaml
# docker-compose.yml
version: "3.8"
services:
  robot_base:
    image: my_robot:${ROS_TARGET_DISTRO:?请先选择目标发行版}
    build:
      context: .
      dockerfile: Dockerfile
      args: { ROS_TARGET_DISTRO: "${ROS_TARGET_DISTRO:?请先选择目标发行版}" }
    network_mode: host
    privileged: true
    devices: ["/dev/ttyUSB0:/dev/ttyUSB0"]
    environment: { ROS_DOMAIN_ID: "42" }
    command: ros2 launch my_robot base_driver.launch.py

  slam:
    image: my_robot:${ROS_TARGET_DISTRO:?请先选择目标发行版}
    network_mode: host
    environment: { ROS_DOMAIN_ID: "42" }
    depends_on: [robot_base]
    command: ros2 launch slam_toolbox online_async_launch.py

  navigation:
    image: my_robot:${ROS_TARGET_DISTRO:?请先选择目标发行版}
    network_mode: host
    environment: { ROS_DOMAIN_ID: "42" }
    depends_on: [robot_base, slam]
    volumes: ["./maps:/maps:ro"]
    command: ros2 launch my_robot navigation.launch.py
```

```bash
docker compose up -d          # 启动所有服务
docker compose logs -f slam   # 查看日志
docker compose down           # 停止
```

## DDS 与容器网络

`--network host` 最简单，DDS 直接可用。必须用 bridge 时，配置 CycloneDDS 单播：

```xml
<!-- cyclonedds.xml -->
<CycloneDDS>
  <Domain>
    <General>
      <AllowMulticast>false</AllowMulticast>
    </General>
    <Discovery>
      <Peers>
        <Peer address="robot_base"/>
        <Peer address="slam"/>
      </Peers>
    </Discovery>
  </Domain>
</CycloneDDS>
```

```bash
export CYCLONEDDS_URI=file:///config/cyclonedds.xml
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

## 常见故障

| 现象 | 可能原因 | 解决方法 |
|------|---------|---------|
| 容器间节点找不到 | 网络模式/DDS 配置 | 优先用 `--network host` |
| GUI 无法显示 | DISPLAY/权限 | `xhost +local:docker` |
| 编译缓存失效 | Dockerfile 层顺序 | `COPY src/` 放在依赖安装之后 |
| 容器内找不到设备 | 缺 `--privileged` | 添加 `--device` 映射 |

## 官方与高星参考

- [OSRF Docker Images](https://hub.docker.com/r/osrf/ros)
- [ROS 2 Docker 教程](https://docs.ros.org/en/humble/How-To-Guides/Run-2-Nodes-in-Docker.html)
- [VS Code Dev Containers + ROS](https://github.com/athackst/vscode_ros2_workspace)
