import { NextResponse } from 'next/server';
import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';
import { writeFile } from 'fs/promises';

export async function POST(request) {
  try {
    const formData = await request.formData();
    const file = formData.get('file');

    if (!file) {
      return NextResponse.json({ success: false, error: 'No file uploaded' }, { status: 400 });
    }

    // Save uploaded file temporarily
    const bytes = await file.arrayBuffer();
    const buffer = Buffer.from(bytes);
    const uploadDir = path.join(process.cwd(), 'uploads');
    
    if (!fs.existsSync(uploadDir)) {
      fs.mkdirSync(uploadDir, { recursive: true });
    }

    const filePath = path.join(uploadDir, `${Date.now()}_${file.name}`);
    await writeFile(filePath, buffer);

    // Run Python LangGraph agent
    const pythonScript = path.join(process.cwd(), 'scripts', 'langgraph_agent.py');
    // Use virtual environment Python on Railway, fallback to system python
    const pythonPath = process.env.PYTHON_PATH || '/opt/venv/bin/python3' || 'python3';
    
    return new Promise((resolve) => {
      const python = spawn(pythonPath, [pythonScript, filePath], {
        cwd: process.cwd(),
        env: {
          ...process.env,
          PYTHONPATH: '/opt/venv/lib/python3.13/site-packages'
        }
      });
      
      let resultData = null;
      let errorOutput = '';

      python.stdout.on('data', (data) => {
        const lines = data.toString().split('\n').filter(line => line.trim());
        
        lines.forEach(line => {
          try {
            const parsed = JSON.parse(line);
            
            if (parsed.type === 'result') {
              resultData = parsed.data;
            } else if (parsed.type === 'error') {
              errorOutput = parsed.message;
            }
            // Progress messages are logged but not stored
          } catch (e) {
            // Ignore non-JSON lines
          }
        });
      });

      python.stderr.on('data', (data) => {
        errorOutput += data.toString();
        console.error('Python stderr:', data.toString());
      });

      python.on('close', (code) => {
        // Clean up uploaded file
        try {
          fs.unlinkSync(filePath);
        } catch (e) {
          // Ignore cleanup errors
        }

        if (code === 0 && resultData) {
          resolve(NextResponse.json({ success: true, data: resultData }));
        } else {
          resolve(NextResponse.json({
            success: false,
            error: errorOutput || 'Failed to process file'
          }, { status: 500 }));
        }
      });
    });
  } catch (error) {
    console.error('Error in agent route:', error);
    return NextResponse.json({
      success: false,
      error: error.message
    }, { status: 500 });
  }
}