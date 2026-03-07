from datetime import timedelta
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from activities_customer import (
        fulfil_loan_info,
        request_a_loan,
        receive_notification,
        send_ack_receipt
    )
    from activities_staff import (
        receive_loan_request,
        evaluate_risk,
        send_rating_reports
    )
    from activities_supplier import (
        collect_customer_information,
        request_report,
        collect_rating_reports,
        send_negative_notification,
        send_approved_notification, 
        open_loan_file,
        close_loan_approval_file
    )

@workflow.defn
class LoanRequestWorkflow:
    @workflow.run
    async def run(self, initial_data: dict) -> dict:
        # Common Timeout for all activities
        common_timeout = timedelta(seconds=10)

        # --- 1. Customer Swimlane ---
        loan_info = await workflow.execute_activity(
            fulfil_loan_info,
            initial_data,
            start_to_close_timeout=common_timeout,
        )
        loan_request = await workflow.execute_activity(
            request_a_loan,
            loan_info,
            start_to_close_timeout=common_timeout,
        )

        # --- 2. Supplier Swimlane ---
        customer_data = await workflow.execute_activity(
            collect_customer_information,
            loan_request,
            start_to_close_timeout=common_timeout,
        )

        loan_request = await workflow.execute_activity(
            request_report,
            customer_data,
            start_to_close_timeout=common_timeout,
        )

        # --- 3. Staff Swimlane ---
        received_req = await workflow.execute_activity(
            receive_loan_request,
            loan_request,
            start_to_close_timeout=common_timeout,
        )
        loan_request_report = await workflow.execute_activity(
            evaluate_risk,
            received_req,
            start_to_close_timeout=common_timeout,
        )
        loan_request_report = await workflow.execute_activity(
            send_rating_reports,
            loan_request_report,
            start_to_close_timeout=common_timeout,
        )

        # --- 4. Supplier Swimlane (Gateway) ---        
        loan_request_report = await workflow.execute_activity(
            collect_rating_reports,
            loan_request_report,
            start_to_close_timeout=common_timeout,
        )

        # Decision logic based on the 'evaluate_risk' assesment
        # Could also be assessed with Rego OPA

        if loan_request_report.get("risk", 100) <= 60:
            # Approved
            notif = {"msg": "Loan Approved", "approved": True}
            await workflow.execute_activity(send_approved_notification, notif, start_to_close_timeout=common_timeout)
            await workflow.execute_activity(open_loan_file, loan_request_report, start_to_close_timeout=common_timeout)
        else:
            # Denied
            notif = {"msg": "Loan Denied because of high risk", "approved": False}
            await workflow.execute_activity(send_negative_notification, notif, start_to_close_timeout=common_timeout)

        # --- 5. Customer Swimlane (Notification) ---
        notif_result = await workflow.execute_activity(
            receive_notification, 
            notif, 
            start_to_close_timeout=common_timeout
        )
        
        ack = await workflow.execute_activity(
            send_ack_receipt, 
            notif_result, 
            start_to_close_timeout=common_timeout
        )

        # --- 6. Supplier Swimlane (Closing) ---
        loan_request_report = await workflow.execute_activity(
            close_loan_approval_file,
            loan_request_report,
            start_to_close_timeout=common_timeout,
        )
    
        final_summary = {
            "report": loan_request_report,
            "notification": notif,
            "status": "COMPLETED"
        }
        return final_summary