"""Read-only board inventory. Run with python3 -B scripts/inspect_board.py."""
import json
import platform
import shutil
import subprocess
from pathlib import Path
from urllib.request import build_opener,ProxyHandler

report={'system':platform.system(),'architecture':platform.machine(),'python':platform.python_version(),
        'binaries':{x:shutil.which(x) for x in ('python3','ollama','llama-server','llama-cli')},
        'accelerator_devices':[str(p) for pattern in ('*npu*','*aipu*') for p in Path('/dev').glob(pattern)],
        'note':'只读结果；未安装、启动、下载模型，未更改系统，也未运行推理'}
if Path('/proc/meminfo').exists():
    report['memory']=[x for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith(('MemTotal:','MemAvailable:'))]
models={}
for name,url in [('ollama','http://127.0.0.1:11434/api/tags'),('llamacpp','http://127.0.0.1:8080/v1/models')]:
    try:
        with build_opener(ProxyHandler({})).open(url,timeout=2) as r: data=json.loads(r.read(1024*1024))
        models[name]=[x.get('name',x.get('id','')) for x in data.get('models',data.get('data',[])) if isinstance(x,dict)]
    except Exception: models[name]={'available':False}
report['running_model_services']=models
if shutil.which('dpkg-query'):
    result=subprocess.run(['dpkg-query','-W','-f=${Package} ${Version}\n','*cix*','*neural*'],capture_output=True,text=True,timeout=10)
    report['sdk_packages']=result.stdout.splitlines()[:40]
print(json.dumps(report,ensure_ascii=False,indent=2))
