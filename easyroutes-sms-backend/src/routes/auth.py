from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta
import os
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def require_auth(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check session timeout
        login_time = session.get('login_time')
        if login_time:
            login_datetime = datetime.fromisoformat(login_time)
            timeout_minutes = int(os.getenv('SESSION_TIMEOUT', 60))
            if datetime.now() - login_datetime > timedelta(minutes=timeout_minutes):
                session.clear()
                return jsonify({'error': 'Session expired'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    """Authenticate user with password"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        password = data.get('password')
        if not password:
            return jsonify({'error': 'Password is required'}), 400
        
        # Check against configured admin password
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        
        if password == admin_password:
            session['authenticated'] = True
            session['login_time'] = datetime.now().isoformat()
            session.permanent = True
            
            return jsonify({
                'success': True,
                'message': 'Login successful'
            })
        else:
            return jsonify({'error': 'Invalid password'}), 401
            
    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@auth_bp.route('/auth/logout', methods=['POST'])
def logout():
    """Clear user session"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@auth_bp.route('/auth/status', methods=['GET'])
def auth_status():
    """Check authentication status"""
    authenticated = session.get('authenticated', False)
    
    if authenticated:
        login_time = session.get('login_time')
        if login_time:
            login_datetime = datetime.fromisoformat(login_time)
            timeout_minutes = int(os.getenv('SESSION_TIMEOUT', 60))
            if datetime.now() - login_datetime > timedelta(minutes=timeout_minutes):
                session.clear()
                authenticated = False
    
    return jsonify({
        'authenticated': authenticated,
        'login_time': session.get('login_time') if authenticated else None
    })

@auth_bp.route('/auth/test', methods=['GET'])
@require_auth
def test_auth():
    """Test endpoint to verify authentication is working"""
    return jsonify({
        'success': True,
        'message': 'Authentication is working',
        'login_time': session.get('login_time')
    })

