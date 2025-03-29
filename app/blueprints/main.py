from flask import Blueprint, render_template
from app.utils.site_settings import get_site_settings

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def index():
    # Home page
    system_notice = get_site_settings().get("system_notice", "")
    return render_template("index.html", system_notice=system_notice)

@main_bp.route("/test")
def test_route():
    # Test route
    return "Testing Site! Turn Back if You Aren't A Tester!"

@main_bp.route("/debug/routes")
def debug_routes():
    # List all routes (testing)
    from flask import current_app
    routes = []
    for rule in current_app.url_map.iter_rules():
        routes.append({
            "endpoint": rule.endpoint,
            "methods": [method for method in rule.methods if method != "HEAD" and method != "OPTIONS"],
            "rule": str(rule)
        })
    return render_template("debug_routes.html", routes=routes)