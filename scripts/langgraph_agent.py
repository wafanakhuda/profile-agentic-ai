#!/usr/bin/env python3
import sys
import os
import json
import pandas as pd
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from anthropic import Anthropic
from dotenv import load_dotenv
from nudge_system import get_nudge_level, get_nudge_config

load_dotenv()

# Mandatory fields for student profile
MANDATORY_FIELDS = [
    'student_name',
    'roll_number',
    'institute_name',
    'enrolled_program',
    'stream',
    'date_of_birth',
    'gender',
    'email',
    'previous_education',
    'primary_language',
    'nationality'
]

# Column name mappings (Excel columns -> our field names)
COLUMN_MAPPINGS = {
    'student name': 'student_name',
    'roll number': 'roll_number',
    'institute name': 'institute_name',
    'enrolled program': 'enrolled_program',
    'stream': 'stream',
    'date  of birth': 'date_of_birth',
    'date of birth': 'date_of_birth',
    'gender': 'gender',
    'email address': 'email',
    'email': 'email',
    'previous education qualification': 'previous_education',
    'previous education': 'previous_education',
    'primary language': 'primary_language',
    'nationality': 'nationality'
}

# Agent State
class AgentState(TypedDict):
    file_path: str
    students: List[Dict[str, Any]]
    decisions: List[Dict[str, Any]]
    generated_emails: List[Dict[str, Any]]
    progress: int

# Initialize Anthropic client
client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

def print_progress(message: str, progress: int):
    """Print progress as JSON for streaming to frontend"""
    print(json.dumps({
        'type': 'progress',
        'message': message,
        'progress': progress
    }), flush=True)

def read_excel_node(state: AgentState) -> AgentState:
    """Read Excel file and identify missing fields"""
    print_progress('Reading Excel file...', 10)
    
    try:
        df = pd.read_excel(state['file_path'])
        
        # Normalize column names (lowercase, strip spaces, collapse multiple spaces)
        df.columns = df.columns.str.lower().str.strip()
        
        # Map Excel columns to our field names
        mapped_df = pd.DataFrame()
        for col in df.columns:
            clean_col = col.replace('  ', ' ')  # collapse double spaces
            if clean_col in COLUMN_MAPPINGS:
                mapped_df[COLUMN_MAPPINGS[clean_col]] = df[col]
        
        students = []
        for idx, row in df.iterrows():
            student = {}
            missing_fields = []
            
            # Check each mandatory field
            for field in MANDATORY_FIELDS:
                if field in mapped_df.columns:
                    value = mapped_df.iloc[idx][field]
                    # Check if value is missing (NaN, None, empty string)
                    if pd.isna(value) or str(value).strip() == '':
                        missing_fields.append(field)
                        student[field] = None
                    else:
                        student[field] = str(value).strip()
                else:
                    missing_fields.append(field)
                    student[field] = None
            
            # Calculate completion percentage
            total_fields = len(MANDATORY_FIELDS)
            completed_fields = total_fields - len(missing_fields)
            completion = int((completed_fields / total_fields) * 100)
            
            student['missing_fields'] = missing_fields
            student['completion'] = completion
            student['row_index'] = idx
            
            students.append(student)
        
        print_progress(f'Found {len(students)} students in Excel', 20)
        
        return {
            **state,
            'students': students,
            'progress': 20
        }
    
    except Exception as e:
        print(json.dumps({'type': 'error', 'message': str(e)}), flush=True)
        raise

