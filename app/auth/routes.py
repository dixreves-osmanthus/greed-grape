from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User
from app.auth.forms import LoginForm, RegistrationForm

from app.auth import auth


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            
            # Redirect to next page or home
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            if user.is_admin:
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('main.index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('auth/login.html', form=form)


@auth.route('/register', methods=['GET', 'POST'])
def register():
    """User registration."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # Check if email already exists
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already registered', 'error')
            return render_template('auth/register.html', form=form)
        
        # Check if username already exists
        existing_username = User.query.filter_by(username=form.username.data).first()
        if existing_username:
            flash('Username already taken', 'error')
            return render_template('auth/register.html', form=form)
        
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            is_admin=False
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    """User logout."""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('main.index'))


@auth.route('/profile')
@login_required
def profile():
    """User profile."""
    return render_template('auth/profile.html', user=current_user)
