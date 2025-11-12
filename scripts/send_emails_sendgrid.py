#!/usr/bin/env python3
"""
Email sender using SendGrid (faster and more reliable for cloud deployments)
"""
import sys
import os
import json
from dotenv import load_dotenv

load_dotenv()

def send_email_sendgrid(to_email, subject, body_html, from_email, from_name):
    """Send email via SendGrid API (much faster than SMTP)"""
    try:
        # Try importing sendgrid
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Email, To, Content
        except ImportError:
            return {
                'status': 'error', 
                'email': to_email, 
                'error': 'SendGrid not installed. Run: pip install sendgrid'
            }
        
        sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
        if not sendgrid_api_key:
            return {
                'status': 'error',
                'email': to_email,
                'error': 'SENDGRID_API_KEY not configured'
            }
        
        # Create SendGrid message
        message = Mail(
            from_email=Email(from_email, from_name),
            to_emails=To(to_email),
            subject=subject,
            html_content=Content("text/html", body_html)
        )
        
        # Send via SendGrid API
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        
        print(f"DEBUG: SendGrid response status: {response.status_code}", file=sys.stderr, flush=True)
        
        if response.status_code == 202:
            return {'status': 'success', 'email': to_email}
        else:
            return {'status': 'error', 'email': to_email, 'error': f'SendGrid error: {response.status_code}'}
    
    except Exception as e:
        return {'status': 'error', 'email': to_email, 'error': str(e)}


def send_email_gmail(to_email, subject, body_html, from_email, from_name, smtp_user, smtp_password):
    """Fallback: Send email via Gmail SMTP"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    try:
        message = MIMEMultipart('alternative')
        message['From'] = f'{from_name} <{from_email}>'
        message['To'] = to_email
        message['Subject'] = subject
        
        html_part = MIMEText(body_html, 'html')
        message.attach(html_part)
        
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=5) as server:
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
    
    try:
        emails_data = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(json.dumps({'error': f'Invalid JSON: {str(e)}'}), flush=True)
        sys.exit(1)
    
    # Get credentials
    from_email = os.getenv('FROM_EMAIL', 'noreply@iiitd.ac.in')
    from_name = os.getenv('FROM_NAME', 'IIIT Dharwad')
    sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
    
    # Decide which service to use
    use_sendgrid = bool(sendgrid_api_key)
    
    if use_sendgrid:
        print("DEBUG: Using SendGrid for email delivery", file=sys.stderr, flush=True)
    else:
        print("DEBUG: Using Gmail SMTP (slower, may timeout)", file=sys.stderr, flush=True)
        smtp_user = os.getenv('GMAIL_USER')
        smtp_password = os.getenv('GMAIL_APP_PASSWORD', '').replace(' ', '')
        
        if not smtp_user or not smtp_password:
            print(json.dumps({'error': 'No email credentials configured'}), flush=True)
            sys.exit(1)
    
    results = []
    success_count = 0
    skipped_count = 0
    
    for email_data in emails_data:
        if not email_data.get('student_email'):
            results.append({
                'status': 'skipped',
                'email': None,
                'error': 'Student has no email address'
            })
            skipped_count += 1
            continue
        
        # Send email
        if use_sendgrid:
            result = send_email_sendgrid(
                email_data['student_email'],
                email_data['subject'],
                email_data['body_html'],
                from_email,
                from_name
            )
        else:
            result = send_email_gmail(
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
            
            # Record nudge
            try:
                from nudge_system import record_nudge
                nudge_level = email_data.get('nudge_level', 1)
                record_nudge(
                    email_data['student_email'],
                    email_data.get('student_name', 'Unknown'),
                    nudge_level
                )
            except Exception as e:
                print(f"DEBUG: Failed to record nudge: {str(e)}", file=sys.stderr, flush=True)
    
    print(json.dumps({
        'success': True,
        'sent': success_count,
        'skipped': skipped_count,
        'total': len(emails_data),
        'results': results
    }), flush=True)

if __name__ == '__main__':
    main()
