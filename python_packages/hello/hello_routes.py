from flask import Blueprint

hello_bp = Blueprint('hello_bp', __name__)

@hello_bp.route('/')
def hello_world():
    return "hello world"
