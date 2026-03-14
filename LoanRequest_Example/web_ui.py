from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import logging

# Import the temporal client and the workflow
from temporalio.client import Client
from workflow_LoanRequest_signals import LoanRequestWorkflowSignals

app = FastAPI(title="Loan Request - Control Panel")
logging.basicConfig(level=logging.INFO)

# To store the tasks
tasks_db = {}

# Data model it expects to receive via the API to send signals
class SignalRequest(BaseModel):
    workflow_id: str
    user: str
    action: str  # "claim" or "complete"
    result_data: dict = None

# Data model it expects to receive via the API to receive tasks
class WebhookTask(BaseModel):
    workflow_id: str
    task_name: str
    status: str = "pending"
    data: dict = {}

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
        body { font-family: 'Segoe UI', sans-serif; background: #f4f7f6; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        
        /* Login Styling */
        #loginScreen { text-align: center; padding: 40px 20px; }
        .login-input { display: block; margin: 10px auto; padding: 10px; width: 80%; max-width: 300px; border: 1px solid #ccc; border-radius: 4px; }
        #dashboardScreen { display: none; }
        
        .user-bar { background: #e8f4f8; padding: 15px; border-radius: 5px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;}
        .task-card { border: 1px solid #ddd; padding: 15px; border-radius: 5px; margin-bottom: 15px; background: #fff; }
        .task-card.claimed { border-left: 5px solid #f39c12; }
        .task-card.pending { border-left: 5px solid #e74c3c; }
        .btn { padding: 8px 15px; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .btn-primary { background: #3498db; }
        .btn-claim { background: #f39c12; }
        .btn-complete { background: #27ae60; }
        pre { background: #eee; padding: 10px; border-radius: 4px; font-size: 12px; overflow-x: auto;}
    </style>
</head>
<body>
    <div class="container">
        
        <div id="loginScreen">
            <h2>Please LogIn</h2>
            <input type="text" id="loginUser" class="login-input" placeholder="Username">
            <input type="password" id="loginPass" class="login-input" placeholder="Password">
            <button class="btn btn-primary" onclick="login()">Log In</button>
            <p id="loginError" style="color: red; display: none;">Incorrect user or password</p>
        </div>

        <div id="dashboardScreen">
            <h1>Task Dashboard</h1>
            <div class="user-bar">
                <span><b>Usuario Activo:</b> <span id="displayUser" style="color:#2980b9; font-weight:bold;"></span></span>
                <div>
                    <button class="btn btn-primary" onclick="loadTasks()">Refresh</button>
                    <button class="btn" style="background:#e74c3c; margin-left:10px;" onclick="logout()">Logout</button>
                </div>
            </div>
            <div id="tasksContainer">Loading Tasks...</div>
        </div>

    </div>

    <script>
        let currentUser = null;
        let authToken = null;
        let taskInterval = null;
        const EasyAuthURL = 'http://127.0.0.1:8330'

        // --- USER AREA --- //

        async function login() {
            const user = document.getElementById('loginUser').value;
            const pass = document.getElementById('loginPass').value;
            const errorMsg = document.getElementById('loginError');
            
            errorMsg.style.display = 'none';

            // EasyAuth uses the OAuth2 standard, thus it requires the data in the form: x-www-form-urlencoded
            const formData = new URLSearchParams();
            formData.append('username', user);
            formData.append('password', pass);

            try {
                // Request EasyAuth URL
                const response = await fetch(`${EasyAuthURL}/auth/token`, {                    
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: formData
                });

                if (response.ok) {
                    const data = await response.json();
                    authToken = data.access_token; // Save the token
                    currentUser = user;            // Save the user

                    // Change the layout
                    document.getElementById('displayUser').innerText = currentUser;
                    document.getElementById('loginScreen').style.display = 'none';
                    document.getElementById('dashboardScreen').style.display = 'block';
                    
                    // Load Tasks
                    loadTasks();
                    taskInterval = setInterval(loadTasks, 5000); // Do so periodically, every 5s
                } else {
                    errorMsg.style.display = 'block';
                }
            } catch (err) {
                console.error(err);
                errorMsg.innerText = "Error on the connection with EasyAuth";
                errorMsg.style.display = 'block';
            }
        }

        function logout() {
            currentUser = null;
            authToken = null;
            clearInterval(taskInterval);
            
            document.getElementById('loginUser').value = '';
            document.getElementById('loginPass').value = '';
            document.getElementById('loginScreen').style.display = 'block';
            document.getElementById('dashboardScreen').style.display = 'none';
        }

        // --- TASK AREA --- //
        async function loadTasks() {
            if (!currentUser) return; // Don't load anything if there is no active user
            
            const response = await fetch('/api/tasks?t=' + new Date().getTime());
            const data = await response.json();
            const container = document.getElementById('tasksContainer');
            
            if (data.tasks.length === 0) {
                container.innerHTML = "<p>No pending tasks</p>";
                return;
            }

            container.innerHTML = ""; 
            
            data.tasks.forEach(task => {
                const isPending = task.status === 'pending';
                const isMine = task.assignee === currentUser;
                const safeData = JSON.stringify(task.data).replace(/"/g, '&quot;');
                
                let buttonsHtml = '';
                if (isPending) {
                    buttonsHtml = `<button class="btn btn-claim" onclick="sendSignal('${task.workflow_id}', 'claim', ${safeData}, '${task.task_name}')">Claim</button>`;
                } else if (isMine) {
                    buttonsHtml = `<button class="btn btn-complete" onclick="sendSignal('${task.workflow_id}', 'complete', ${safeData}, '${task.task_name}')">Complete</button>`;
                } else {
                    buttonsHtml = `<i>Blocked (Assigned to ${task.assignee})</i>`;
                }

                container.innerHTML += `
                    <div class="task-card ${task.status}">
                        <h3> ${task.task_name}</h3>
                        <p><b>Workflow ID:</b> ${task.workflow_id}</p>
                        <p><b>State:</b> ${task.status.toUpperCase()}</p>
                        <details>
                            <summary>See Data</summary>
                            <pre>${JSON.stringify(task.data, null, 2)}</pre>
                        </details>
                        <br>
                        ${buttonsHtml}
                    </div>
                `;
            });
        }

        async function sendSignal(wfId, action, taskData, taskName) {
            let resultData = taskData;

            // Add info of task done and by who if it's completed
            if (action === 'complete') {
                resultData["last_task_done"] = taskName;
                resultData["user_did_last_task"] = currentUser;
            }
            await fetch('/api/signal', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    workflow_id: wfId, 
                    user: currentUser, 
                    action: action, 
                    result_data: resultData 
                })
            });
            
            loadTasks();
        }
    </script>
</body>
</html>
    """
    return html_content

# --- API ENDPOINTS --- #
@app.post("/api/webhook/tasks")
async def receive_task(task: WebhookTask):
    """
    Receives the HTTP Request from a Temporal Worflow to announce a new task
    """
    logging.info(f"New task received: {task.task_name} from Workflow: {task.workflow_id}")
    tasks_db[task.workflow_id] = {
        "workflow_id": task.workflow_id,
        "task_name": task.task_name,
        "status": task.status,
        "assignee": None,
        "data": task.data
    }
    return {"status": "recibido"}

@app.get("/api/tasks")
async def get_tasks():
    """
    The frontend calls here to get a list of the current tasks
    """
    return {"tasks": list(tasks_db.values())}

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
            "update_human_task", 
            args=[req.action, req.user, req.result_data]
        )
        logging.info(f"Signal '{req.action}' sent to workflow {req.workflow_id} by the user {req.user}")

        if req.workflow_id in tasks_db:
            if req.action == "claim":
                tasks_db[req.workflow_id]["status"] = "claimed"
                tasks_db[req.workflow_id]["assignee"] = req.user
                logging.info(f"Local DB Updated: Task {req.action} -> CLAIMED by {req.user}")
            elif req.action == "complete":
                del tasks_db[req.workflow_id]
                logging.info(f"Local DB Updated: Task {req.action} -> Deleted (Completed by {req.user})")
        else:
            logging.warning(f"Workflow {req.workflow_id} not in the Local DB.")
        
        return {"status": "success", "message": f"Signal '{req.action}' processed correctly."}
    
    except Exception as e:
        logging.error(f"Error sending the signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))