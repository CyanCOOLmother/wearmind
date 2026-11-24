# 决赛源码说明

本仓库只放源码、网页资源、测试与启动脚本。模型权重、`.cix` 文件和用户数据不包含在仓库里。

当前开发板上，Qwen2.5-1.5B-Instruct 经 llama.cpp 在 CPU 推理，CIX YOLOv11n-Pose 经 NOE Engine 在 NPU 推理。衣伴的文字入口是单次条件理解与用户确认，推荐由本地衣橱及规则完成。当前没有多轮聊天或模型自主工具调度。

板端手动启动：`bash scripts/start-board.sh`。端到端自检：`python3 scripts/smoke-competition.py`。开机服务文件位于 `scripts/wearmind*.service`，其中路径需按实际安装目录调整。

依赖 CIX 板端 NOE_Engine、numpy、Pillow、OpenCV、Qwen 本地 llama.cpp 服务及对应模型；模型文件另行部署。当前从干净开发板的一键安装未验证，因此不要将此仓库描述为零配置部署。
