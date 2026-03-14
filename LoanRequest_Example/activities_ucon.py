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
async def check_opa_policy(auth_data: dict) -> dict:
    '''
    Receives the phase (pre,on,post) in auth_data['phase]
             the user in auth_data['user']
             and the task in auth_data['task']
    '''
    # This mimics the behavior of an OPA check
    activity.logger.info(f"OPA {auth_data['phase'].upper()}-AUTH check para {auth_data['user']} en {auth_data['task']}")
    # For checking purposes let's say it always returns ('allow':True)
    return {"allow": True}