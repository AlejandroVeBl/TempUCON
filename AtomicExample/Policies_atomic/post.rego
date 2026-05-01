# --- POST ---
package ucon.post

default allow = false

allow if {
    input.action.task == "Activity_A"
}