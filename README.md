# TempUCON
# Dynamic Usage Control (UCON) in Workflow Orchestration

## Overview
This repository contains the implementation of a dynamic, continuous access control system based on the **Usage Control (UCON)** model. Designed for modern, event-driven orchestration environments, this project integrates **Temporal.io** and **Open Policy Agent (OPA)** to provide resilient, stateful, and context-aware security for long-running workflows and human-in-the-loop tasks.

This project was developed as part of a Bachelor's Thesis.

## Key Features
- **Continuous Authorization:** Implements `pre`, `on`, and `post` authorization phases to monitor context and attribute changes during task execution.
- **Policy as Code:** Decouples security logic from business logic using OPA and Rego language.
- **Resilient Workflows:** Leverages Temporal.io's event sourcing to ensure state recovery and fault tolerance.
- **PEP-PDP-PIP Architecture:**
  - **PEP (Policy Enforcement Point):** Python-based Temporal workflow function that handles the human tasks.
  - **PDP (Policy Decision Point):** Open Policy Agent (OPA) evaluating dynamic constraints.
  - **PIP (Policy Information Point):** OAuth 2.0 based attribute management (EasyAuth) supplying subject metadata.
