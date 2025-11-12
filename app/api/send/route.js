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
    const pythonPath = '/root/.venv/bin/python3';
    
    return new Promise((resolve) => {
      const python = spawn(pythonPath, [pythonScript, JSON.stringify(emails)]);
      
      let resultData = '';
      let errorOutput = '';

      python.stdout.on('data', (data) => {
        resultData += data.toString();
      });

      python.stderr.on('data', (data) => {
        errorOutput += data.toString();
      });

      python.on('close', (code) => {
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