package ucon.on

# Don't allow by default
default allow := false

# ===========================================================================
# MAIN RULE
# ===========================================================================
# To allow it has to pass the RBAC role membership check and the UCON rules
allow if {
    has_rbac
    passes_ucon
}

# ===========================================================================
# RBAC: Basic role membership check
# ===========================================================================
# Map each task with the right needed to execute it
task_permissions := {
    "fulfil_loan_info": "TAKE_CUSTOMER_ACTIVITY",
    "request_a_loan": "TAKE_CUSTOMER_ACTIVITY",
    
    "collect_customer_information": "TAKE_SUPPLIER_ACTIVITY",
    "send_approved_notification": "TAKE_SUPPLIER_ACTIVITY",
    "open_loan_file": "TAKE_SUPPLIER_ACTIVITY",

    "receive_loan_request": "TAKE_STAFF_ACTIVITY",
    "evaluate_risk_1": "TAKE_STAFF_ACTIVITY",
    "evaluate_risk_2": "TAKE_STAFF_ACTIVITY"
}

# Map the rbac check into "has_rbac" variable
default has_rbac := false
has_rbac if {
    required_permission := task_permissions[input.action.task]
    required_permission in input.subject.permissions.actions
}

# ===========================================================================
# UCON: ON-Checks
# ===========================================================================

default passes_ucon := false

# ------------------------------------------
# TASKS WITHOUT EXPLICIT UCON ON CHECKS
# ------------------------------------------
passes_ucon if {
    tasks_without_ucon := {
        "fulfil_loan_info", 
        "collect_customer_information",
        "receive_loan_request"
    }
    input.action.task in tasks_without_ucon
}

# ------------------------------------------
# TASK: request_a_loan
# ------------------------------------------
passes_ucon if {
    input.action.task == "request_a_loan"

    # --- Auth Checks --- #
    # onA0: The customer is allowed while its credentials are not revoked
    input.object.customer.credentials.revoked == false
}

# ------------------------------------------
# TASK: evaluate_risk -> 1 & 2
# ------------------------------------------
passes_ucon if {
    eval_tasks := {"evaluate_risk_1", "evaluate_risk_2"}
    input.action.task in eval_tasks

    # --- Auth Checks --- #
    # onA1,3: active_loan_reviews <= 10
    input.environment.history.active_loan_reviews <= 10

    # onA1,2,3: pending_inactive_reports <= 5
    input.environment.history.pending_inactive_reports <= 5

    # --- Obligation Checks --- #
    # onB0: Review while control time system is active
    input.environment.control_time_system_active == true

    # --- Condition Checks --- #
    # onC0: Allowed to review during office hours (9 am - 17 pm)
    time := input.environment.current_time
    time >= "09:00:00"
    time <= "17:00:00"
}

# ------------------------------------------
# TASK: send_approved_notification
# ------------------------------------------
passes_ucon if {
    input.action.task == "send_approved_notification"

    # --- Obligation Checks --- #
    # onB1,3: has to ask for the reports so there's a rate 
    "rate" in object.keys(input.object)
}

# ------------------------------------------
# TASK: open_loan_file
# ------------------------------------------
passes_ucon if {
    input.action.task == "open_loan_file"

    # --- Obligation Checks --- #
    # onB2: ack the receipt
    input.object.ack.ack == true
    input.object.ack.days <= 2
}