# EasyRoutes SMS Tool - Web Application Specifications

**Author:** Manus AI  
**Date:** July 24, 2025  
**Version:** 2.0 (Web Application)

## Application Overview

The EasyRoutes SMS Tool is now designed as a modern web application that provides a simple, secure interface for sending SMS notifications to incomplete delivery stops. The application features a clean user interface with password authentication and real-time feedback.

## Technical Architecture

### Frontend Architecture
- **Framework**: React with modern hooks and functional components
- **Styling**: Tailwind CSS for responsive, utility-first styling
- **Icons**: Lucide React for consistent iconography
- **State Management**: React hooks (useState, useEffect, useContext)
- **HTTP Client**: Fetch API with error handling and loading states

### Backend Architecture
- **Framework**: Flask (Python) with Blueprint organization
- **Authentication**: Session-based authentication with secure cookies
- **API Integration**: Async HTTP clients for EasyRoutes and Twilio APIs
- **Security**: CSRF protection, input validation, rate limiting
- **Configuration**: Environment-based configuration management

## Application Components

### 1. Authentication System

#### Login Component (React)
```jsx
const LoginForm = () => {
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password })
      });
      
      if (response.ok) {
        window.location.href = '/dashboard';
      } else {
        setError('Invalid password');
      }
    } catch (err) {
      setError('Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Enter password"
        className="w-full px-4 py-2 border rounded-lg"
        required
      />
      <button
        type="submit"
        disabled={loading}
        className="w-full bg-blue-600 text-white py-2 rounded-lg"
      >
        {loading ? 'Logging in...' : 'Login'}
      </button>
      {error && <p className="text-red-500">{error}</p>}
    </form>
  );
};
```

#### Authentication Backend (Flask)
```python
from flask import Blueprint, request, session, jsonify
from werkzeug.security import check_password_hash
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    password = data.get('password')
    
    # Check against configured admin password
    admin_password = os.getenv('ADMIN_PASSWORD')
    
    if password == admin_password:
        session['authenticated'] = True
        session['login_time'] = datetime.now().isoformat()
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Invalid password'}), 401

@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

def require_auth(f):
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function
```

### 2. Main SMS Interface

#### SMS Form Component (React)
```jsx
const SMSForm = () => {
  const [routeNumber, setRouteNumber] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch('/api/sms/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          route_number: routeNumber,
          message: message
        })
      });

      const data = await response.json();
      
      if (response.ok) {
        setResults(data);
      } else {
        setError(data.error || 'Failed to send messages');
      }
    } catch (err) {
      setError('Network error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">EasyRoutes SMS Tool</h1>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">
            Route Number
          </label>
          <input
            type="text"
            value={routeNumber}
            onChange={(e) => setRouteNumber(e.target.value)}
            placeholder="Enter route number (e.g., RT-12345)"
            className="w-full px-4 py-2 border rounded-lg"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">
            Custom Message
          </label>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Enter your custom message..."
            rows={4}
            maxLength={160}
            className="w-full px-4 py-2 border rounded-lg"
            required
          />
          <p className="text-sm text-gray-500 mt-1">
            {message.length}/160 characters
          </p>
        </div>

        <button
          type="submit"
          disabled={loading || !routeNumber || !message}
          className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium disabled:bg-gray-400"
        >
          {loading ? (
            <span className="flex items-center justify-center">
              <Loader className="animate-spin mr-2" size={20} />
              Sending Messages...
            </span>
          ) : (
            'Send SMS Messages'
          )}
        </button>
      </form>

      {error && (
        <div className="mt-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
          {error}
        </div>
      )}

      {results && <ResultsDisplay results={results} />}
    </div>
  );
};
```

