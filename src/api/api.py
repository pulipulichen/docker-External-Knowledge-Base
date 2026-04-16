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
from .python_packages.retrieval.retrieval import retrieval_bp
from .python_packages.knowledge_base_config.knowledge_list import knowledge_list_bp
# from .python_packages.hello.hello_routes import hello_bp
from .python_packages.upload_file.upload_file import upload_file_bp
from .python_packages.update.update import update_bp
from .python_packages.file_host.file_host import file_host_bp
from .python_packages.search.search import search_bp
from .python_packages.scrape.scrape import scrape_bp
from .python_packages.news.news import news_bp
from .python_packages.reset.reset import reset_bp
from .python_packages.retrieval_demo.retrieval_demo import retrieval_demo_bp
from .python_packages.search_demo.search_demo import search_demo_bp
from .python_packages.reset_demo.reset_demo import reset_demo_bp
from .python_packages.ingest.ingest_all import ingest_all_bp

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="weaviate")

import logging

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpx_logger").setLevel(logging.WARNING)
logging.getLogger("weaviate").setLevel(logging.WARNING)

_API_DIR = os.path.dirname(os.path.abspath(__file__))
_RETRIEVAL_DEMO_DIR = os.path.join(_API_DIR, 'python_packages', 'retrieval_demo')
app = Flask(
    __name__,
    static_folder=os.path.join(_RETRIEVAL_DEMO_DIR, 'static'),
    static_url_path='/static',
    template_folder=os.path.join(_RETRIEVAL_DEMO_DIR, 'templates'),
)
# app.register_blueprint(hello_bp)
app.register_blueprint(retrieval_bp)
app.register_blueprint(knowledge_list_bp)
app.register_blueprint(upload_file_bp)
app.register_blueprint(update_bp)
app.register_blueprint(file_host_bp)
app.register_blueprint(search_bp)
app.register_blueprint(scrape_bp)
app.register_blueprint(news_bp)
app.register_blueprint(reset_bp)
app.register_blueprint(retrieval_demo_bp)
app.register_blueprint(search_demo_bp)
app.register_blueprint(reset_demo_bp)
app.register_blueprint(ingest_all_bp)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
