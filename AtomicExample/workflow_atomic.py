import asyncio
from datetime import timedelta
from datetime import timezone
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    # Import UCON activities
    from activities_ucon import notify_external_system, check_opa_policy, get_user_data

@workflow.defn
class AtomicUconWorkflow:
    def __init__(self):
        # State variables for the current human task
        self.current_task_state = "uninitialized"
        self.current_task_assignee = None
        self.current_task_result = {}

    # -------------------------------------------------- #
    #                                                    #
    # --------------   SIGNAL HANDLER &   -------------- #
    # -------------- FUNCTION DEFINITIONS -------------- #
    #                                                    #
    # -------------------------------------------------- #


    @workflow.signal
    def update_human_task(self, action: str, user: str, result: dict = None, task_info: dict = None):
        '''
        Signal that receives the events from the outside server
        action: 'claim' (claim a task) or 'complete' (complete task)
        '''
        if action == "claim":
            self.current_task_state = "claimed"
            self.current_task_assignee = user
        elif action == "complete":
            self.current_task_state = "completed"
            self.current_task_result = result or {}
            self.last_event_info = task_info

    async def execute_ucon_human_task(self, task_name: str, object_data: dict, environment_data: dict, common_timeout: timedelta) -> dict:
        '''
        Function that abstracts the worflow from the nuances of running a human task with UCON policy checks
        This function uses signals itself to handle the Pre, On and Post policy checks for a given human task 
        '''
        OnPolicyChecksTime=timedelta(seconds=15) # Frecuency in which the On-Policies are checked when a task is claimed

        while True:

            self.current_task_state = "pending"
            self.current_task_assignee = None
            self.current_task_result = {}

            # Notify the external system there's a new pending activity
            await workflow.execute_activity(
                notify_external_system,
                {"task_name": task_name, "status": "pending", "data": object_data},
                start_to_close_timeout=common_timeout
            )

            # --- PRE-Policy Checks ---
            # Wait for someone to claim the task
            await workflow.wait_condition(lambda: self.current_task_state == "claimed")
            
            # Get the user data from the current logged-in user
            user_data = await workflow.execute_activity(
                get_user_data,
                self.current_task_assignee,
                start_to_close_timeout=common_timeout
            )

            # Check the pre condition to see if they can actually claim that task
            pre_auth = await workflow.execute_activity(
                check_opa_policy,
                {"phase": "pre", "task": task_name, "user_data": user_data, "object_data": object_data,"environment_data":environment_data},
                start_to_close_timeout=common_timeout
            )
            
            if not pre_auth.get("allow"):
                # If the policy check is denied, restart
                continue

            # --- ON-Policy Checks ---
            revoked = False
            while self.current_task_state == "claimed":
                try:
                    # Wait for the task to be completed, but wake up periodically to check
                    await workflow.wait_condition(
                        lambda: self.current_task_state == "completed",
                        timeout=OnPolicyChecksTime # Frequency to be checked
                    )
                    # object_data["customer"]["credentials"]["validated"] = False
                except asyncio.TimeoutError:
                    # Time to check passed and it's still 'claimed'. Check On-Policies
                    on_auth = await workflow.execute_activity(
                        check_opa_policy,
                        {"phase": "on", "task": task_name, "user_data": user_data, "object_data": object_data,"environment_data":environment_data},
                        start_to_close_timeout=common_timeout
                    )
                    if not on_auth.get("allow"):
                        # Access revoked in real time
                        revoked = True
                        break # Break from the On-Policy check loop
            
            if revoked:
                continue # Back to the beggining, create the task as pending

            # --- POST-Policy Checks ---
            if self.current_task_state == "completed":

                # Add data to history when it's completed
                new_history_entry = (task_name, self.current_task_assignee)
                history_dict = environment_data.get("history", {})
                if "tasks_done" not in history_dict or not isinstance(history_dict["tasks_done"], list):
                    history_dict["tasks_done"] = []
                history_dict["tasks_done"].append(new_history_entry)

                # Post-check, after adding the history, in case it was neccesary
                post_auth = await workflow.execute_activity(
                    check_opa_policy,
                    {"phase": "post", "task": task_name, "user_data": user_data, "object_data": object_data,"environment_data":environment_data, "result": self.current_task_result},
                    start_to_close_timeout=common_timeout
                )
                
                if post_auth.get("allow"):
                    # Everything checks, keep on with the workflow
                    return self.current_task_result
                else:
                    # Post-Check denied, back to pending
                    history_dict["tasks_done"].pop() # Remove the history if it failed
                    continue

    # ------------------------------------------------ #
    #                                                  #
    # -------------- WORFLOW DEFINITION -------------- #
    #                                                  #
    # ------------------------------------------------ #
    @workflow.run
    async def run(self, initial_data: dict) -> dict:
        # Parameters
        timeout = timedelta(seconds=10)
        object_data = initial_data.get("object", {})
        environment = initial_data.get("environment", {"history": {"tasks_done": []}})

        # Sequential execution of tasks A and B
        result_A = await self.execute_ucon_human_task("Activity_A", object_data, environment, timeout)
        
        # Pasamos el resultado de A como parte del objeto para B
        object_data["result_A"] = result_A
        
        result_B = await self.execute_ucon_human_task("Activity_B", object_data, environment, timeout)

        return {"status": "COMPLETED", "final_result": result_B, "environment": environment}