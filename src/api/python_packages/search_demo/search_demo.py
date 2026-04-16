from flask import Blueprint, render_template


search_demo_bp = Blueprint(
    "search_demo",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/search-demo/static",
)


@search_demo_bp.route("/demo/search")
def search_demo_page():
    return render_template("search_demo.html")

