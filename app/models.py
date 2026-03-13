from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

# ── Many-to-many association tables ──────────────────────────────────────────

user_departments = db.Table(
    'user_departments',
    db.Column('user_id',       db.Integer, db.ForeignKey('users.id',       ondelete='CASCADE'), primary_key=True),
    db.Column('department_id', db.Integer, db.ForeignKey('departments.id', ondelete='CASCADE'), primary_key=True),
)

department_dashboards = db.Table(
    'department_dashboards',
    db.Column('dashboard_id',  db.Integer, db.ForeignKey('dashboards.id',  ondelete='CASCADE'), primary_key=True),
    db.Column('department_id', db.Integer, db.ForeignKey('departments.id', ondelete='CASCADE'), primary_key=True),
)


# ── Models ────────────────────────────────────────────────────────────────────

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id              = db.Column(db.Integer, primary_key=True)
    username        = db.Column(db.String(80),  unique=True, nullable=False)
    email           = db.Column(db.String(120), unique=True)
    password_hash   = db.Column(db.String(255), nullable=False)
    role            = db.Column(db.Enum('admin', 'user'), nullable=False, default='user')
    is_active       = db.Column(db.Boolean, default=True, nullable=False)
    force_pw_change = db.Column(db.Boolean, default=True, nullable=False)
    created_by      = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    departments     = db.relationship('Department', secondary=user_departments, back_populates='users', lazy='select')
    dashboard_views = db.relationship('DashboardView', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    def get_accessible_dashboards(self):
        """Return all active dashboards this user can view."""
        if self.is_admin:
            return Dashboard.query.filter_by(is_active=True).all()
        dept_ids = [d.id for d in self.departments]
        if not dept_ids:
            return []
        return (
            Dashboard.query
            .join(department_dashboards, Dashboard.id == department_dashboards.c.dashboard_id)
            .filter(
                department_dashboards.c.department_id.in_(dept_ids),
                Dashboard.is_active == True
            )
            .distinct()
            .all()
        )

    def can_access_dashboard(self, dashboard_id):
        """Check if user has permission to view a specific dashboard."""
        if self.is_admin:
            return True
        return any(d.id == dashboard_id for d in self.get_accessible_dashboards())


class Department(db.Model):
    __tablename__ = 'departments'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    parent_id   = db.Column(db.Integer, db.ForeignKey('departments.id', ondelete='SET NULL'))
    description = db.Column(db.Text)
    is_active   = db.Column(db.Boolean, default=True, nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    users      = db.relationship('User', secondary=user_departments, back_populates='departments', lazy='select')
    dashboards = db.relationship('Dashboard', secondary=department_dashboards, back_populates='departments', lazy='select')
    children   = db.relationship('Department', backref=db.backref('parent', remote_side='Department.id'), lazy='select')


class Dashboard(db.Model):
    __tablename__ = 'dashboards'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    embed_src   = db.Column(db.Text, nullable=False)
    embed_title = db.Column(db.String(200))
    iframe_raw  = db.Column(db.Text)
    is_active   = db.Column(db.Boolean, default=True, nullable=False)
    created_by  = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    departments = db.relationship('Department', secondary=department_dashboards, back_populates='dashboards', lazy='select')
    views       = db.relationship('DashboardView', backref='dashboard', lazy='dynamic', cascade='all, delete-orphan')
    creator     = db.relationship('User', foreign_keys=[created_by])


class DashboardView(db.Model):
    __tablename__ = 'dashboard_views'

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id',      ondelete='CASCADE'), nullable=False)
    dashboard_id = db.Column(db.Integer, db.ForeignKey('dashboards.id', ondelete='CASCADE'), nullable=False)
    last_viewed  = db.Column(db.DateTime, default=datetime.utcnow)
    view_count   = db.Column(db.Integer, default=1, nullable=False)

    __table_args__ = (db.UniqueConstraint('user_id', 'dashboard_id', name='uq_user_dash'),)


class LoginAudit(db.Model):
    __tablename__ = 'login_audit'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    username   = db.Column(db.String(80))
    ip_address = db.Column(db.String(45))
    status     = db.Column(db.Enum('success', 'failed'), nullable=False)
    logged_at  = db.Column(db.DateTime, default=datetime.utcnow)
