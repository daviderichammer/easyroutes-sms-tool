from flask import Blueprint, request, jsonify
from src.routes.auth import require_auth
from src.clients.easyroutes import EasyRoutesClient, run_async
from src.clients.twilio_client import TwilioSMSClient
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

sms_bp = Blueprint('sms', __name__)

@sms_bp.route('/sms/send', methods=['POST'])
@require_auth
def send_sms():
    """Send SMS messages to incomplete stops on a route"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        route_number = data.get('route_number', '').strip()
        message = data.get('message', '').strip()
        
        # Validate inputs
        if not route_number:
            return jsonify({'error': 'Route number is required'}), 400
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        if len(message) > 160:
            return jsonify({'error': 'Message too long (max 160 characters)'}), 400
        
        logger.info(f"Processing SMS request for route: {route_number}")
        
        # Initialize API clients
        try:
            easyroutes = EasyRoutesClient()
            twilio = TwilioSMSClient()
        except Exception as e:
            logger.error(f"Failed to initialize API clients: {str(e)}")
            return jsonify({'error': f'Configuration error: {str(e)}'}), 500
        
        # Get route and incomplete stops
        try:
            route = run_async(easyroutes.get_route_by_number(route_number))
            if not route:
                return jsonify({'error': f'Route "{route_number}" not found'}), 404
            
            incomplete_stops = run_async(easyroutes.get_incomplete_stops(route['id']))
            
            if not incomplete_stops:
                return jsonify({
                    'success': True,
                    'message': 'No incomplete stops found for this route',
                    'results': {
                        'route_id': route['id'],
                        'route_name': route.get('name', route_number),
                        'total_stops': len(route.get('stops', [])),
                        'incomplete_stops': 0,
                        'messages_sent': 0,
                        'failures': 0,
                        'details': []
                    }
                })
            
        except Exception as e:
            logger.error(f"Error retrieving route data: {str(e)}")
            return jsonify({'error': f'Failed to retrieve route data: {str(e)}'}), 500
        
        # Send SMS messages
        try:
            results = send_messages_to_stops(twilio, incomplete_stops, message)
            results['route_id'] = route['id']
            results['route_name'] = route.get('name', route_number)
            results['total_stops'] = len(route.get('stops', []))
            results['incomplete_stops'] = len(incomplete_stops)
            
            logger.info(f"SMS sending completed for route {route_number}: {results['messages_sent']} sent, {results['failures']} failed")
            
            return jsonify({
                'success': True,
                'results': results
            })
            
        except Exception as e:
            logger.error(f"Error sending SMS messages: {str(e)}")
            return jsonify({'error': f'Failed to send SMS messages: {str(e)}'}), 500
        
    except Exception as e:
        logger.error(f"Unexpected error in send_sms: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

def send_messages_to_stops(twilio_client: TwilioSMSClient, stops: list, message: str) -> dict:
    """Send SMS messages to all stops and return results"""
    results = {
        'messages_sent': 0,
        'failures': 0,
        'details': [],
        'timestamp': datetime.now().isoformat()
    }
    
    for stop in stops:
        stop_id = stop.get('id', 'Unknown')
        contact = stop.get('contact', {})
        phone_number = contact.get('phone', '').strip()
        customer_name = contact.get('name', 'Customer')
        
        if not phone_number:
            results['details'].append({
                'stop_id': stop_id,
                'customer_name': customer_name,
                'status': 'failed',
                'error': 'No phone number provided',
                'phone': None
            })
            results['failures'] += 1
            continue
        
        try:
            # Send SMS message
            sms_result = twilio_client.send_message_sync(phone_number, message)
            
            if sms_result['success']:
                results['details'].append({
                    'stop_id': stop_id,
                    'customer_name': customer_name,
                    'status': 'sent',
                    'phone': f"***{phone_number[-4:]}" if len(phone_number) >= 4 else "***",
                    'message_sid': sms_result['message_sid']
                })
                results['messages_sent'] += 1
            else:
                results['details'].append({
                    'stop_id': stop_id,
                    'customer_name': customer_name,
                    'status': 'failed',
                    'error': sms_result['error'],
                    'phone': f"***{phone_number[-4:]}" if len(phone_number) >= 4 else "***"
                })
                results['failures'] += 1
                
        except Exception as e:
            logger.error(f"Error sending SMS to stop {stop_id}: {str(e)}")
            results['details'].append({
                'stop_id': stop_id,
                'customer_name': customer_name,
                'status': 'failed',
                'error': f'Unexpected error: {str(e)}',
                'phone': f"***{phone_number[-4:]}" if len(phone_number) >= 4 else "***"
            })
            results['failures'] += 1
    
    return results

@sms_bp.route('/sms/preview', methods=['POST'])
@require_auth
def preview_sms():
    """Preview which stops would receive SMS messages without actually sending"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        route_number = data.get('route_number', '').strip()
        
        if not route_number:
            return jsonify({'error': 'Route number is required'}), 400
        
        # Initialize EasyRoutes client
        try:
            easyroutes = EasyRoutesClient()
        except Exception as e:
            return jsonify({'error': f'Configuration error: {str(e)}'}), 500
        
        # Get route and incomplete stops
        try:
            route = run_async(easyroutes.get_route_by_number(route_number))
            if not route:
                return jsonify({'error': f'Route "{route_number}" not found'}), 404
            
            incomplete_stops = run_async(easyroutes.get_incomplete_stops(route['id']))
            route_summary = run_async(easyroutes.get_route_summary(route['id']))
            
            # Prepare preview data
            preview_stops = []
            valid_phone_count = 0
            
            for stop in incomplete_stops:
                contact = stop.get('contact', {})
                phone_number = contact.get('phone', '').strip()
                
                preview_stops.append({
                    'stop_id': stop.get('id', 'Unknown'),
                    'customer_name': contact.get('name', 'Customer'),
                    'phone': f"***{phone_number[-4:]}" if phone_number and len(phone_number) >= 4 else "No phone",
                    'has_phone': bool(phone_number),
                    'delivery_status': stop.get('deliveryStatus', 'UNKNOWN'),
                    'address': stop.get('address', {}).get('formatted', 'No address')
                })
                
                if phone_number:
                    valid_phone_count += 1
            
            return jsonify({
                'success': True,
                'preview': {
                    'route_summary': route_summary,
                    'incomplete_stops': preview_stops,
                    'total_incomplete': len(incomplete_stops),
                    'valid_phone_numbers': valid_phone_count,
                    'will_receive_sms': valid_phone_count
                }
            })
            
        except Exception as e:
            return jsonify({'error': f'Failed to retrieve route data: {str(e)}'}), 500
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@sms_bp.route('/sms/test', methods=['POST'])
@require_auth
def test_sms():
    """Test SMS functionality with a single message"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        phone_number = data.get('phone_number', '').strip()
        message = data.get('message', '').strip()
        
        if not phone_number or not message:
            return jsonify({'error': 'Phone number and message are required'}), 400
        
        # Initialize Twilio client
        try:
            twilio = TwilioSMSClient()
        except Exception as e:
            return jsonify({'error': f'Configuration error: {str(e)}'}), 500
        
        # Send test message
        result = twilio.send_message_sync(phone_number, message)
        
        return jsonify({
            'success': result['success'],
            'result': result
        })
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

