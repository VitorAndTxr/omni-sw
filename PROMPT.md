## Purpose

Plan the construction of a skill that orchestrate and manages the workflow described by `README_AGENCY.md` and `docs\agency\phase-walkthrough.md` through the spawn of agents and sub-agents using de tools `TeamCreate` and `Task` using the skills `/pm`, `/po`, `/tl`, `/dev` and `/qa`

## Instructions

1. Read `README_AGENCY.md` and its dependencies
2. Plan a skill called `/orchestrator` that manages and execute de flow described by the `README_AGENCY.md` through `TeamCreate` and `Task` to plan and implement the objective discribed by a prompt passed as argument to the slash command

## Important

- The orchestrator should bring questions from the team to the user to be answered before it continues the work
- The `/orchestrator` should enforce the application of the Agency to the flow and delegate the job to be made by `/pm`, `/po`, `/tl`, `/dev` and `/qa` skills as defined in the flow
