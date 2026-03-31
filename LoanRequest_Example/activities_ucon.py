from temporalio import activity
import aiohttp

@activity.defn
async def notify_external_system(task_data: dict) -> dict:
    '''
    Receives the task name in task_data['task_name']
    and sends a real HTTP POST request to the external system.
    '''
    task_data["workflow_id"] = activity.info().workflow_id

    activity.logger.info(f"Sending the API request for task -> {task_data.get('task_name')}")
    
    # URL of the front end system
    api_url = "http://localhost:8000/api/webhook/tasks" 
    
    try:
        # Use aiohttp to avoid blocking the Temporal worker
        async with aiohttp.ClientSession() as session:
            # Send the dict task_data as a JSON
            # Short timeout in case the server is down
            async with session.post(api_url, json=task_data, timeout=5.0) as response:
                
                # If the server returns an error raise an error
                response.raise_for_status() 
                
                # Try to read the response JSON
                try:
                    server_response = await response.json()
                except Exception:
                    server_response = await response.text()
                
                activity.logger.info(f"Success, server reply: {response.status}")
                return {"status": "notified", "server_response": server_response}
                
    except aiohttp.ClientError as e:
        # If there is a connection error
        activity.logger.error(f"Critical error connecting to the outside system: {e}")
        # Use raise so Temporal knows there's an error and it can retry after a while and periodically
        raise

@activity.defn
async def get_user_data(username: str) -> dict:
    "Receives the username of an EasyAuth user and returns its data"
    # --- Parameters for the Easy-Auth connection
    EASYAUTH_BASE_URL = "http://127.0.0.1:8330" 
    # Should't be hardcoded.
    SERVICE_USER = "admin"
    SERVICE_PASS = "zwygaazv"

    activity.logger.info(f"Fetching EasyAuth data for user: {username}")
    
    async with aiohttp.ClientSession() as session:
        # Login
        auth_payload = {
            "username": SERVICE_USER,
            "password": SERVICE_PASS
        }
        
        async with session.post(f"{EASYAUTH_BASE_URL}/auth/token", data=auth_payload) as token_response:
            if token_response.status != 200:
                error_text = await token_response.text()
                # Raise exception if it fails so Temporal retries it
                raise RuntimeError(f"Failure authenticating in EasyAuth: {error_text}")
                
            token_data = await token_response.json()
            access_token = token_data.get("access_token")
            
        # Fetch user data adding the appropiate authorized token in the header
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        async with session.get(f"{EASYAUTH_BASE_URL}/auth/users/{username}", headers=headers) as user_response:
            if user_response.status != 200:
                error_text = await user_response.text()
                # Raise exception if it fails so Temporal retries it
                raise RuntimeError(f"Failure fetching user {username}: {error_text}")
                
            user_data = await user_response.json()
            return user_data

@activity.defn
async def check_opa_policy(data: dict) -> dict:
    '''
    Function that receives the following dictionary:

    {
        "phase": phase,
        "task": task_name,
        "user_data": {complete_user_data},
        "object_data": {complete_object_data},
        "environment_data": {complete_environmente_data}
    }

    And calls for the OPA API with the appropiate phase URL with the following dict:

    input : {
        action{
            phase,
            task
        },
        subject{
            ... # Gotten from EasyAuth in this case
        }, 
        object{
            ...  # Possible ones are LoanRequest, LoanRequestReport, *account, task
        },
        environment{
            history[
                [task,user_done_it],
                [task,user_done_it],
                ...
            ],
            device,
            time
        }
    }
    '''
    activity.logger.info(f"OPA {data['phase'].upper()}-AUTH check for {data['user_data']['username']} in {data['task']}")

    # URL of the OPA service
    opa_url = "http://localhost:8181/v1/data/ucon/policy" # This would be for a package ucon.policy 

    input = dict()
    action = dict()
    action["phase"]=data["phase"]
    action["task"]=data["task"]
    input["action"]=action
    input["subject"]=data["user_data"]
    input["object"]=data["object_data"]
    input["environment"]=data["environment_data"]

    # OPA expects the data under the "input" key
    payload = {
        "input": input
    }

    # OPA connection
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(opa_url, json=payload) as response:
                if response.status == 200:
                    opa_response = await response.json()
                    
                    # OPA returns its data under the "result" key
                    # If something odd happens in the file, return False
                    result = opa_response.get("result", {"allow": False})
                    
                    activity.logger.info(f"OPA reply: {result}")
                    return result
                else:
                    error_text = await response.text()
                    activity.logger.error(f"HTTP Error from OPA: {response.status} - {error_text}")
                    raise RuntimeError(f"Failure produced consulting OPA: HTTP {response.status}")
                    
    except aiohttp.ClientError as e:
        activity.logger.error(f"Connection error with OPA: {e}")
        raise RuntimeError(f"Connection error with OPA: {e}")