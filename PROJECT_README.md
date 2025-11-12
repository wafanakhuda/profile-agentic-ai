# 🤖 Agentic Student Profile Completion System

A complete AI-powered autonomous agent system built with **LangGraph** and **Claude AI** to analyze student profiles, identify gaps, and generate personalized emails for profile completion.

## 🎯 Overview

This system uses a **LangGraph state machine** with autonomous AI decision-making to:
- Analyze student profiles from Excel files
- Identify missing mandatory fields
- Make autonomous decisions about email strategy (tone, urgency, content)
- Generate personalized HTML emails using Claude AI
- Send emails via Gmail SMTP

## 🏗️ Architecture

### Tech Stack
- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS + shadcn/ui
- **Backend**: Next.js API Routes + Python 3.11
- **AI Agent**: LangGraph + Anthropic Claude (claude-3-5-sonnet-20241022)
- **Email**: Gmail SMTP
- **Data Processing**: Pandas + openpyxl

### LangGraph Agent Workflow

```
START → read_excel_node → analyze_gaps_node → 
decide_strategy_node → generate_emails_node → 
finalize_node → END
```

#### Agent Nodes:
1. **read_excel_node**: Reads Excel file, maps columns, identifies missing fields
2. **analyze_gaps_node**: AI analyzes each student (criticality, responsiveness, priority)
3. **decide_strategy_node**: AI decides email strategy (tone, length, emphasis)
4. **generate_emails_node**: AI generates personalized HTML emails via Claude
5. **finalize_node**: Prepares final output with complete analysis

## 📁 Project Structure

```
/app/
├── app/
│   ├── page.js                    # Main UI (upload, analytics, table)
│   └── api/
│       ├── agent/route.js         # Spawns Python LangGraph agent
│       └── send/route.js          # Sends emails via Gmail SMTP
├── scripts/
│   ├── langgraph_agent.py         # LangGraph autonomous agent
│   └── send_emails.py             # Gmail SMTP email sender
├── components/ui/                  # shadcn/ui components
├── .env                           # API keys & configuration
├── requirements.txt               # Python dependencies
└── package.json                   # Node dependencies
```

## 🚀 Quick Start

### 1. Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies
yarn install
```

### 2. Configuration

Update `.env` with your credentials:

```env
# Anthropic API
ANTHROPIC_API_KEY=sk-ant-xxx

# Gmail SMTP
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password
FROM_EMAIL=noreply@yourschool.edu
FROM_NAME=Your Institution Name

# Google Form
GOOGLE_FORM_URL=https://forms.gle/your-form-id
```

### 3. Run the Application

```bash
# Start Next.js server
npm run dev
```

Visit: http://localhost:3000

## 📊 Excel File Format

### Required Columns (with flexible naming):

The system automatically maps these column names:

| Expected Field | Possible Excel Column Names |
|---------------|----------------------------|
| student_name | "Student Name" |
| roll_number | "Roll Number" |
| institute_name | "Institute Name" |
| enrolled_program | "Enrolled program" |
| stream | "Stream" |
| date_of_birth | "Date of birth", "Date  of birth" |
| gender | "Gender" |
| email | "email address", "email" |
| previous_education | "previous education qualification", "previous education" |
| primary_language | "primary language" |
| nationality | "Nationality" |

### Sample Excel Structure:
```
| Student Name | Roll Number | Institute Name | ... | email address |
|--------------|-------------|----------------|-----|---------------|
| John Doe     | CS23B1001   | IIIT Delhi     | ... | john@iiitd.ac.in |
```

## 🎨 Features

### 1. Smart Excel Upload
- Drag & drop or click to upload
- Automatic column name mapping
- Real-time validation

### 2. AI-Powered Analysis
- **Autonomous agent** analyzes each student
- Calculates completion percentage
- Identifies critical gaps
- Makes strategy decisions

### 3. Beautiful Dashboard
- **Analytics Cards**: Total, Complete, Incomplete, Critical students
- **Color-coded badges**:
  - 🟢 Green: ≥90% complete
  - 🟡 Yellow: 70-89% complete
  - 🔴 Red: <70% complete
- **Yellow highlights** for missing fields

### 4. Personalized Email Generation
- Claude AI generates unique email for each student
- Personalized subject lines
- HTML formatted emails
- Mentions specific missing fields
- Includes call-to-action button

### 5. Bulk Email Sending
- Send to all incomplete students with one click
- Progress tracking
- Success/failure reporting
- Skips students without email addresses

## 🤖 How the Agent Works

### Autonomous Decision-Making

The LangGraph agent makes **NO hardcoded decisions**. Everything is determined by Claude AI:

#### Example Decision Process:

**Input**: Student with 63% completion (missing: gender, email, previous_education)

**Agent Analysis**:
```json
{
  "criticality": "high",
  "responsiveness": "medium",
  "priority": "yes",
  "reasoning": "PhD student with multiple critical fields missing"
}
```

**Email Strategy**:
```json
{
  "tone": "professional",
  "length": "detailed",
  "emphasis": "benefits",
  "reasoning": "PhD student needs comprehensive explanation"
}
```

**Generated Email**:
- Subject: "Complete Your IIIT Dharwad Profile - Action Required"
- Body: Personalized HTML with specific missing fields
- CTA: Button linking to Google Form

## 📧 Email Examples

### Sample Generated Email (Fallback):
```html
<html><body>
<p>Dear John Doe,</p>
<p>We noticed your profile is 90% complete. Please update these fields:</p>
<ul>
  <li>Gender</li>
