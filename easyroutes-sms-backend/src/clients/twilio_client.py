import os
import re
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class TwilioSMSClient:
    """Client for Twilio SMS API integration"""
    
    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = os.getenv('TWILIO_FROM_NUMBER')
        
        if not all([self.account_sid, self.auth_token, self.from_number]):
            raise ValueError("Twilio credentials not configured properly")
        
        self.client = Client(self.account_sid, self.auth_token)
    
    def _format_phone_number(self, phone_number: str) -> str:
        """Format phone number to E.164 standard"""
        if not phone_number:
            raise ValueError("Phone number is required")
        
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone_number)
        
        if not digits_only:
            raise ValueError("Invalid phone number format")
        
        # Add country code if missing (assume US +1)
        if len(digits_only) == 10:
            return f"+1{digits_only}"
        elif len(digits_only) == 11 and digits_only.startswith('1'):
            return f"+{digits_only}"
        elif digits_only.startswith('+'):
            return phone_number  # Already formatted
        else:
            return f"+{digits_only}"
    
    def _validate_message(self, message: str) -> str:
        """Validate and clean message content"""
        if not message:
            raise ValueError("Message content is required")
        
        # Trim whitespace
        message = message.strip()
        
        # Check length (SMS limit is 160 characters for single message)
        max_length = int(os.getenv('MAX_MESSAGE_LENGTH', 160))
        if len(message) > max_length:
            raise ValueError(f"Message too long (max {max_length} characters)")
        
        return message
    
    async def send_message(self, to_number: str, message_body: str) -> Dict:
        """Send SMS message with error handling"""
        try:
            # Validate and format inputs
            formatted_number = self._format_phone_number(to_number)
            validated_message = self._validate_message(message_body)
            
            # Send message using Twilio
            message = self.client.messages.create(
                body=validated_message,
                from_=self.from_number,
                to=formatted_number
            )
            
            logger.info(f"SMS sent successfully to {formatted_number[-4:]} with SID: {message.sid}")
            
            return {
                "success": True,
                "message_sid": message.sid,
                "status": message.status,
                "to": formatted_number,
                "from": self.from_number,
                "body": validated_message
            }
            
        except TwilioException as e:
            error_msg = f"Twilio error: {str(e)}"
            logger.error(f"Twilio error sending to {to_number}: {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "error_code": getattr(e, 'code', None),
                "to": to_number
            }
            
        except ValueError as e:
            error_msg = f"Validation error: {str(e)}"
            logger.error(f"Validation error for {to_number}: {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "to": to_number
            }
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Unexpected error sending to {to_number}: {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "to": to_number
            }
    
    def send_message_sync(self, to_number: str, message_body: str) -> Dict:
        """Synchronous version of send_message for compatibility"""
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.send_message(to_number, message_body))
    
    def get_message_status(self, message_sid: str) -> Dict:
        """Get the status of a sent message"""
        try:
            message = self.client.messages(message_sid).fetch()
            
            return {
                "success": True,
                "message_sid": message.sid,
                "status": message.status,
                "error_code": message.error_code,
                "error_message": message.error_message,
                "date_sent": message.date_sent.isoformat() if message.date_sent else None,
                "date_updated": message.date_updated.isoformat() if message.date_updated else None
            }
            
        except TwilioException as e:
            return {
                "success": False,
                "error": f"Failed to get message status: {str(e)}"
            }
    
    def validate_phone_number(self, phone_number: str) -> Dict:
        """Validate phone number format without sending a message"""
        try:
            formatted_number = self._format_phone_number(phone_number)
            
            return {
                "valid": True,
                "formatted_number": formatted_number,
                "original_number": phone_number
            }
            
        except ValueError as e:
            return {
                "valid": False,
                "error": str(e),
                "original_number": phone_number
            }
    
    def get_account_info(self) -> Dict:
        """Get Twilio account information"""
        try:
            account = self.client.api.accounts(self.account_sid).fetch()
            
            return {
                "success": True,
                "account_sid": account.sid,
                "friendly_name": account.friendly_name,
                "status": account.status,
                "type": account.type
            }
            
        except TwilioException as e:
            return {
                "success": False,
                "error": f"Failed to get account info: {str(e)}"
            }

