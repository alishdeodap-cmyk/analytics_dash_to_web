from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, abort, flash
from flask_login import login_required, current_user
from app.models import Dashboard, DashboardView
from app import db

portal = Blueprint('portal', __name__)


@portal.route('/')
@login_required
def home():
    # Admin always redirects to admin home
    if current_user.is_admin:
        return redirect(url_for('admin.home'))

    recent_views = (
        DashboardView.query
        .filter_by(user_id=current_user.id)
        .order_by(DashboardView.last_viewed.desc())
        .limit(6).all()
    )
    recent_dashboards = [
        v.dashboard for v in recent_views
        if v.dashboard and v.dashboard.is_active
    ]

    allowed = current_user.get_accessible_dashboards()
    return render_template('portal/home.html',
                           recent_dashboards=recent_dashboards,
                           allowed_dashboards=allowed)


@portal.route('/dashboards')
@login_required
def dashboards():
    q = request.args.get('q', '').strip()
    all_dash = current_user.get_accessible_dashboards()
    if q:
        all_dash = [d for d in all_dash if q.lower() in d.name.lower()]
    return render_template('portal/dashboards.html', dashboards=all_dash, q=q)


@portal.route('/dashboard/<int:dashboard_id>')
@login_required
def view_dashboard(dashboard_id):
    dashboard = Dashboard.query.get_or_404(dashboard_id)

    # Server-side permission check — never rely on frontend alone
    if not dashboard.is_active:
        abort(403)
    if not current_user.can_access_dashboard(dashboard_id):
        abort(403)

    # Track the view
    view = DashboardView.query.filter_by(
        user_id=current_user.id, dashboard_id=dashboard_id
    ).first()

    if view:
        view.last_viewed = datetime.utcnow()
        view.view_count  += 1
    else:
        view = DashboardView(user_id=current_user.id, dashboard_id=dashboard_id)
        db.session.add(view)

    db.session.commit()
    return render_template('portal/viewer.html', dashboard=dashboard)


@portal.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    error = None
    success = None

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'profile':
            email = request.form.get('email', '').strip() or None
            # Check uniqueness if email changed
            if email and email != current_user.email:
                from app.models import User
                if User.query.filter_by(email=email).first():
                    error = 'That email is already in use.'
            if not error:
                current_user.email = email
                db.session.commit()
                success = 'Profile updated.'

        elif action == 'password':
            current_pw = request.form.get('current_password', '')
            new_pw     = request.form.get('new_password', '').strip()
            confirm    = request.form.get('confirm_password', '').strip()

            if not current_user.check_password(current_pw):
                error = 'Current password is incorrect.'
            elif len(new_pw) < 8:
                error = 'New password must be at least 8 characters.'
            elif new_pw != confirm:
                error = 'Passwords do not match.'
            else:
                current_user.set_password(new_pw)
                db.session.commit()
                success = 'Password changed successfully.'

    return render_template('portal/settings.html', error=error, success=success)
