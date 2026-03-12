from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import logging

# Import the temporal client and the workflow
from temporalio.client import Client
from workflow_LoanRequest_signals import LoanRequestWorkflowSignals

app = FastAPI(title="Loan Request - Control Panel")
logging.basicConfig(level=logging.INFO)

# Data model it expects to receive via the API
class SignalRequest(BaseModel):
    workflow_id: str
    user: str
    action: str  # "claim" or "complete"
    result_data: dict = None

@app.get("/", response_class=HTMLResponse)
async def serve_webpage():
    """
    Simple webpage
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Task Panel</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; color: #333; padding: 20px; }
            .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; font-size: 24px; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
            .form-group { margin-bottom: 15px; }
            label { display: block; font-weight: bold; margin-bottom: 5px; }
            input[type="text"] { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
            .btn { padding: 10px 20px; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; margin-right: 10px; }
            .btn-claim { background-color: #f39c12; }
            .btn-complete { background-color: #27ae60; }
            .btn:hover { opacity: 0.9; }
            #logBox { margin-top: 20px; background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 4px; height: 150px; overflow-y: auto; font-family: monospace; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Employee Panel</h1>
            
            <div class="form-group">
                <label for="workflowId">Workflow ID:</label>
                <input type="text" id="workflowId" placeholder="Paste your Workflow ID here">
            </div>
            
            <div class="form-group">
                <label for="userName">Username:</label>
                <input type="text" id="userName" placeholder="">
            </div>

            <div style="margin-top: 20px;">
                <button class="btn btn-claim" onclick="sendSignal('claim')">Claim Task</button>
                <button class="btn btn-complete" onclick="sendSignal('complete')">Complete Task</button>
            </div>

            <div id="logBox">Waiting for actions</div>
        </div>

        <script>
            function logMessage(msg) {
                const logBox = document.getElementById('logBox');
                logBox.innerHTML += '<div>> ' + msg + '</div>';
                logBox.scrollTop = logBox.scrollHeight;
            }

            async function sendSignal(action) {
                const wfId = document.getElementById('workflowId').value;
                const user = document.getElementById('userName').value;

                if (!wfId || !user) {
                    alert("Please fill out the workflow ID and user info");
                    return;
                }

                logMessage(`Sending [${action.toUpperCase()}] for user ${user}...`);

                // Mock data for 'complete'
                let resultData = null;
                if (action === 'complete') {
                    resultData = { "status": "ok"};
                }

                try {
                    const response = await fetch('/api/signal', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            workflow_id: wfId,
                            user: user,
                            action: action,
                            result_data: resultData
                        })
                    });
                    
                    const result = await response.json();
                    if (response.ok) {
                        logMessage(`Success: ${result.message}`);
                    } else {
                        logMessage(`Error: ${result.detail}`);
                    }
                } catch (error) {
                    logMessage(`Error: ${error}`);
                }
            }
        </script>
    </body>
    </html>
    """
    return html_content

@app.post("/api/signal")
async def handle_signal(req: SignalRequest):
    """
    Receives the HTTP request from the frontend and turns it into a Temporal Signal.
    """
    try:
        # Connect to Temporal
        client = await Client.connect("localhost:7233")
        handle = client.get_workflow_handle(req.workflow_id)
        
        # Send the signal to the workflow
        await handle.signal(
            LoanRequestWorkflowSignals.update_human_task,
            req.action,
            req.user,
            req.result_data
        )
        logging.info(f"Signal '{req.action}' sent to workflow {req.workflow_id} by the user {req.user}")
        
        return {"status": "success", "message": f"Signal '{req.action}' processed correctly."}
    
    except Exception as e:
        logging.error(f"Error sending the signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))