</ul>
<p>
  <a href="https://forms.gle/xxx" style="background-color:#4285F4;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;">
    Complete Profile
  </a>
</p>
<p>Best regards,<br>IIIT Dharwad</p>
</body></html>
```

### AI-Generated Email (when Claude API works):
Claude generates completely unique, contextual emails based on:
- Student's name and completion percentage
- Specific missing fields
- Decided tone (friendly/professional/urgent)
- Decided length (short/medium/detailed)
- Decided emphasis (deadline/benefits/personal_touch)

## 🔒 Security Notes

1. **Gmail App Password**: Never use your regular Gmail password. Always generate an App Password.
2. **API Keys**: Keep `.env` file secure and never commit it to version control.
3. **Student Data**: Excel files are temporarily stored and deleted after processing.

## 🛠️ Testing

### Test Python Agent:
```bash
python3 scripts/langgraph_agent.py path/to/students.xlsx
```

### Test Email Sending:
```bash
# Create test JSON
echo '[{"student_email":"test@example.com","student_name":"Test","subject":"Test","body_html":"<p>Test</p>"}]' > test_emails.json

python3 scripts/send_emails.py "$(cat test_emails.json)"
```

## 📈 Progress Tracking

The agent streams progress updates:
```json
{"type": "progress", "message": "Reading Excel file...", "progress": 10}
{"type": "progress", "message": "Analyzing profile gaps with AI...", "progress": 30}
{"type": "progress", "message": "Generating personalized emails...", "progress": 80}
{"type": "result", "data": {...}}
```

## 🎯 Use Cases

1. **University Admissions**: Track incomplete student applications
2. **HR Onboarding**: Ensure new hires complete profile information
3. **Registration Systems**: Follow up on incomplete registrations
4. **Compliance**: Ensure mandatory fields are collected

## 🔧 Customization

### Add New Mandatory Fields:
Edit `scripts/langgraph_agent.py`:
```python
MANDATORY_FIELDS = [
    'student_name',
    'roll_number',
    # ... add more fields
    'your_new_field'
]

COLUMN_MAPPINGS = {
    'your excel column name': 'your_new_field'
}
```

### Change AI Model:
Edit Claude model in `scripts/langgraph_agent.py`:
```python
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",  # Change this
    max_tokens=2000,
    messages=[...]
)
```

## 📝 Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| ANTHROPIC_API_KEY | Claude API key | sk-ant-xxx |
| GMAIL_USER | Gmail address for sending | your@gmail.com |
| GMAIL_APP_PASSWORD | Gmail app password (16 chars) | abcd efgh ijkl mnop |
| FROM_EMAIL | Display email address | noreply@school.edu |
| FROM_NAME | Sender name | University Admin |
| GOOGLE_FORM_URL | Profile completion form | https://forms.gle/xxx |

## 🚨 Troubleshooting

### Agent Not Running:
- Check Python dependencies: `pip install -r requirements.txt`
- Verify Anthropic API key is valid
- Check uploads directory exists: `mkdir -p uploads`

### Emails Not Sending:
- Verify Gmail App Password (not regular password)
- Check Gmail account has 2FA enabled
- Ensure student has valid email address
- Check Gmail sending limits (500/day)

### Frontend Issues:
- Clear browser cache
- Check Next.js server is running: `npm run dev`
- Verify all UI components exist: `ls components/ui/`

## 🎓 Credits

Built with:
- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent orchestration
- [Anthropic Claude](https://www.anthropic.com/) - AI decision-making
- [Next.js](https://nextjs.org/) - Full-stack framework
- [shadcn/ui](https://ui.shadcn.com/) - UI components
- [Tailwind CSS](https://tailwindcss.com/) - Styling

## 📄 License

This project is for educational purposes. Modify as needed for your institution.

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the LangGraph agent logs
3. Verify all environment variables are set correctly

---

**Built with ❤️ using autonomous AI agents**
