## Purpose

Plan the construction of a skill that will be used to this claude plugin that will replace the backlog documentation and consume to better organizer the proccess of consumption by the agents

## Instructions

`docs\templates\BACKLOG.md` management must be replaced by a skill that manages a table or a json with scripts and predefined roules and communication interface.

- Only `/po` and `/pm` can `CreateNewUs`
- Only `/po`, `/pm` and `/tl` can edit description of a Us
- `/dev` and `/qa` can only change Backlog status
- All project backlog data shoud be in `/agent_docs/backlog` folder of the project
- Backlog.md shoud be a resume and have a reference to how to use the system

The system must be based on the orchestration of the elements using `TeamCreate` and `Task` tools

Reforce a agencia descrita em `README_AGENCY.md`
