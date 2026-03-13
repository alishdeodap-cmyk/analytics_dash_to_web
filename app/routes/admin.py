from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from app.models import User, Department, Dashboard, DashboardView, LoginAudit
from app.utils import parse_iframe
from app import db

admin = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


# ── HOME ─────────────────────────────────────────────────────────────────────

@admin.route('/')
@login_required
@admin_required
def home():
    stats = {
        'users':      User.query.filter_by(role='user', is_active=True).count(),
        'departments': Department.query.filter_by(is_active=True).count(),
        'dashboards': Dashboard.query.filter_by(is_active=True).count(),
    }
    recent_views = (
        DashboardView.query
        .order_by(DashboardView.last_viewed.desc())
        .limit(10).all()
    )
    recent_logins = (
        LoginAudit.query
        .order_by(LoginAudit.logged_at.desc())
        .limit(8).all()
    )
    return render_template('admin/home.html',
                           stats=stats,
                           recent_views=recent_views,
                           recent_logins=recent_logins)


# ── DASHBOARDS ───────────────────────────────────────────────────────────────

@admin.route('/dashboards')
@login_required
@admin_required
def dashboards():
    q = request.args.get('q', '').strip()
    query = Dashboard.query
    if q:
        query = query.filter(Dashboard.name.ilike(f'%{q}%'))
    all_dash = query.order_by(Dashboard.created_at.desc()).all()
    return render_template('admin/dashboards.html', dashboards=all_dash, q=q)


@admin.route('/dashboards/new', methods=['GET', 'POST'])
@login_required
@admin_required
def dashboard_new():
    departments = Department.query.filter_by(is_active=True).order_by(Department.name).all()
    error = None

    if request.method == 'POST':
        name        = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        iframe_raw  = request.form.get('iframe_raw', '').strip()
        dept_ids    = request.form.getlist('department_ids')

        if not name or not iframe_raw:
            error = 'Dashboard name and iframe code are required.'
        else:
            parsed = parse_iframe(iframe_raw)
            if not parsed:
                error = 'Could not parse iframe. Please paste valid Power BI embed code.'
            elif not parsed['src'].startswith('https://app.powerbi.com/'):
                error = 'Only Power BI embed URLs (https://app.powerbi.com/) are allowed.'
            else:
                dash = Dashboard(
                    name        = name,
                    description = description,
                    embed_src   = parsed['src'],
                    embed_title = parsed['title'] or name,
                    iframe_raw  = iframe_raw,
                    created_by  = current_user.id,
                )
                for dept_id in dept_ids:
                    dept = Department.query.get(int(dept_id))
                    if dept:
                        dash.departments.append(dept)
                db.session.add(dash)
                db.session.commit()
                flash(f"Dashboard '{name}' added successfully.", 'success')
                return redirect(url_for('admin.dashboards'))

    return render_template('admin/dashboard_form.html',
                           departments=departments, error=error, dashboard=None)


