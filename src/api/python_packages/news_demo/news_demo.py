from flask import Blueprint, render_template


news_demo_bp = Blueprint(
    "news_demo",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/news-demo/static",
)


@news_demo_bp.route("/demo/news")
def news_demo_page():
    return render_template("news_demo.html")
