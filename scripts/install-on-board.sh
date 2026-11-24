#!/usr/bin/env bash
# Install autostart units on a CIX Debian board after the two models are provisioned.
set -euo pipefail
repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_dir"
board_user="${SUDO_USER:-$(id -un)}"
qwen_dir="${WEARMIND_QWEN_DIR:-/home/$board_user/wearmind-ai}"
npu_model="${WEARMIND_NPU_POSE_MODEL:-/home/$board_user/wearmind-npu/yolov11n-pose.cix}"
qwen_model="$qwen_dir/qwen2.5-1.5b-instruct-q4_k_m.gguf"

for file in /usr/share/cix/bin/llama-server "$qwen_model" "$npu_model"; do
  if [[ ! -s "$file" ]]; then echo "缺少前置文件：$file" >&2; exit 1; fi
done
python3 -c 'import numpy, cv2; from PIL import Image; from NOE_Engine import EngineInfer' || {
  echo '缺少板端 Python NPU、OpenCV、Pillow 或 numpy 组件' >&2; exit 1;
}
if [[ "${1:-}" == '--check' ]]; then echo '板端前置依赖检查通过'; exit 0; fi
if [[ "$EUID" -ne 0 ]]; then echo '安装开机服务请用 sudo bash scripts/install-on-board.sh' >&2; exit 1; fi
if [[ "$repo_dir" == *' '* ]]; then echo '请把仓库放到不含空格的目录' >&2; exit 1; fi

sed -e "s|User=cix|User=$board_user|" \
    -e "s|/home/cix/wearmind-ai|$qwen_dir|g" \
    scripts/wearmind-qwen.service > /etc/systemd/system/wearmind-qwen.service
sed -e "s|User=cix|User=$board_user|" \
    -e "s|/home/cix/wearmind-v2-release-20261108-122821|$repo_dir|g" \
    scripts/wearmind.service > /etc/systemd/system/wearmind.service
systemctl daemon-reload
systemctl enable --now wearmind-qwen.service wearmind.service
systemctl restart wearmind-qwen.service wearmind.service
systemctl is-active --quiet wearmind-qwen.service
systemctl is-active --quiet wearmind.service
echo '衣伴开机服务已安装：http://127.0.0.1:8790/'
