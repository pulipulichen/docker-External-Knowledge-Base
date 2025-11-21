from flask import Flask
from python_packages.retrieval.retrieval import retrieval_bp
# from python_packages.hello.hello_routes import hello_bp
from python_packages.upload_file.upload_file import upload_file_bp

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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
