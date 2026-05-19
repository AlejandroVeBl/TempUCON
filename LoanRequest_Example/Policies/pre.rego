package ucon.pre

# Don't allow by default
default allow := false

# ===========================================================================
# MAIN RULE
# ===========================================================================
# To allow it has to pas the RBAC role membership check and the UCON rules
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
# UCON: PRE-Checks
# ===========================================================================

default passes_ucon := false

# ------------------------------------------
# TASKS WITHOUT EXPLICIT UCON PRE CHECKS PASS DIRECTLY
# ------------------------------------------
passes_ucon if {
    tasks_without_ucon := {
        "fulfil_loan_info", 
        "collect_customer_information", 
        "receive_loan_request", 
        "send_approved_notification", 
    }
    input.action.task in tasks_without_ucon
}

# ------------------------------------------
# TASK: request_a_loan
# ------------------------------------------
passes_ucon if {
    input.action.task == "request_a_loan"

    # --- Auth Checks --- #
    # preA1: (remuneration - cost) > (remuneration / 2)
    remuneration := input.object.customer.remuneration
    cost := input.object.cost
    (remuneration - cost) > (remuneration / 2)

    # preA3: active_loans < 3
    input.environment.history.active_loans < 3

    # --- Obligation Checks --- #
    # preB0: gdpr
    input.object.gpdrAgreement.gpdrValidated == true

    # preB1: loan terms
    input.object.loanTerms == true

    # --- Condition Checks --- #
    # preC0: not a phone
    input.environment.device_type != "mobile"
}

# ------------------------------------------
# TASK: evaluate_risk -> 1 & 2
# ------------------------------------------
passes_ucon if {
    input.action.task == "evaluate_risk_1"
    # evaluate_risk_1 has no additional checks
}

# --- Auth Checks --- #
# preA0: SoD
# Helper checks in the history if the user trying to do the current task did evaluate_risk_1
user_did_eval_1 if {
    some entry in input.environment.history.tasks_done
    entry[0] == "evaluate_risk_1"
    entry[1] == input.subject.username
}

passes_ucon if {
    input.action.task == "evaluate_risk_2"
    not user_did_eval_1
}

# ------------------------------------------
# TASK: open_loan_file
# ------------------------------------------
passes_ucon if {
    input.action.task == "open_loan_file"
    
    req := input.object.loan_request
    
    old_balance := req.customerAccount.old_balance
    new_balance := req.customerAccount.balance
    amount := req.amount
    cost := req.cost
    
    # preB3: Balance = old + loan - costs
    new_balance == (old_balance + amount) - cost
}