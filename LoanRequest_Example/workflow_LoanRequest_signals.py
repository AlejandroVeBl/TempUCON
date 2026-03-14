import asyncio
from datetime import timedelta
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    # Import regular activities from the BPMN diagram
    from activities_customer import receive_notification, send_ack_receipt
    from activities_staff import send_rating_reports
    from activities_supplier import request_report, collect_rating_reports, send_negative_notification, close_loan_approval_file
    # Import UCON activities
    from activities_ucon import notify_external_system, check_opa_policy

@workflow.defn
class LoanRequestWorkflowSignals:
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
    def update_human_task(self, action: str, user: str, result: dict = None):
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

    async def execute_ucon_human_task(self, task_name: str, input_data: dict, common_timeout: timedelta) -> dict:
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
                {"task_name": task_name, "status": "pending", "data": input_data},
                start_to_close_timeout=common_timeout
            )

            # --- PRE-Policy Checks ---
            # Wait for someone to claim the task
            await workflow.wait_condition(lambda: self.current_task_state == "claimed")

            # Check the pre condition to see if they can actually claim that task
            pre_auth = await workflow.execute_activity(
                check_opa_policy,
                {"phase": "pre", "task": task_name, "user": self.current_task_assignee},
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
                except asyncio.TimeoutError:
                    # Time to check passed and it's still 'claimed'. Check On-Policies
                    on_auth = await workflow.execute_activity(
                        check_opa_policy,
                        {"phase": "on", "task": task_name, "user": self.current_task_assignee},
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
                post_auth = await workflow.execute_activity(
                    check_opa_policy,
                    {"phase": "post", "task": task_name, "user": self.current_task_assignee, "result": self.current_task_result},
                    start_to_close_timeout=common_timeout
                )
                
                if post_auth.get("allow"):
                    # Everything checks, keep on with the workflow
                    return self.current_task_result
                else:
                    # Post-Check denied, back to pending
                    continue

    # ------------------------------------------------ #
    #                                                  #
    # -------------- WORFLOW DEFINITION -------------- #
    #                                                  #
    # ------------------------------------------------ #
    @workflow.run
    async def run(self, initial_data: dict) -> dict:
        # Parameters
        common_timeout = timedelta(seconds=10)

        # --- 1. Customer Swimlane ---
        loan_info = await self.execute_ucon_human_task("fulfil_loan_info", initial_data, common_timeout)
        
        loan_request = await self.execute_ucon_human_task("request_a_loan", loan_info, common_timeout)

        # --- 2. Supplier Swimlane ---
        customer_data = await self.execute_ucon_human_task("collect_customer_information", loan_request, common_timeout)

        loan_request = await workflow.execute_activity(request_report, customer_data, start_to_close_timeout=common_timeout)

        # --- 3. Staff Swimlane ---
        received_req = await self.execute_ucon_human_task("receive_loan_request", loan_request, common_timeout)
        
        loan_request_report = await self.execute_ucon_human_task("evaluate_risk", received_req, common_timeout)
        
        loan_request_report = await workflow.execute_activity(send_rating_reports, loan_request_report, start_to_close_timeout=common_timeout)

        # --- 4. Supplier Swimlane (Gateway)  ---        
        loan_request_report = await workflow.execute_activity(collect_rating_reports, loan_request_report, start_to_close_timeout=common_timeout)

        # The gateway can be replaced with an activity to check the condition
        if loan_request_report.get("risk", 100) <= 60:
            notif = {"msg": "Loan Approved", "approved": True}
            await self.execute_ucon_human_task("send_approved_notification", notif, common_timeout)
            await self.execute_ucon_human_task("open_loan_file", loan_request_report, common_timeout)
        else:
            notif = {"msg": "Loan Denied because of high risk", "approved": False}
            await workflow.execute_activity(send_negative_notification, notif, start_to_close_timeout=common_timeout)

        # --- 5. Customer Swimlane (Notification) ---
        notif_result = await workflow.execute_activity(receive_notification, notif, start_to_close_timeout=common_timeout)
        
        ack = await workflow.execute_activity(send_ack_receipt, notif_result, start_to_close_timeout=common_timeout)

        # --- 6. Supplier Swimlane (Closing) ---
        loan_request_report = await workflow.execute_activity(close_loan_approval_file, loan_request_report, start_to_close_timeout=common_timeout)

        # Probably would wanna have an activity to store the data in a DB here
    
        final_summary = {
            "report": loan_request_report,
            "notification": notif,
            "status": "COMPLETED"
        }
        return final_summary