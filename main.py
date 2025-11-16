from python_packages.retrieval.retrieval import app
from python_packages.retrieval.hello_routes import hello_bp

app.register_blueprint(hello_bp)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
