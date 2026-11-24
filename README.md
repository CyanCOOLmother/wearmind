# 衣伴 WearMind · 开发板决赛演示版

衣伴从当天场景和用户确认的身体感受出发，结合本机衣橱给出一套可穿的搭配、理由与缺件提示。蓝白完整界面同时适配开发板桌面浏览器和窄屏浏览器。默认入口：`http://127.0.0.1:8790/`。

## 已实现

- 快速选场景、衣橱快捷录入、实拍衣物手动入库、整套推荐、保存与反馈；衣橱数据保存在开发板本地 SQLite。
- Qwen2.5-1.5B-Instruct 通过开发板本机 llama.cpp 服务整理用户文字，用户确认后才用于推荐。该文字模型当前使用 **CPU**，不声称 NPU 大模型加速。
- CIX YOLOv11n-Pose `.cix` 通过 NOE Engine 在 **NPU** 定位人物与 17 个姿势关键点，供 OOTD 构图检查。它不识别衣服品牌、材质或身体状态。
- 手动天气可离线使用；用户主动查询天气时访问 Open-Meteo。云端照片识别已关闭。

## 运行环境与模型

实测平台为 CIX P1 开发板、Debian 12、Python 3.11。网页与规则层只用 Python 标准库；NPU 流程还需要板端 `NOE_Engine`、`numpy`、`python3-opencv`、`python3-pil` 和 `/usr/share/cix/lib`。模型服务使用 `/usr/share/cix/bin/llama-server`。

模型不包含在仓库中，需先放好：

- `/home/cix/wearmind-ai/qwen2.5-1.5b-instruct-q4_k_m.gguf`
- `/home/cix/wearmind-npu/yolov11n-pose.cix`，实测 SHA256：`abe863635c25d69002df5b91b897ff8ef7c7053f9847543a0764f62b7f8de3a1`

此版本不自动下载、转换或购买模型。若使用其他目录，可在运行前设置 `WEARMIND_QWEN_DIR` 与 `WEARMIND_NPU_POSE_MODEL`；开机服务模板中的模型路径也需相应调整。

## 部署与启动

在模型和板端运行库已就绪的 CIX Debian 开发板上，把仓库放在 `cix` 用户可访问的目录，进入仓库根目录执行：

```bash
bash scripts/install-on-board.sh --check
sudo bash scripts/install-on-board.sh
```

第二条命令会安装并启动 `wearmind-qwen.service` 和 `wearmind.service`；以后开机自动启动。程序只监听开发板本机 `127.0.0.1:8790`，在开发板浏览器打开 `http://127.0.0.1:8790/`。衣橱与历史数据写入仓库的 `data/`，已被 `.gitignore` 排除。Mac 或手机访问需要额外的安全网络通路。

不安装服务时，可先自行启动本机 llama.cpp 服务，再执行 `bash scripts/start-board.sh`。从全新开发板获取并安装 CIX SDK 和两份模型的过程尚未验证为一键完成；上面的“一键”仅覆盖**已备好运行环境和模型后的应用与开机服务部署**。

## 比赛前核验

先运行 `python3 -m unittest discover -s tests -q`，再运行 `python3 scripts/smoke-competition.py` 做真实 Qwen 与 NPU 链路检查。自检未通过时请说明实际状态，不用示例回复冒充模型结果。当前文字模型只做一次条件理解，推荐由本地规则引擎生成；没有多轮对话或模型自主工具调度。