#### SMS Backend Handler (Flask)
```python
from flask import Blueprint, request, jsonify
from .auth import require_auth
from .api_clients import EasyRoutesClient, TwilioClient
import asyncio

sms_bp = Blueprint('sms', __name__)

@sms_bp.route('/api/sms/send', methods=['POST'])
@require_auth
async def send_sms():
    try:
        data = request.get_json()
        route_number = data.get('route_number')
        message = data.get('message')
        
        # Validate inputs
        if not route_number or not message:
            return jsonify({'error': 'Route number and message are required'}), 400
        
        if len(message) > 160:
            return jsonify({'error': 'Message too long (max 160 characters)'}), 400
        
        # Initialize API clients
        easyroutes = EasyRoutesClient()
        twilio = TwilioClient()
        
        # Get route and incomplete stops
        route = await easyroutes.get_route_by_number(route_number)
        if not route:
            return jsonify({'error': f'Route {route_number} not found'}), 404
        
        incomplete_stops = await easyroutes.get_incomplete_stops(route['id'])
        
        if not incomplete_stops:
            return jsonify({
                'success': True,
                'message': 'No incomplete stops found for this route',
                'results': {
                    'total_stops': 0,
                    'messages_sent': 0,
                    'failures': 0,
                    'details': []
                }
            })
        
        # Send SMS messages
        results = await send_messages_to_stops(twilio, incomplete_stops, message)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

async def send_messages_to_stops(twilio_client, stops, message):
    results = {
        'total_stops': len(stops),
        'messages_sent': 0,
        'failures': 0,
        'details': []
    }
    
    for stop in stops:
        phone_number = stop.get('contact', {}).get('phone')
        if not phone_number:
            results['details'].append({
                'stop_id': stop['id'],
                'status': 'failed',
                'error': 'No phone number',
                'phone': None
            })
            results['failures'] += 1
            continue
        
        try:
            sms_result = await twilio_client.send_message(phone_number, message)
            
            if sms_result['success']:
                results['details'].append({
                    'stop_id': stop['id'],
                    'status': 'sent',
                    'phone': phone_number[-4:],  # Last 4 digits only
                    'message_sid': sms_result['message_sid']
                })
                results['messages_sent'] += 1
            else:
                results['details'].append({
                    'stop_id': stop['id'],
                    'status': 'failed',
                    'error': sms_result['error'],
                    'phone': phone_number[-4:]
                })
                results['failures'] += 1
                
        except Exception as e:
            results['details'].append({
                'stop_id': stop['id'],
                'status': 'failed',
                'error': str(e),
                'phone': phone_number[-4:]
            })
            results['failures'] += 1
    
    return results
```

### 3. Results Display Component

