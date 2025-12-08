import os
from datetime import datetime
import resend
from icalendar import Calendar, Event
from flask import current_app
import base64

def format_session_type(session_type):
    if session_type == 'in-person':
        return 'In-Person'
    elif session_type == 'online':
        return 'Online'
    return session_type.title() if session_type else 'Online'

def generate_ics_event(session_data, tutor_name, student_name):
    cal = Calendar()
    cal.add('prodid', '-//Chinese Tutoring System//EN')
    cal.add('version', '2.0')
    cal.add('method', 'REQUEST')
    
    session_type_display = format_session_type(session_data.get('session_type', 'online'))
    
    event = Event()
    event.add('summary', f'Tutoring Session - {session_data.get("course", "Chinese")}')
    event.add('dtstart', datetime.fromisoformat(session_data['start_time'].replace('Z', '+00:00')) if isinstance(session_data['start_time'], str) else session_data['start_time'])
    event.add('dtend', datetime.fromisoformat(session_data['end_time'].replace('Z', '+00:00')) if isinstance(session_data['end_time'], str) else session_data['end_time'])
    event.add('description', f'Chinese tutoring session with {tutor_name}\nStudent: {student_name}\nType: {session_type_display}')
    event.add('uid', f'session-{session_data["id"]}@chinesetutoring.com')
    
    cal.add_component(event)
    return cal.to_ical()

def send_booking_confirmation(student_email, student_name, tutor_name, session_data):
    api_key = current_app.config.get('RESEND_API_KEY')
    from_email = current_app.config.get('RESEND_FROM_EMAIL')
    
    if not api_key:
        print("Resend API key not configured, skipping email")
        return False
    
    resend.api_key = api_key
    
    start_time = session_data['start_time']
    if isinstance(start_time, str):
        start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    
    formatted_date = start_time.strftime('%B %d, %Y')
    formatted_time = start_time.strftime('%I:%M %p')
    session_type_display = format_session_type(session_data.get('session_type', 'online'))
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2563eb;">Session Booked Successfully!</h2>
        <p>Hi {student_name},</p>
        <p>Your tutoring session has been confirmed.</p>
        <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <p><strong>Course:</strong> {session_data.get('course', 'Chinese')}</p>
            <p><strong>Tutor:</strong> {tutor_name}</p>
            <p><strong>Date:</strong> {formatted_date}</p>
            <p><strong>Time:</strong> {formatted_time}</p>
            <p><strong>Type:</strong> {session_type_display}</p>
        </div>
        <p>A calendar invite is attached to this email. Click to add it to your calendar!</p>
        <p>Best regards,<br>Chinese Tutoring System</p>
    </div>
    """
    
    ics_content = generate_ics_event(session_data, tutor_name, student_name)
    encoded_ics = base64.b64encode(ics_content).decode()
    
    try:
        params = {
            "from": from_email,
            "to": [student_email],
            "subject": f'Session Confirmed - {formatted_date} at {formatted_time}',
            "html": html_content,
            "attachments": [
                {
                    "filename": "session.ics",
                    "content": encoded_ics,
                    "content_type": "text/calendar"
                }
            ]
        }
        
        response = resend.Emails.send(params)
        print(f"Booking confirmation sent to {student_email}, id: {response.get('id')}")
        return True
    except Exception as e:
        print(f"Error sending booking confirmation: {e}")
        return False

def send_tutor_notification(tutor_email, tutor_name, student_name, session_data):
    api_key = current_app.config.get('RESEND_API_KEY')
    from_email = current_app.config.get('RESEND_FROM_EMAIL')
    
    if not api_key:
        print("Resend API key not configured, skipping email")
        return False
    
    resend.api_key = api_key
    
    start_time = session_data['start_time']
    if isinstance(start_time, str):
        start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    
    formatted_date = start_time.strftime('%B %d, %Y')
    formatted_time = start_time.strftime('%I:%M %p')
    session_type_display = format_session_type(session_data.get('session_type', 'online'))
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2563eb;">New Session Booked!</h2>
        <p>Hi {tutor_name},</p>
        <p>A student has booked a session with you.</p>
        <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <p><strong>Student:</strong> {student_name}</p>
            <p><strong>Course:</strong> {session_data.get('course', 'Chinese')}</p>
            <p><strong>Date:</strong> {formatted_date}</p>
            <p><strong>Time:</strong> {formatted_time}</p>
            <p><strong>Type:</strong> {session_type_display}</p>
        </div>
        <p>A calendar invite is attached to this email.</p>
        <p>Best regards,<br>Chinese Tutoring System</p>
    </div>
    """
    
    ics_content = generate_ics_event(session_data, tutor_name, student_name)
    encoded_ics = base64.b64encode(ics_content).decode()
    
    try:
        params = {
            "from": from_email,
            "to": [tutor_email],
            "subject": f'New Booking - {student_name} on {formatted_date}',
            "html": html_content,
            "attachments": [
                {
                    "filename": "session.ics",
                    "content": encoded_ics,
                    "content_type": "text/calendar"
                }
            ]
        }
        
        response = resend.Emails.send(params)
        print(f"Tutor notification sent to {tutor_email}, id: {response.get('id')}")
        return True
    except Exception as e:
        print(f"Error sending tutor notification: {e}")
        return False

def send_feedback_request(student_email, student_name, tutor_name, session_data):
    api_key = current_app.config.get('RESEND_API_KEY')
    from_email = current_app.config.get('RESEND_FROM_EMAIL')
    frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:5173')
    
    if not api_key:
        print("Resend API key not configured, skipping email")
        return False
    
    resend.api_key = api_key
    
    session_id = session_data['id']
    feedback_url = f"{frontend_url}/feedback/{session_id}"
    
    start_time = session_data['start_time']
    if isinstance(start_time, str):
        start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    
    formatted_date = start_time.strftime('%B %d, %Y')
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2563eb;">How was your session?</h2>
        <p>Hi {student_name},</p>
        <p>We hope you had a great tutoring session with {tutor_name} on {formatted_date}!</p>
        <p>We'd love to hear your feedback. It helps us improve and lets your tutor know how they're doing.</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{feedback_url}" style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                Leave Feedback
            </a>
        </div>
        <p style="color: #6b7280; font-size: 14px;">Or copy this link: {feedback_url}</p>
        <p>Thank you!<br>Chinese Tutoring System</p>
    </div>
    """
    
    try:
        params = {
            "from": from_email,
            "to": [student_email],
            "subject": f'How was your session with {tutor_name}?',
            "html": html_content
        }
        
        response = resend.Emails.send(params)
        print(f"Feedback request sent to {student_email}, id: {response.get('id')}")
        return True
    except Exception as e:
        print(f"Error sending feedback request: {e}")
        return False