def analyze_gaps_node(state: AgentState) -> AgentState:
    """Analyze each student's profile gaps using AI"""
    print_progress('Analyzing profile gaps with AI...', 30)
    
    students = state['students']
    decisions = []
    
    # Filter only students with missing fields
    incomplete_students = [s for s in students if len(s['missing_fields']) > 0]
    
    print_progress(f'Analyzing {len(incomplete_students)} incomplete profiles', 40)
    
    for idx, student in enumerate(incomplete_students):
        # Use Claude to analyze this student
        prompt = f"""You are an autonomous agent analyzing a student profile.

Student Profile:
- Name: {student.get('student_name', 'Unknown')}
- Email: {student.get('email', 'Unknown')}
- Completion: {student['completion']}%
- Missing Fields: {', '.join(student['missing_fields'])}

Analyze this student's situation and decide:
1. How critical is this profile gap? (low/medium/high)
2. What's the student's likely responsiveness? (low/medium/high)
3. Should we prioritize this student? (yes/no)

Provide your analysis as JSON:
{{
  "criticality": "low/medium/high",
  "responsiveness": "low/medium/high",
  "priority": "yes/no",
  "reasoning": "brief explanation"
}}

Output ONLY the JSON, nothing else."""
        
        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            analysis = json.loads(response.content[0].text)
            decisions.append({
                'student_email': student.get('email', 'unknown'),
                'student_name': student.get('student_name', 'Unknown'),
                'analysis': analysis
            })
        
        except Exception as e:
            # Fallback decision
            decisions.append({
                'student_email': student.get('email', 'unknown'),
                'student_name': student.get('student_name', 'Unknown'),
                'analysis': {
                    'criticality': 'medium',
                    'responsiveness': 'medium',
                    'priority': 'yes',
                    'reasoning': f'Auto-analysis (API error: {str(e)})'
                }
            })
    
    print_progress('Gap analysis complete', 50)
    
    return {
        **state,
        'decisions': decisions,
        'progress': 50
    }

def decide_strategy_node(state: AgentState) -> AgentState:
    """Agent decides email strategy for each student"""
    print_progress('AI deciding email strategy for each student...', 60)
    
    students = state['students']
    decisions = state['decisions']
    
    # Update decisions with strategy
    for decision in decisions:
        student = next((s for s in students if s.get('email') == decision['student_email']), None)
        if not student:
            continue
        
        # Use Claude to decide email strategy
        prompt = f"""You are an autonomous agent deciding email strategy.

Student: {decision['student_name']}
Completion: {student['completion']}%
Missing: {', '.join(student['missing_fields'])}
Analysis: {decision['analysis']}

Decide the best email strategy:
1. Tone: friendly/professional/urgent
2. Length: short/medium/detailed
3. Emphasis: deadline/benefits/personal_touch

Output JSON:
{{
  "tone": "friendly/professional/urgent",
  "length": "short/medium/detailed",
  "emphasis": "deadline/benefits/personal_touch",
  "reasoning": "brief explanation"
}}

Output ONLY the JSON."""
        
        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            strategy = json.loads(response.content[0].text)
            decision['strategy'] = strategy
        
        except Exception as e:
            decision['strategy'] = {
                'tone': 'professional',
                'length': 'medium',
                'emphasis': 'benefits',
                'reasoning': f'Default strategy (API error: {str(e)})'
            }
    
    print_progress('Email strategies decided', 70)
    
    return {
        **state,
        'decisions': decisions,
        'progress': 70
    }

