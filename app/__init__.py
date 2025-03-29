from flask import Flask
from flask_assets import Environment, Bundle
from app.config import Config
import os
from app.utils.cache import init_cache

def create_app(config_class=Config):
    # Create and configure the Flask app
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    app.config.from_object(config_class)
    
    # Initialize Flask-Assets
    assets = Environment(app)
    
    # This is to reduce the amount of requests made, improving load times
    css = Bundle(
        # Base
        'css/base/variables.css',
        'css/base/reset.css',
        'css/base/typography.css',
        
        # Layout
        'css/layout/header.css',
        'css/layout/footer.css',
        'css/layout/containers.css',
        'css/layout/navigation.css',
        
        # Components
        'css/components/buttons.css',
        'css/components/forms.css',
        'css/components/counters.css',
        'css/components/tables.css',
        'css/components/cards.css',
        'css/components/alerts.css',
        
        # Pages
        'css/pages/home.css',
        'css/pages/reports.css',
        'css/pages/match-planner.css',
        'css/pages/admin.css',
        
        # Utilities
        'css/utilities/helpers.css',
        'css/utilities/responsive.css',
        
        filters='cssmin',
        output='gen/all.css'
    )
    assets.register('css_all', css)
    
    # Initialize cache
    init_cache(app)
    
    # Create necessary directories
    os.makedirs(app.config["REPORTS_DIR"], exist_ok=True)
    os.makedirs(app.config["LOGS_DIR"], exist_ok=True)
    
    # Import user_manager from app.services
    from app.services.user_service import user_manager
    app.user_manager = user_manager
    
    # Register blueprints
    from app.blueprints.main import main_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.scout import scout_bp
    from app.blueprints.reports import reports_bp
    from app.blueprints.stats import stats_bp
    from app.blueprints.match_planner import planner_bp
    from app.blueprints.admin import admin_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(scout_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(planner_bp)
    app.register_blueprint(admin_bp)
    
    # Error handlers
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)
    
    # Template filters
    from app.utils.template_filters import register_template_filters
    register_template_filters(app)
    
    return app