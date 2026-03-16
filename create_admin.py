"""Run this once on the server to create the first admin user."""
from app import create_app
from app.models import db, User

app = create_app()
with app.app_context():
    username = input("Admin username: ").strip()
    password = input("Admin password: ").strip()
    email    = input("Admin email (optional): ").strip() or None

    if User.query.filter_by(username=username).first():
        print(f"User '{username}' already exists.")
    else:
        u = User(username=username, email=email, role='admin',
                 is_active=True, force_pw_change=False)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        print(f"Admin user '{username}' created successfully.")
