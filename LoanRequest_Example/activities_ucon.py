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
async def check_opa_policy(data: dict) -> dict:
    '''
    Receives the phase (pre,on,post) in data['phase]
             the user in data['user']
             and the task in data['task']

    TODO : It should send the following structure:
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
    # This mimics the behavior of an OPA check
    activity.logger.info(f"OPA {data['phase'].upper()}-AUTH check para {data['user']} en {data['task']}")

    # URL of the OPA service
    opa_url = "http://localhost:8181/v1/data/ucon/policy" # This would be for a package ucon.policy 


    # OPA expects the data under the "input" key
    payload = {
        "input": data
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