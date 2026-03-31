package ucon.post

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
# UCON: POST-Checks
# ===========================================================================

default passes_ucon := false

# ------------------------------------------
# TASKS WITHOUT EXPLICIT UCON ON CHECKS
# ------------------------------------------
# It's all of them for this example
passes_ucon if {
    # There are no post checks in the example
    all_tasks := {
        "fulfil_loan_info", 
        "request_a_loan",
        "collect_customer_information", 
        "receive_loan_request", 
        "evaluate_risk_1",
        "evaluate_risk_2",
        "send_approved_notification", 
        "open_loan_file"
    }
    input.action.task in all_tasks
}