def generate_emails_node(state: AgentState) -> AgentState:
    """Generate personalized emails using Claude for each student"""
    print_progress('Generating personalized emails with AI...', 80)
    
    students = state['students']
    decisions = state['decisions']
    decision_map = {d['student_email']: d for d in decisions}
    
    generated_emails = []
    
    form_url = os.getenv('GOOGLE_FORM_URL', 'https://forms.gle/AFNpAnnS9aWURoQj9')
    from_name = os.getenv('FROM_NAME', 'IIIT Dharwad')
    
    # Email template to guide AI
    template_guide = """
Use this template structure but personalize it:

Dear {{student_name}},
Greetings from IIIT Dharwad! 👋

We noticed that your student profile is incomplete, and a few important details are still missing. Please take a moment to update them so we can ensure your records are accurate and you get full access to all academic resources.

🧾 Missing fields:
{{missing_fields_list}}

Completing your profile helps you stay connected with:
🎯 Class schedules and live sessions
📚 Study materials and announcements
🧩 Interactive academic activities

👉 Complete your profile here:
🔗 {{form_link}}

If you need any help, our Support Team is always here for you.

Let's make sure your journey at IIIT Dharwad continues smoothly and without interruption!

Best regards,
Team IIIT Dharwad
"""
    
    for student in students:
        if len(student['missing_fields']) == 0:
            continue  # Skip complete profiles
        
        student_email = student.get('email')
        decision = decision_map.get(student_email, {})
        strategy = decision.get('strategy', {})
        
        # Get nudge level for this student
        nudge_level, days_since, can_send = get_nudge_level(student_email) if student_email else (1, 0, True)
        nudge_config = get_nudge_config(nudge_level)
        
        # Adjust tone based on nudge level
        tone_guidance = {
            1: "Use a warm, friendly, and gentle tone. This is the first reminder.",
            2: "Use a professional, encouraging tone with slight urgency. This is the second reminder (2 days after first).",
            3: "Use an urgent, direct, but still respectful tone. This is the FINAL reminder (4 days after first). Emphasize deadline and consequences."
        }
        
        # Generate personalized email using Claude
        prompt = f"""You are an autonomous email generation agent for {from_name}.

Generate a personalized email following this template structure:

{template_guide}

Student Details:
- Name: {student.get('student_name', 'Student')}
- Completion: {student['completion']}%
- Missing Fields: {', '.join(student['missing_fields'])}

Nudge Information:
- Nudge Level: {nudge_level} of 3 ({nudge_config['description']})
- Days Since Last: {days_since}
- Tone: {tone_guidance[nudge_level]}
- Urgency: {nudge_config['urgency']}

Requirements:
1. Create a compelling subject line with prefix "{nudge_config['subject_prefix']}" (e.g., "{nudge_config['subject_prefix']}Complete Your IIIT Dharwad Profile")
2. Follow the template structure provided above
3. Adjust tone based on nudge level (Nudge {nudge_level}):
   - Nudge 1: Warm, friendly, gentle reminder
   - Nudge 2: Professional, encouraging with slight urgency
   - Nudge 3: Urgent, direct - FINAL reminder with emphasis on consequences
4. Use emojis appropriately
5. For Nudge 3, add urgency language like "Final Reminder", "Immediate Action Required"
6. Format missing fields as a bulleted list with proper formatting
7. Make it HTML formatted with professional styling
8. Include the Google Form link: {form_url}
9. Sign off as "Team IIIT Dharwad"

Output JSON:
{{
  "subject": "subject with appropriate prefix and urgency",
  "body_html": "full HTML email content with appropriate tone for nudge level {nudge_level}"
}}

Output ONLY the JSON."""
        
        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            email_content = json.loads(response.content[0].text)
            
            generated_emails.append({
                'student_email': student_email,
                'student_name': student.get('student_name', 'Student'),
                'subject': email_content['subject'],
                'body_html': email_content['body_html'],
                'missing_fields': student['missing_fields'],
                'completion': student['completion'],
                'nudge_level': nudge_level,
                'nudge_config': nudge_config
            })
        
        except Exception:
            # Fallback email using template format
            missing_fields_html = ''.join([f"<li>✦ <strong>{field.replace('_', ' ').title()}</strong></li>" for field in student['missing_fields']])
            
            # Get nudge styling based on level
            header_color = {
                1: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                2: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                3: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)'
            }.get(nudge_level, 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)')
            
            generated_emails.append({
                'student_email': student_email,
                'student_name': student.get('student_name', 'Student'),
                'subject': f'{nudge_config["subject_prefix"]}Complete Your IIIT Dharwad Profile - Action Needed',
                'body_html': f'''<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: {header_color}; color: white; padding: 20px; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; }}
        .missing-fields {{ background: #fff; padding: 15px; border-left: 4px solid #f59e0b; margin: 20px 0; border-radius: 5px; }}
        .missing-fields ul {{ list-style: none; padding: 0; }}
        .missing-fields li {{ padding: 8px 0; }}
        .benefits {{ background: #fff; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        .benefits ul {{ list-style: none; padding: 0; }}
        .benefits li {{ padding: 5px 0; }}
        .cta-button {{ display: inline-block; background: #4285F4; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
        .footer {{ text-align: center; color: #666; margin-top: 30px; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2 style="margin:0;">IIIT Dharwad</h2>
        </div>
        <div class="content">
            <p>Dear <strong>{student.get('student_name', 'Student')}</strong>,</p>
            <p>Greetings from IIIT Dharwad! 👋</p>
            
            <p>We noticed that your student profile is <strong>{student['completion']}% complete</strong>, and a few important details are still missing. Please take a moment to update them so we can ensure your records are accurate and you get full access to all academic resources.</p>
            
            <div class="missing-fields">
                <p><strong>🧾 Missing fields:</strong></p>
                <ul>{missing_fields_html}</ul>
            </div>
            
            <div class="benefits">
                <p><strong>Completing your profile helps you stay connected with:</strong></p>
                <ul>
                    <li>🎯 Class schedules and live sessions</li>
                    <li>📚 Study materials and announcements</li>
                    <li>🧩 Interactive academic activities</li>
                </ul>
            </div>
            
            <p><strong>👉 Complete your profile here:</strong></p>
            <center>
                <a href="{form_url}" class="cta-button">Complete Profile Now</a>
            </center>
            
            <p>If you need any help, our Support Team is always here for you.</p>
            
            <p>Let's make sure your journey at IIIT Dharwad continues smoothly and without interruption!</p>
            
            <div class="footer">
                <p><strong>Best regards,</strong><br>Team IIIT Dharwad</p>
            </div>
        </div>
    </div>
</body>
</html>''',
                'missing_fields': student['missing_fields'],
                'completion': student['completion'],
                'nudge_level': nudge_level,
                'nudge_config': nudge_config
            })
    
    print_progress(f'Generated {len(generated_emails)} personalized emails', 90)
    
    return {
        **state,
        'generated_emails': generated_emails,
        'progress': 90
    }

