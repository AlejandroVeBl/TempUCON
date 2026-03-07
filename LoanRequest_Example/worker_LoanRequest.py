import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from temporalio import workflow
import logging

with workflow.unsafe.imports_passed_through():
    # Workflow Import
    from workflow_LoanRequest import LoanRequestWorkflow 
    # Customer Import
    from activities_customer import (
        fulfil_loan_info, request_a_loan, receive_notification, send_ack_receipt
    )
    # Staff Import
    from activities_staff import (
        receive_loan_request, evaluate_risk, send_rating_reports
    )
    # Supplier Import
    from activities_supplier import (
        collect_customer_information, request_report, collect_rating_reports,
        send_negative_notification, send_approved_notification, open_loan_file, close_loan_approval_file
    )

async def main():
    
    # Configure logging so that it logs the activity.logger.info function calls in the activities
    # logging.basicConfig(level=logging.INFO)

    client = await Client.connect("localhost:7233")

    # All Activities List
    all_activities = [
        fulfil_loan_info, request_a_loan, receive_notification, send_ack_receipt,
        receive_loan_request, evaluate_risk, send_rating_reports,
        collect_customer_information, request_report, collect_rating_reports,
        send_negative_notification, send_approved_notification, open_loan_file, close_loan_approval_file
    ]

    worker = Worker(
        client,
        task_queue="loan-task-queue", # Could be multiple queues for multiple workers, i.e. one worker for the staff swimlane and one for the rest
        workflows=[LoanRequestWorkflow],
        activities=all_activities,
    )
    print("Worker started.")
    await worker.run()

if __name__ == "__main__":
    
    asyncio.run(main())