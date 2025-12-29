import os

# 1. 告訴 OnnxRuntime 不要嘗試設定 CPU 親和性 (Affinity)
# 這是直接針對該錯誤代碼的設定
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

# 2. 如果可以，設定這兩個變數來進一步抑制警告
os.environ["OMP_WAIT_POLICY"] = "PASSIVE"

from flask import Flask
from python_packages.retrieval.retrieval import retrieval_bp
# from python_packages.hello.hello_routes import hello_bp
from python_packages.upload_file.upload_file import upload_file_bp
from python_packages.update.update import update_bp
from python_packages.file_host.file_host import file_host_bp

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="weaviate")

import logging

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpx_logger").setLevel(logging.WARNING)
logging.getLogger("weaviate").setLevel(logging.WARNING)

app = Flask(__name__)
# app.register_blueprint(hello_bp)
app.register_blueprint(retrieval_bp)
app.register_blueprint(upload_file_bp)
app.register_blueprint(update_bp)
app.register_blueprint(file_host_bp)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