```jsx
const ResultsDisplay = ({ results }) => {
  const { total_stops, messages_sent, failures, details } = results;
  
  return (
    <div className="mt-8 p-6 bg-gray-50 rounded-lg">
      <h2 className="text-xl font-bold mb-4">SMS Delivery Results</h2>
      
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="text-center p-4 bg-blue-100 rounded-lg">
          <div className="text-2xl font-bold text-blue-600">{total_stops}</div>
          <div className="text-sm text-blue-800">Total Stops</div>
        </div>
        <div className="text-center p-4 bg-green-100 rounded-lg">
          <div className="text-2xl font-bold text-green-600">{messages_sent}</div>
          <div className="text-sm text-green-800">Messages Sent</div>
        </div>
        <div className="text-center p-4 bg-red-100 rounded-lg">
          <div className="text-2xl font-bold text-red-600">{failures}</div>
          <div className="text-sm text-red-800">Failures</div>
        </div>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full border-collapse border border-gray-300">
          <thead>
            <tr className="bg-gray-200">
              <th className="border border-gray-300 px-4 py-2">Stop ID</th>
              <th className="border border-gray-300 px-4 py-2">Status</th>
              <th className="border border-gray-300 px-4 py-2">Phone</th>
              <th className="border border-gray-300 px-4 py-2">Details</th>
            </tr>
          </thead>
          <tbody>
            {details.map((detail, index) => (
              <tr key={index}>
                <td className="border border-gray-300 px-4 py-2">{detail.stop_id}</td>
                <td className="border border-gray-300 px-4 py-2">
                  <span className={`px-2 py-1 rounded text-sm ${
                    detail.status === 'sent' 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {detail.status === 'sent' ? '✅ Sent' : '❌ Failed'}
                  </span>
                </td>
                <td className="border border-gray-300 px-4 py-2">
                  {detail.phone ? `***${detail.phone}` : 'N/A'}
                </td>
                <td className="border border-gray-300 px-4 py-2">
                  {detail.error || detail.message_sid || 'Success'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      <div className="mt-4 flex space-x-4">
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg"
        >
          Send Another
        </button>
        <button
          onClick={() => exportResults(results)}
          className="px-4 py-2 bg-gray-600 text-white rounded-lg"
        >
          Export Results
        </button>
      </div>
    </div>
  );
};
```

## Project Structure (Updated)

```
easyroutes-sms-tool/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   └── sms.py
│   │   ├── clients/
│   │   │   ├── __init__.py
│   │   │   ├── easyroutes.py
│   │   │   └── twilio_client.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── validators.py
│   ├── config.py
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── public/
│   │   ├── index.html
│   │   └── favicon.ico
│   ├── src/
│   │   ├── components/
│   │   │   ├── LoginForm.jsx
│   │   │   ├── SMSForm.jsx
│   │   │   └── ResultsDisplay.jsx
│   │   ├── App.jsx
│   │   └── index.js
│   ├── package.json
│   └── tailwind.config.js
├── docs/
│   ├── web_interface_design.md
│   └── deployment_guide.md
├── .env.example
├── README.md
└── docker-compose.yml
```

## Environment Configuration

### Updated .env.example
```bash
# Authentication
ADMIN_PASSWORD=your_secure_admin_password_here
FLASK_SECRET_KEY=your_flask_secret_key_here
SESSION_TIMEOUT=3600

# EasyRoutes API
EASYROUTES_CLIENT_ID=your_easyroutes_client_id_here
EASYROUTES_CLIENT_SECRET=your_easyroutes_client_secret_here

# Twilio SMS
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_FROM_NUMBER=+1234567890

# Application Settings
FLASK_ENV=production
DEBUG=false
MAX_MESSAGE_LENGTH=160
RATE_LIMIT_PER_MINUTE=10

# Security
CSRF_ENABLED=true
SECURE_COOKIES=true
```

## Deployment Configuration

### Docker Compose Setup
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
```

## Security Features

### Input Validation
- Route number format validation
- Message length limits (160 characters)
- XSS prevention through output encoding
- CSRF token validation

### Authentication Security
- Secure session management
- Password-based access control
- Session timeout handling
- Rate limiting for login attempts

### Data Protection
- Phone numbers partially masked in results
- No sensitive data in logs
- HTTPS enforcement in production
- Secure cookie configuration

## Testing Strategy

### Frontend Testing
```javascript
// LoginForm.test.jsx
import { render, screen, fireEvent } from '@testing-library/react';
import LoginForm from './LoginForm';

test('submits login form with password', async () => {
  render(<LoginForm />);
  
  const passwordInput = screen.getByPlaceholderText('Enter password');
  const submitButton = screen.getByText('Login');
  
  fireEvent.change(passwordInput, { target: { value: 'testpassword' } });
  fireEvent.click(submitButton);
  
  // Assert API call was made
});
```

### Backend Testing
```python
# test_sms_routes.py
import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app(testing=True)
    with app.test_client() as client:
        yield client

def test_send_sms_requires_auth(client):
    response = client.post('/api/sms/send', json={
        'route_number': 'RT-123',
        'message': 'Test message'
    })
    assert response.status_code == 401

def test_send_sms_with_valid_data(client):
    # Login first
    client.post('/api/auth/login', json={'password': 'testpass'})
    
    response = client.post('/api/sms/send', json={
        'route_number': 'RT-123',
        'message': 'Test message'
    })
    assert response.status_code == 200
```

This web-based approach provides a much more user-friendly interface while maintaining all the core functionality of the original command-line tool.