@admin.route('/dashboards/<int:dashboard_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def dashboard_edit(dashboard_id):
    dashboard   = Dashboard.query.get_or_404(dashboard_id)
    departments = Department.query.filter_by(is_active=True).order_by(Department.name).all()
    error = None

    if request.method == 'POST':
        name        = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        iframe_raw  = request.form.get('iframe_raw', '').strip()
        dept_ids    = request.form.getlist('department_ids')

        if not name or not iframe_raw:
            error = 'Dashboard name and iframe code are required.'
        else:
            parsed = parse_iframe(iframe_raw)
            if not parsed:
                error = 'Could not parse iframe.'
            elif not parsed['src'].startswith('https://app.powerbi.com/'):
                error = 'Only Power BI embed URLs are allowed.'
            else:
                dashboard.name        = name
                dashboard.description = description
                dashboard.embed_src   = parsed['src']
                dashboard.embed_title = parsed['title'] or name
                dashboard.iframe_raw  = iframe_raw
                dashboard.departments = []
                for dept_id in dept_ids:
                    dept = Department.query.get(int(dept_id))
                    if dept:
                        dashboard.departments.append(dept)
                db.session.commit()
                flash(f"Dashboard '{name}' updated.", 'success')
                return redirect(url_for('admin.dashboards'))

    return render_template('admin/dashboard_form.html',
                           departments=departments, error=error, dashboard=dashboard)


@admin.route('/dashboards/<int:dashboard_id>/toggle', methods=['POST'])
@login_required
@admin_required
def dashboard_toggle(dashboard_id):
    dashboard = Dashboard.query.get_or_404(dashboard_id)
    dashboard.is_active = not dashboard.is_active
    db.session.commit()
    status = 'activated' if dashboard.is_active else 'deactivated'
    flash(f"Dashboard '{dashboard.name}' {status}.", 'success')
    return redirect(url_for('admin.dashboards'))


@admin.route('/dashboards/<int:dashboard_id>/delete', methods=['POST'])
@login_required
@admin_required
def dashboard_delete(dashboard_id):
    dashboard = Dashboard.query.get_or_404(dashboard_id)
    name = dashboard.name
    db.session.delete(dashboard)
    db.session.commit()
    flash(f"Dashboard '{name}' deleted.", 'success')
    return redirect(url_for('admin.dashboards'))


# ── DEPARTMENTS ───────────────────────────────────────────────────────────────

@admin.route('/departments')
@login_required
@admin_required
def departments():
    top_level = (
        Department.query
        .filter_by(parent_id=None)
        .order_by(Department.name)
        .all()
    )
    return render_template('admin/departments.html', departments=top_level)


@admin.route('/departments/new', methods=['GET', 'POST'])
@login_required
@admin_required
def department_new():
    parent_depts = Department.query.filter_by(parent_id=None, is_active=True).order_by(Department.name).all()
    error = None

    if request.method == 'POST':
        name        = request.form.get('name', '').strip()
        parent_id   = request.form.get('parent_id') or None
        description = request.form.get('description', '').strip()

        if not name:
            error = 'Department name is required.'
        else:
            dept = Department(name=name, parent_id=parent_id, description=description)
            db.session.add(dept)
            db.session.commit()
            flash(f"Department '{name}' created.", 'success')
            return redirect(url_for('admin.departments'))

    return render_template('admin/department_form.html',
                           parent_depts=parent_depts, error=error, department=None)


@admin.route('/departments/<int:dept_id>')
@login_required
@admin_required
def department_detail(dept_id):
    dept          = Department.query.get_or_404(dept_id)
    all_users     = User.query.filter_by(is_active=True).order_by(User.username).all()
    all_dashboards = Dashboard.query.filter_by(is_active=True).order_by(Dashboard.name).all()
    return render_template('admin/department_detail.html',
                           dept=dept,
                           all_users=all_users,
                           all_dashboards=all_dashboards)


@admin.route('/departments/<int:dept_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def department_edit(dept_id):
    dept = Department.query.get_or_404(dept_id)
    parent_depts = (
        Department.query
        .filter(Department.parent_id == None, Department.id != dept_id, Department.is_active == True)
        .order_by(Department.name)
        .all()
    )
    error = None

    if request.method == 'POST':
        name        = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        parent_id   = request.form.get('parent_id') or None

        if not name:
            error = 'Department name is required.'
        else:
            dept.name        = name
            dept.description = description
            dept.parent_id   = parent_id
            db.session.commit()
            flash('Department updated.', 'success')
            return redirect(url_for('admin.departments'))

    return render_template('admin/department_form.html',
                           parent_depts=parent_depts, error=error, department=dept)


@admin.route('/departments/<int:dept_id>/delete', methods=['POST'])
@login_required
@admin_required
def department_delete(dept_id):
    dept = Department.query.get_or_404(dept_id)
    name = dept.name
    db.session.delete(dept)
    db.session.commit()
    flash(f"Department '{name}' deleted.", 'success')
    return redirect(url_for('admin.departments'))


@admin.route('/departments/<int:dept_id>/add-user', methods=['POST'])
@login_required
@admin_required
def department_add_user(dept_id):
    dept    = Department.query.get_or_404(dept_id)
    user_id = request.form.get('user_id', type=int)
    user    = User.query.get_or_404(user_id)
    if user not in dept.users:
        dept.users.append(user)
        db.session.commit()
        flash(f"User '{user.username}' added to {dept.name}.", 'success')
    else:
        flash(f"User '{user.username}' is already in {dept.name}.", 'error')
    return redirect(url_for('admin.department_detail', dept_id=dept_id))


@admin.route('/departments/<int:dept_id>/remove-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def department_remove_user(dept_id, user_id):
    dept = Department.query.get_or_404(dept_id)
    user = User.query.get_or_404(user_id)
    if user in dept.users:
        dept.users.remove(user)
        db.session.commit()
        flash(f"User '{user.username}' removed from {dept.name}.", 'success')
    return redirect(url_for('admin.department_detail', dept_id=dept_id))


@admin.route('/departments/<int:dept_id>/add-dashboard', methods=['POST'])
@login_required
@admin_required
def department_add_dashboard(dept_id):
    dept         = Department.query.get_or_404(dept_id)
    dashboard_id = request.form.get('dashboard_id', type=int)
    dashboard    = Dashboard.query.get_or_404(dashboard_id)
    if dashboard not in dept.dashboards:
        dept.dashboards.append(dashboard)
        db.session.commit()
        flash(f"Dashboard '{dashboard.name}' assigned to {dept.name}.", 'success')
    else:
        flash('Dashboard already assigned to this department.', 'error')
    return redirect(url_for('admin.department_detail', dept_id=dept_id))


@admin.route('/departments/<int:dept_id>/remove-dashboard/<int:dashboard_id>', methods=['POST'])
@login_required
@admin_required
def department_remove_dashboard(dept_id, dashboard_id):
    dept      = Department.query.get_or_404(dept_id)
    dashboard = Dashboard.query.get_or_404(dashboard_id)
    if dashboard in dept.dashboards:
        dept.dashboards.remove(dashboard)
        db.session.commit()
        flash(f"Dashboard '{dashboard.name}' removed from {dept.name}.", 'success')
    return redirect(url_for('admin.department_detail', dept_id=dept_id))


# ── USERS ─────────────────────────────────────────────────────────────────────

@admin.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)


@admin.route('/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def user_new():
    departments = Department.query.filter_by(is_active=True).order_by(Department.name).all()
    error = None

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip() or None
        password = request.form.get('password', '').strip()
        role     = request.form.get('role', 'user')
        dept_ids = request.form.getlist('department_ids')

        if not username or not password:
            error = 'Username and password are required.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        elif User.query.filter_by(username=username).first():
            error = f"Username '{username}' is already taken."
        elif email and User.query.filter_by(email=email).first():
            error = 'That email is already registered.'
        else:
            user = User(
                username        = username,
                email           = email,
                role            = role,
                force_pw_change = True,
                created_by      = current_user.id,
            )
            user.set_password(password)
            for dept_id in dept_ids:
                dept = Department.query.get(int(dept_id))
                if dept:
                    user.departments.append(dept)
            db.session.add(user)
            db.session.commit()
            flash(f"User '{username}' created. They will be prompted to change password on first login.", 'success')
            return redirect(url_for('admin.users'))

    return render_template('admin/user_form.html',
                           departments=departments, error=error, user_obj=None)


@admin.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def user_edit(user_id):
    user_obj    = User.query.get_or_404(user_id)
    departments = Department.query.filter_by(is_active=True).order_by(Department.name).all()
    error = None

    if request.method == 'POST':
        email    = request.form.get('email', '').strip() or None
        role     = request.form.get('role', 'user')
        dept_ids = request.form.getlist('department_ids')

        if email and email != user_obj.email and User.query.filter_by(email=email).first():
            error = 'That email is already registered.'
        else:
            user_obj.email        = email
            user_obj.role         = role
            user_obj.departments  = []
            for dept_id in dept_ids:
                dept = Department.query.get(int(dept_id))
                if dept:
                    user_obj.departments.append(dept)
            db.session.commit()
            flash(f"User '{user_obj.username}' updated.", 'success')
            return redirect(url_for('admin.users'))

    return render_template('admin/user_form.html',
                           departments=departments, error=error, user_obj=user_obj)


@admin.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def user_reset_password(user_id):
    user_obj = User.query.get_or_404(user_id)
    new_pw   = request.form.get('new_password', '').strip()
    if len(new_pw) < 6:
        flash('Password must be at least 6 characters.', 'error')
    else:
        user_obj.set_password(new_pw)
        user_obj.force_pw_change = True
        db.session.commit()
        flash(f"Password reset for '{user_obj.username}'. They must change it on next login.", 'success')
    return redirect(url_for('admin.users'))


@admin.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def user_toggle(user_id):
    user_obj = User.query.get_or_404(user_id)
    if user_obj.id == current_user.id:
        flash('You cannot deactivate your own account.', 'error')
    else:
        user_obj.is_active = not user_obj.is_active
        db.session.commit()
        status = 'activated' if user_obj.is_active else 'deactivated'
        flash(f"User '{user_obj.username}' {status}.", 'success')
    return redirect(url_for('admin.users'))
