#!/usr/bin/env python3
"""
Nudge System for Student Profile Completion
Tracks and manages 3-level nudging with escalation
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

NUDGE_DATA_FILE = Path('nudge_history.json')

def load_nudge_history():
    """Load nudge history from file"""
    if NUDGE_DATA_FILE.exists():
        with open(NUDGE_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_nudge_history(history):
    """Save nudge history to file"""
    with open(NUDGE_DATA_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def get_nudge_level(student_email):
    """
    Get the current nudge level for a student
    Returns: (nudge_level, days_since_last_nudge, can_send)
    """
    history = load_nudge_history()
    
    if student_email not in history:
        return (1, 0, True)  # First nudge
    
    student_data = history[student_email]
    last_nudge_date = datetime.fromisoformat(student_data['last_nudge_date'])
    current_nudge = student_data['nudge_count']
    days_since = (datetime.now() - last_nudge_date).days
    
    # Can send if 2+ days have passed since last nudge
    can_send = days_since >= 2
    
    # Max 3 nudges
    if current_nudge >= 3:
        return (current_nudge, days_since, False)
    
    # If can send, increment nudge level
    next_nudge = current_nudge + 1 if can_send else current_nudge
    
    return (next_nudge, days_since, can_send)

def record_nudge(student_email, student_name, nudge_level):
    """Record that a nudge was sent"""
    history = load_nudge_history()
    
    history[student_email] = {
        'student_name': student_name,
        'nudge_count': nudge_level,
        'last_nudge_date': datetime.now().isoformat(),
        'nudges': history.get(student_email, {}).get('nudges', []) + [
            {
                'level': nudge_level,
                'date': datetime.now().isoformat()
            }
        ]
    }
    
    save_nudge_history(history)

def get_nudge_config(nudge_level):
    """
    Get configuration for each nudge level
    Returns: (tone, urgency, days_wait)
    """
    configs = {
        1: {
            'tone': 'friendly',
            'urgency': 'low',
            'subject_prefix': '',
            'days_wait': 2,
            'description': 'First gentle reminder'
        },
        2: {
            'tone': 'professional',
            'urgency': 'medium',
            'subject_prefix': 'Reminder: ',
            'days_wait': 2,
            'description': 'Second reminder after 2 days'
        },
        3: {
            'tone': 'urgent',
            'urgency': 'high',
            'subject_prefix': 'URGENT: ',
            'days_wait': 0,
            'description': 'Final critical reminder after 4 days total'
        }
    }
    
    return configs.get(nudge_level, configs[1])

def get_students_needing_nudge(students):
    """
    Get list of students who need a nudge
    Returns: [(student, nudge_level, can_send), ...]
    """
    results = []
    
    for student in students:
        if not student.get('email'):
            continue
        
        if len(student.get('missing_fields', [])) == 0:
            continue
        
        nudge_level, days_since, can_send = get_nudge_level(student['email'])
        
        results.append({
            'student': student,
            'nudge_level': nudge_level,
            'days_since_last': days_since,
            'can_send': can_send,
            'config': get_nudge_config(nudge_level)
        })
    
    return results

if __name__ == '__main__':
    # Test the system
    print("Nudge System Test")
    print("=" * 50)
    
    # Test student
    test_email = "test@example.com"
    
    level, days, can_send = get_nudge_level(test_email)
    print(f"Nudge Level: {level}, Days Since: {days}, Can Send: {can_send}")
    
    config = get_nudge_config(level)
    print(f"Config: {config}")
