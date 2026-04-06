import os

# 1. 告訴 OnnxRuntime 不要嘗試設定 CPU 親和性 (Affinity)
# 這是針對該錯誤代碼的設定
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

# 2. 如果可以，設定這兩個變數來進一步抑制警告
os.environ["OMP_WAIT_POLICY"] = "PASSIVE"

from flask import Flask

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="weaviate")

import logging

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpx_logger").setLevel(logging.WARNING)
logging.getLogger("weaviate").setLevel(logging.WARNING)

_API_DIR = os.path.dirname(os.path.abspath(__file__))
_DEMO_DIR = os.path.join(_API_DIR, 'python_packages', 'demo')
app = Flask(
    __name__,
    static_folder=os.path.join(_DEMO_DIR, 'static'),
    static_url_path='/static',
    template_folder=os.path.join(_DEMO_DIR, 'templates'),
)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
