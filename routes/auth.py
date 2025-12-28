"""Authentication routes: login, register, logout."""
from flask import request, render_template, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from validation import validate_email, validate_username, validate_password, validate_name, sanitize_input
from db import create_user, get_user_by_username, get_user_by_email


def register_login_routes(app):
    """Register authentication routes with the Flask app."""
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        try:
            next_url = request.args.get('next') or request.form.get('next') or url_for('dashboard')
            if request.method == 'POST':
                username = sanitize_input(request.form.get('username') or '')
                password = request.form.get('password') or ''
                if not username or not password:
                    flash('Please enter both username and password', 'error')
                else:
                    try:
                        user = get_user_by_username(username)
                        if user and check_password_hash(user.get('password', ''), password):
                            session['user'] = user.get('username')
                            session['user_id'] = user.get('sr_no')
                            session.permanent = True
                            return redirect(next_url or url_for('dashboard'))
                        else:
                            flash('Invalid username or password', 'error')
                    except Exception as db_error:
                        # Log database connection errors
                        import sys
                        error_msg = f"Database error during login: {str(db_error)}"
                        print(error_msg, file=sys.stderr)
                        sys.stderr.flush()
                        flash('Database connection error. Please contact administrator.', 'error')
            # Render login template (for both GET and POST if login failed)
            return render_template('login.html', next=next_url)
        except Exception as e:
            import sys
            import traceback
            error_msg = f"ERROR: login route exception: {str(e)}\n"
            print(error_msg, file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
            return f"Login error: {e}", 500

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """User registration page."""
        try:
            next_url = request.args.get('next') or request.form.get('next') or url_for('dashboard')
            error = None
            
            if request.method == 'POST':
                email = sanitize_input(request.form.get('email') or '')
                name = sanitize_input(request.form.get('name') or '')
                username = sanitize_input(request.form.get('username') or '')
                password = request.form.get('password') or ''
                confirm = request.form.get('confirm') or ''
                
                # Validation
                if not all([email, name, username, password, confirm]):
                    error = 'All fields are required'
                elif password != confirm:
                    error = 'Passwords do not match'
                else:
                    # Validate inputs
                    email_valid, email_error = validate_email(email)
                    if not email_valid:
                        error = email_error or 'Invalid email address'
                    
                    name_valid, name_error = validate_name(name)
                    if not name_valid and not error:
                        error = name_error or 'Invalid name'
                    
                    username_valid, username_error = validate_username(username)
                    if not username_valid and not error:
                        error = username_error or 'Invalid username'
                    
                    password_valid, password_error = validate_password(password)
                    if not password_valid and not error:
                        error = password_error or 'Invalid password'
                
                if not error:
                    # Check if username or email already exists
                    existing_user = get_user_by_username(username)
                    if existing_user:
                        error = 'Username already exists'
                    else:
                        existing_email = get_user_by_email(email)
                        if existing_email:
                            error = 'Email already registered'
                        else:
                            # Create user
                            try:
                                # Hash the password before storing
                                password_hash = generate_password_hash(password)
                                user_id = create_user(
                                    username=username,
                                    email=email,
                                    password_hash=password_hash,
                                    name=name
                                )
                                if user_id:
                                    flash('Registration successful! Please log in.', 'success')
                                    return redirect(url_for('login', next=next_url))
                                else:
                                    error = 'Registration failed. Please try again.'
                            except Exception as db_error:
                                import sys
                                print(f"ERROR: Registration database error: {db_error}", file=sys.stderr)
                                error = 'Registration failed. Please try again.'
            
            return render_template('register.html', error=error, next=next_url)
        except Exception as e:
            import sys
            import traceback
            error_msg = f"ERROR: register route exception: {str(e)}\n"
            print(error_msg, file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
            return f"Registration error: {e}", 500

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('landing'))

