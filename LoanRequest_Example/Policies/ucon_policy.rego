package ucon.policy

import rego.v1

# By default it returns allow false
default allow = true

# ---------------------------------------------------------
# Route the request depending on which type of check it is: (Pre/On/Post)
# ---------------------------------------------------------

allow if {
    print(">>> Evaluating PRE check. User:", input.user)
    input.phase == "pre"
    pre_allow
}

allow if {
    print(">>> Evaluating ON check. User:", input.user)
    input.phase == "on"
    on_allow
}

allow if {
    print(">>> Evaluating POST check. User:", input.user)
    input.phase == "post"
    post_allow
}

# ---------------------------------------------------------
# Logic for each path
# ---------------------------------------------------------

# --- PRE ---
default pre_allow = false
pre_allow if {
    # It has to receive a user
    input.user != null
}

# --- ON ---
default on_allow = false
on_allow if {
    # TODO
    input.user != null
}

# --- POST ---
default post_allow = false
post_allow if {
    # It has to receive what and who completed for future checks
}