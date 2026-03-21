import asyncio
import uuid
from temporalio.client import Client
from temporalio import workflow

async def main():
    client = await Client.connect("localhost:7233")

    # Bogus Dict that would be gotten from the loan form / the bank DB
    loan_data = {
        # --- User Data ---
        "user_id": "Ale",
        "role": "Customer",
        
        # --- Loan Info ---
        "amount": 25000,
        "remuneration": 3000,   # For preA1
        "costs": 1000,          # For preA1
        
        # --- History ---
        "active_loans": 2,      # For preA3
        
        # --- Previous Obligations ---
        "agreed_gdpr": True,    # For preB0
        "agreed_terms": True,   # For preB1
        
        # --- Environment ---
        "device_type": "desktop" # For preC0
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