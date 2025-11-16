from flask import Flask
from python_packages.retrieval.retrieval import retrieval_bp
from python_packages.hello.hello_routes import hello_bp

app = Flask(__name__)
app.register_blueprint(hello_bp)
app.register_blueprint(retrieval_bp)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
