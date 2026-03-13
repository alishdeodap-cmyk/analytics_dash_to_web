from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(
        __name__,
        template_folder='../templates',
        static_folder='../static'
    )
    app.config.from_object('config.Config')

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'error'

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Force password change before accessing any page
    @app.before_request
    def enforce_password_change():
        allowed_endpoints = {'auth.login', 'auth.logout', 'auth.change_password', 'static'}
        if (
            current_user.is_authenticated
            and current_user.force_pw_change
            and request.endpoint not in allowed_endpoints
        ):
            return redirect(url_for('auth.change_password'))

    # Register blueprints
    from app.routes.auth import auth
    from app.routes.portal import portal
    from app.routes.admin import admin

    app.register_blueprint(auth)
    app.register_blueprint(portal)
    app.register_blueprint(admin)

    # Error handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    return app
