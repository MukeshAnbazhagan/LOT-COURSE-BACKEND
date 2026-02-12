import os
from twilio.rest import Client
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
        
        if not self.account_sid or not self.auth_token:
            logger.warning("Twilio credentials not found. WhatsApp messaging will be disabled.")
            self.client = None
        else:
            self.client = Client(self.account_sid, self.auth_token)
    
    def send_enrollment_message(
        self, 
        to_phone: str, 
        user_name: str, 
        course_title: str, 
        dashboard_link: str
    ) -> Optional[str]:
        """Send WhatsApp message for course enrollment"""
        if not self.client:
            logger.warning("WhatsApp client not initialized")
            return None
        
        message_body = f"""🎉 Welcome to {course_title}!

Hi {user_name},

Congratulations on enrolling! 🎓

📚 Access your course here: {dashboard_link}

Need help? Just reply to this message!

Happy Learning! 🚀"""
        
        return self._send_message(to_phone, message_body)
    
    def send_event_rsvp_message(
        self, 
        to_phone: str, 
        user_name: str, 
        event_title: str, 
        event_date: str,
        event_time: str,
        event_link: Optional[str] = None
    ) -> Optional[str]:
        """Send WhatsApp message for event RSVP"""
        if not self.client:
            logger.warning("WhatsApp client not initialized")
            return None
        
        link_text = f"\n\n🔗 Join here: {event_link}" if event_link else ""
        
        message_body = f"""✅ Event Registration Confirmed!

Hi {user_name},

You're registered for: {event_title}

📅 Date: {event_date}
⏰ Time: {event_time}{link_text}

We'll send you a reminder before the event!

See you there! 👋"""
        
        return self._send_message(to_phone, message_body)
    
    def send_certificate_message(
        self, 
        to_phone: str, 
        user_name: str, 
        course_title: str, 
        certificate_url: str
    ) -> Optional[str]:
        """Send WhatsApp message for certificate issuance"""
        if not self.client:
            logger.warning("WhatsApp client not initialized")
            return None
        
        message_body = f"""🏆 Certificate Earned!

Congratulations {user_name}! 

You've successfully completed: {course_title}

Download your certificate: {certificate_url}

Share your achievement! 🎉"""
        
        return self._send_message(to_phone, message_body)
    
    def send_reminder_message(
        self, 
        to_phone: str, 
        user_name: str, 
        event_title: str, 
        event_time: str
    ) -> Optional[str]:
        """Send WhatsApp reminder for upcoming event"""
        if not self.client:
            logger.warning("WhatsApp client not initialized")
            return None
        
        message_body = f"""⏰ Event Reminder!

Hi {user_name},

Don't forget! "{event_title}" starts in 24 hours.

⏰ Time: {event_time}

See you soon! 👋"""
        
        return self._send_message(to_phone, message_body)
    
    def _send_message(self, to_phone: str, message_body: str) -> Optional[str]:
        """Internal method to send WhatsApp message"""
        try:
            # Ensure phone number has whatsapp: prefix
            if not to_phone.startswith("whatsapp:"):
                to_phone = f"whatsapp:{to_phone}"
            
            message = self.client.messages.create(
                from_=self.whatsapp_number,
                body=message_body,
                to=to_phone
            )
            
            logger.info(f"WhatsApp message sent successfully: {message.sid}")
            return message.sid
            
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {str(e)}")
            return None

# Create singleton instance
whatsapp_service = WhatsAppService()