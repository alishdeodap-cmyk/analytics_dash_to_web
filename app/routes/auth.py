from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, LoginAudit
from app import db

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.home') if current_user.is_admin else url_for('portal.home'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user  = User.query.filter_by(username=username).first()
        audit = LoginAudit(username=username, ip_address=request.remote_addr, status='failed')

        if user and user.is_active and user.check_password(password):
            login_user(user)
            audit.user_id = user.id
            audit.status  = 'success'
            db.session.add(audit)
            db.session.commit()
            return redirect(url_for('admin.home') if user.is_admin else url_for('portal.home'))

        error = 'Invalid username or password.'
        db.session.add(audit)
        db.session.commit()

    return render_template('auth/login.html', error=error)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    is_forced = current_user.force_pw_change
    error = None
    success = None

    if request.method == 'POST':
        new_password = request.form.get('new_password', '').strip()
        confirm      = request.form.get('confirm_password', '').strip()

        # On voluntary change, also verify current password
        if not is_forced:
            current_pw = request.form.get('current_password', '')
            if not current_user.check_password(current_pw):
                error = 'Current password is incorrect.'

        if not error:
            if len(new_password) < 8:
                error = 'Password must be at least 8 characters.'
            elif new_password != confirm:
                error = 'Passwords do not match.'

        if not error:
            current_user.set_password(new_password)
            current_user.force_pw_change = False
            db.session.commit()
            if is_forced:
                flash('Password set successfully. Welcome!', 'success')
                return redirect(url_for('admin.home') if current_user.is_admin else url_for('portal.home'))
            success = 'Password changed successfully.'

    return render_template('auth/change_password.html', is_forced=is_forced, error=error, success=success)
