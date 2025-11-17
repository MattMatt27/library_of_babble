"""
Authentication Routes
"""
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from app.auth import auth_bp
from app.extensions import db, login_manager
from app.auth.models import User


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))


@auth_bp.route('/check_login')
def check_login():
    """Check if user is logged in (API endpoint)"""
    if current_user.is_authenticated:
        return jsonify({
            'logged_in': True,
            'username': current_user.username,
            'role': current_user.role
        })
    return jsonify({'logged_in': False})


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.home'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    """User logout"""
    logout_user()
    return redirect(url_for('main.home'))


@auth_bp.route('/users/create', methods=['POST'])
@login_required
def create_user():
    """Create a new user (admin-only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403

    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role', 'user')

    if not username or not password:
        flash('Username and password are required', 'error')
        return redirect(url_for('account.index'))

    # Check if user already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash(f'User "{username}" already exists', 'error')
        return redirect(url_for('account.index'))

    # Create new user
    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password=hashed_password, role=role)

    db.session.add(new_user)
    db.session.commit()

    flash(f'User "{username}" created successfully', 'success')
    return redirect(url_for('account.index'))


@auth_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    """Delete a user (admin-only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403

    user = User.query.get_or_404(user_id)

    # Prevent deleting yourself
    if user.id == current_user.id:
        flash('You cannot delete your own account', 'error')
        return redirect(url_for('account.index'))

    username = user.username
    db.session.delete(user)
    db.session.commit()

    flash(f'User "{username}" deleted successfully', 'success')
    return redirect(url_for('account.index'))


@auth_bp.route('/users/<int:user_id>/change_password', methods=['POST'])
@login_required
def change_password(user_id):
    """Change user password (admin-only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403

    user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password')

    if not new_password:
        flash('Password is required', 'error')
        return redirect(url_for('account.index'))

    user.password = generate_password_hash(new_password)
    db.session.commit()

    flash(f'Password updated for user "{user.username}"', 'success')
    return redirect(url_for('account.index'))


@auth_bp.route('/users/<int:user_id>/change_role', methods=['POST'])
@login_required
def change_role(user_id):
    """Change user role (admin-only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403

    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')

    if not new_role:
        flash('Role is required', 'error')
        return redirect(url_for('account.index'))

    user.role = new_role
    db.session.commit()

    flash(f'Role updated for user "{user.username}" to "{new_role}"', 'success')
    return redirect(url_for('account.index'))
