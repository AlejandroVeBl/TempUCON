import asyncio
import uuid
from temporalio.client import Client
from temporalio import workflow

async def main():
    client = await Client.connect("localhost:7233")

    # Bogus Dict that would be gotten from the loan form
    loan_data = {
        "user": "Ale",
        "amount": 25000,
    }

    # Workflow ID
    workflow_id = f"loan-request-ale-{uuid.uuid4()}"

    print(f"Starting Loan Request for {loan_data['user']}...")

    result = await client.execute_workflow(
        "LoanRequestWorkflowSignals",
        loan_data,
        id=workflow_id,
        task_queue="loan-task-queue",
    )

    print("--- Loan Request Ended ---")
    print(f"Workflow Result: {result}")
    print(f"Notification Result: {result.get('notification', {}).get('msg', 'No Message')}")

if __name__ == "__main__":
    asyncio.run(main())