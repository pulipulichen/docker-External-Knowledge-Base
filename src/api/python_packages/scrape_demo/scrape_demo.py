from flask import Blueprint, render_template


scrape_demo_bp = Blueprint(
    "scrape_demo",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/scrape-demo/static",
)


@scrape_demo_bp.route("/demo/scrape")
def scrape_demo_page():
    return render_template("scrape_demo.html")
