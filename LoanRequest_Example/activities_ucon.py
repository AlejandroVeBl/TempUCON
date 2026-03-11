from temporalio import activity

@activity.defn
async def notify_external_system(task_data: dict) -> dict:
    '''
    Receives the task name in task_data['task_name']
    '''
    # This mimics the behavior of the actual API request to say there is a pending activity
    # TODO: Make it make an actual API Request
    activity.logger.info(f"API REQUEST: Available Task -> {task_data['task_name']}")
    return {"status": "notified"}

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