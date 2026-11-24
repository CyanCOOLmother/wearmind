# 衣伴 WearMind · 开发板决赛演示版

衣伴从当天场景和用户确认的身体感受出发，结合本机衣橱给出一套可穿的搭配、理由与缺件提示。蓝白完整界面同时适配开发板桌面浏览器和窄屏浏览器。默认入口：`http://127.0.0.1:8790/`。

## 已实现

- 快速选场景、衣橱快捷录入、实拍衣物手动入库、整套推荐、保存与反馈；衣橱数据保存在开发板本地 SQLite。
- Qwen2.5-1.5B-Instruct 通过开发板本机 llama.cpp 服务整理用户文字，用户确认后才用于推荐。该文字模型当前使用 **CPU**，不声称 NPU 大模型加速。
- CIX YOLOv11n-Pose `.cix` 通过 NOE Engine 在 **NPU** 定位人物与 17 个姿势关键点，供 OOTD 构图检查。它不识别衣服品牌、材质或身体状态。
- 手动天气可离线使用；用户主动查询天气时访问 Open-Meteo。云端照片识别已关闭。

## 开发板启动

`scripts/wearmind-qwen.service` 与 `scripts/wearmind.service` 可安装为开机服务。前者启动 CPU Qwen，后者启动衣伴网页并保留原 `data/`。仅开发板浏览器可直接用 `127.0.0.1`；Mac 或手机访问需另外配置安全的网络通路。

手动启动仍可运行 `bash scripts/start-board.sh`。模型文件继续位于 `/home/cix/wearmind-ai/` 和 `/home/cix/wearmind-npu/`，不包含在源码包中。

## 比赛前核验

先运行 `python3 -m unittest discover -s tests -q`，再运行 `python3 scripts/smoke-competition.py` 做真实 Qwen 与 NPU 链路检查。现场演示顺序与边界见 `docs/COMPETITION_DEMO.md`。自检未通过时请说明实际状态，不用示例回复冒充模型结果。
