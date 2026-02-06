# Architecture Diagrams

Visual representations of the agency's structure and workflow.

## Agent Hierarchy

```mermaid
graph TB
    PM["PM<br/>Product Manager"]
    PO["PO<br/>Product Owner"]
    TL["TL<br/>Tech Lead"]
    Dev["Dev<br/>Developer Specialist"]
    QA["QA<br/>QA Specialist"]

    PM -->|manages| PO
    PM -->|manages| TL
    PO -->|assigns tasks| Dev
    PO -->|assigns tasks| QA
    TL -->|reviews work| Dev
    TL -->|reviews work| QA
```

The PM sits at the top of the management layer, managing both the PO and TL. The PO assigns tasks to Dev and QA. The TL reviews the technical output of Dev and QA.

## Orchestration Flow

```mermaid
graph LR
    Plan["Phase 1<br/>Plan"] --> Design["Phase 2<br/>Design"]
    Design --> Validate["Phase 3<br/>Validate"]
    Validate --> Implement["Phase 4<br/>Implement"]
    Implement --> Review["Phase 5<br/>Review"]
    Review --> Test["Phase 6<br/>Test"]
    Test --> Document["Phase 7<br/>Document"]
```

## Feedback Loops

```mermaid
graph LR
    Plan --> Design --> Validate --> Implement --> Review --> Test --> Document
    Validate -->|"PM reproves"| Plan
    Validate -->|"TL reproves"| Design
    Review -->|"blocking issues"| Implement
    Test -->|"bug failures"| Implement
```

Three feedback loops exist. Validation failure routes back to Plan (business) or Design (technical). Blocking issues in Review send the workflow back to Implement. Test failures caused by bugs also return to Implement.