def finalize_node(state: AgentState) -> AgentState:
    """Finalize and prepare output"""
    print_progress('Finalizing results...', 100)
    
    # Prepare final output
    output = {
        'total_students': len(state['students']),
        'incomplete_students': len([s for s in state['students'] if len(s['missing_fields']) > 0]),
        'emails_generated': len(state['generated_emails']),
        'students': state['students'],
        'emails': state['generated_emails']
    }
    
    # Print final result as JSON
    print(json.dumps({'type': 'result', 'data': output}), flush=True)
    
    return {
        **state,
        'progress': 100
    }

def build_agent():
    """Build the LangGraph agent"""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node('read_excel', read_excel_node)
    workflow.add_node('analyze_gaps', analyze_gaps_node)
    workflow.add_node('decide_strategy', decide_strategy_node)
    workflow.add_node('generate_emails', generate_emails_node)
    workflow.add_node('finalize', finalize_node)
    
    # Set entry point
    workflow.set_entry_point('read_excel')
    
    # Add edges
    workflow.add_edge('read_excel', 'analyze_gaps')
    workflow.add_edge('analyze_gaps', 'decide_strategy')
    workflow.add_edge('decide_strategy', 'generate_emails')
    workflow.add_edge('generate_emails', 'finalize')
    workflow.add_edge('finalize', END)
    
    return workflow.compile()

def main():
    if len(sys.argv) < 2:
        print(json.dumps({'type': 'error', 'message': 'No file path provided'}), flush=True)
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(json.dumps({'type': 'error', 'message': f'File not found: {file_path}'}), flush=True)
        sys.exit(1)
    
    # Build and run the agent
    agent = build_agent()
    
    initial_state = {
        'file_path': file_path,
        'students': [],
        'decisions': [],
        'generated_emails': [],
        'progress': 0
    }
    
    try:
        agent.invoke(initial_state)
    except Exception as e:
        print(json.dumps({'type': 'error', 'message': str(e)}), flush=True)
        sys.exit(1)

if __name__ == '__main__':
    main()