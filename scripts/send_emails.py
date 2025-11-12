#!/usr/bin/env python3
import sys
import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from nudge_system import record_nudge

load_dotenv()

def send_email(to_email, subject, body_html, from_email, from_name, smtp_user, smtp_password):
    """Send email via Gmail SMTP"""
    try:
        # Create message
        message = MIMEMultipart('alternative')
        message['From'] = f'{from_name} <{from_email}>'
        message['To'] = to_email
        message['Subject'] = subject
        
        # Add HTML body
        html_part = MIMEText(body_html, 'html')
        message.attach(html_part)
        
        # Connect to Gmail SMTP
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, to_email, message.as_string())
        
        return {'status': 'success', 'email': to_email}
    
    except Exception as e:
        return {'status': 'error', 'email': to_email, 'error': str(e)}

def main():
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'No emails data provided'}), flush=True)
        sys.exit(1)
    
    # Parse emails JSON from argument
    try:
        emails_data = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(json.dumps({'error': f'Invalid JSON: {str(e)}'}), flush=True)
        sys.exit(1)
    
    # Get SMTP credentials from environment
    smtp_user = os.getenv('GMAIL_USER')
    smtp_password = os.getenv('GMAIL_APP_PASSWORD')
    from_email = os.getenv('FROM_EMAIL', 'noreply@iiitd.ac.in')
    from_name = os.getenv('FROM_NAME', 'IIIT Dharwad')
    
    if not smtp_user or not smtp_password:
        print(json.dumps({'error': 'Gmail credentials not configured'}), flush=True)
        sys.exit(1)
    
    results = []
    success_count = 0
    skipped_count = 0
    
    for email_data in emails_data:
        # Skip if student has no email address
        if not email_data.get('student_email'):
            results.append({
                'status': 'skipped',
                'email': None,
                'error': 'Student has no email address'
            })
            skipped_count += 1
            continue
        
        result = send_email(
            email_data['student_email'],
            email_data['subject'],
            email_data['body_html'],
            from_email,
            from_name,
            smtp_user,
            smtp_password
        )
        results.append(result)
        if result['status'] == 'success':
            success_count += 1
            # Record nudge after successful send
            nudge_level = email_data.get('nudge_level', 1)
            record_nudge(
                email_data['student_email'],
                email_data.get('student_name', 'Unknown'),
                nudge_level
            )
    
    print(json.dumps({
        'success': True,
        'sent': success_count,
        'skipped': skipped_count,
        'total': len(emails_data),
        'results': results
    }), flush=True)

if __name__ == '__main__':
    main()