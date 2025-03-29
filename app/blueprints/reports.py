from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.services.report_service import report_service
from app.utils.logger import log_activity

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route("")
def view_reports():
    # View all reports with pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Get all reports
    all_reports = report_service.get_all_reports()
    
    # Pagination values
    total_reports = len(all_reports)
    total_pages = (total_reports + per_page - 1) // per_page
    
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total_reports)
    paginated_reports = all_reports[start_idx:end_idx]
    
    return render_template(
        "view_report.html", 
        reports=paginated_reports,
        page=page,
        per_page=per_page,
        total_reports=total_reports,
        total_pages=total_pages
    )

@reports_bp.route("/<filename>")
def view_report(filename):
    # View a specific report
    report = report_service.get_report(filename)
    if not report:
        flash("Report not found")
        return redirect(url_for("reports.view_reports"))
    
    return render_template("report.html", report=report)