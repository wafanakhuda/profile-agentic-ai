import { NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

export async function POST(request) {
  try {
    const { emails } = await request.json();

    if (!emails || !Array.isArray(emails) || emails.length === 0) {
      return NextResponse.json({ success: false, error: 'No emails to send' }, { status: 400 });
    }

    // Run Python email sender
    const pythonScript = path.join(process.cwd(), 'scripts', 'send_emails.py');
    // Use virtual environment Python on Railway, fallback to system python
    const pythonPath = process.env.PYTHON_PATH || '/opt/venv/bin/python3' || 'python3';
    
    return new Promise((resolve) => {
      const python = spawn(pythonPath, [pythonScript, JSON.stringify(emails)], {
        cwd: process.cwd(),
        env: {
          ...process.env,
          PYTHONPATH: '/opt/venv/lib/python3.13/site-packages'
        }
      });
      
      let resultData = '';
      let errorOutput = '';

      python.stdout.on('data', (data) => {
        resultData += data.toString();
      });

      python.stderr.on('data', (data) => {
        errorOutput += data.toString();
        console.error('Email sender stderr:', data.toString());
      });

      // Add timeout to kill process after 30 seconds
      const timeout = setTimeout(() => {
        python.kill();
        resolve(NextResponse.json({
          success: false,
          error: 'Email sending timed out. Gmail SMTP may be blocked on this server. Consider using SendGrid instead.'
        }, { status: 500 }));
      }, 30000);

      python.on('close', (code) => {
        clearTimeout(timeout);
        if (code === 0 && resultData) {
          try {
            const result = JSON.parse(resultData);
            resolve(NextResponse.json(result));
          } catch (e) {
            resolve(NextResponse.json({
              success: false,
              error: 'Failed to parse email results'
            }, { status: 500 }));
          }
        } else {
          resolve(NextResponse.json({
            success: false,
            error: errorOutput || 'Failed to send emails'
          }, { status: 500 }));
        }
      });
    });
  } catch (error) {
    console.error('Error in send route:', error);
    return NextResponse.json({
      success: false,
      error: error.message
    }, { status: 500 });
  }
}