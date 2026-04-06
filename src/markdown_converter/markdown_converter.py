import logging
import os

# Limit thread pools used by native libs (OnnxRuntime / BLAS noise in containers).
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["OMP_WAIT_POLICY"] = "PASSIVE"

from flask import Flask

from markitdown_endpoint.routes import markitdown_convert_bp
from marker_pdf_endpoint.routes import marker_pdf_convert_bp

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.register_blueprint(markitdown_convert_bp)
app.register_blueprint(marker_pdf_convert_bp)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=80)
