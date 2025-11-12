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

def send_email(to_email, subject, body_html, from_name, smtp_user, smtp_password):
    """Send email via Gmail SMTP - OPTIMIZED"""
    try:
        # Create message
        message = MIMEMultipart('alternative')
        # IMPORTANT: Use actual Gmail user as From address to avoid Gmail blocking
        message['From'] = f'{from_name} <{smtp_user}>'
        message['To'] = to_email
        message['Subject'] = subject
        
        # Add HTML body
        html_part = MIMEText(body_html, 'html')
        message.attach(html_part)
        
        print(f"DEBUG: Sending to {to_email} via {smtp_user}", file=sys.stderr, flush=True)
        
        # Option 1: Try port 587 with STARTTLS (standard)
        try:
            with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as server:
                server.set_debuglevel(0)  # Disable verbose debug
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, to_email, message.as_string())
            
            print(f"DEBUG: ✓ Email sent successfully to {to_email}", file=sys.stderr, flush=True)
            return {'status': 'success', 'email': to_email}
        
        except Exception as e1:
            print(f"DEBUG: Port 587 failed: {str(e1)}, trying port 465...", file=sys.stderr, flush=True)
            
            # Option 2: Try port 465 with SSL (alternative)
            import smtplib
            from smtplib import SMTP_SSL
            
            with SMTP_SSL('smtp.gmail.com', 465, timeout=10) as server:
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, to_email, message.as_string())
            
            print(f"DEBUG: ✓ Email sent via port 465 to {to_email}", file=sys.stderr, flush=True)
            return {'status': 'success', 'email': to_email}
    
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f'Authentication failed. Check GMAIL_APP_PASSWORD'
        print(f"DEBUG ERROR: {error_msg} - {str(e)}", file=sys.stderr, flush=True)
        return {'status': 'error', 'email': to_email, 'error': error_msg}
    
    except smtplib.SMTPException as e:
        error_msg = f'SMTP error: {str(e)}'
        print(f"DEBUG ERROR: {error_msg}", file=sys.stderr, flush=True)
        return {'status': 'error', 'email': to_email, 'error': error_msg}
    
    except Exception as e:
        error_msg = f'Connection error: {str(e)}'
        print(f"DEBUG ERROR: {error_msg}", file=sys.stderr, flush=True)
        return {'status': 'error', 'email': to_email, 'error': error_msg}

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
    smtp_password = os.getenv('GMAIL_APP_PASSWORD', '').replace(' ', '')  # Remove any spaces
    from_name = os.getenv('FROM_NAME', 'IIIT Dharwad')
    
    if not smtp_user or not smtp_password:
        print(json.dumps({'error': 'Gmail credentials not configured'}), flush=True)
        sys.exit(1)
    
    print(f"DEBUG: Sending {len(emails_data)} emails via Gmail ({smtp_user})", file=sys.stderr, flush=True)
    print(f"DEBUG: Password length: {len(smtp_password)} chars", file=sys.stderr, flush=True)
    
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