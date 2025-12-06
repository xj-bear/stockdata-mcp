#!/usr/bin/env node
const { spawn } = require('child_process');
const path = require('path');

// Path to the Python server script
const serverPath = path.join(__dirname, 'server.py');

// Spawn the Python process
// Assuming 'python' is in the system PATH. Users might need to adjust this to 'python3' if needed.
const pythonProcess = spawn('python', [serverPath], { stdio: 'inherit' });

pythonProcess.on('close', (code) => {
    process.exit(code);
});

pythonProcess.on('error', (err) => {
    console.error('Failed to start Python server:', err);
    console.error('Please ensure Python is installed and "python" is in your PATH.');
    console.error('You also need to install dependencies: pip install mcp akshare pandas starlette uvicorn httpx');
});
