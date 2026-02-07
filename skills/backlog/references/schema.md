# Backlog JSON Schema

## Root Structure

```json
{
  "metadata": {
    "version": "1.0",
    "created_at": "ISO-8601",
    "updated_at": "ISO-8601"
  },
  "stories": [ ... ],
  "questions": [ ... ]
}
```

## User Story Object

```json
{
  "id": "US-001",
  "title": "Short descriptive title",
  "feature_area": "Feature group name",
  "priority": "Must | Should | Could | Won't",
  "role": "The user role in the story",
  "want": "The capability described",
  "benefit": "The business benefit",
  "acceptance_criteria": [
    {
      "id": "AC-001.1",
      "given": "Context/precondition",
      "when": "Action performed",
      "then": "Expected result"
    }
  ],
  "notes": "Additional context, edge cases, business rules",
  "dependencies": ["US-002", "US-003"],
  "status": "Draft | Ready | In Design | Validated | In Progress | In Review | In Testing | Done | Blocked | Cancelled",
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601",
  "created_by": "po | pm",
  "history": [
    {
      "action": "created | edited | status_change",
      "by": "agent caller",
      "at": "ISO-8601",
      "changes": ["field1", "field2"],
      "from": "old_status",
      "to": "new_status"
    }
  ]
}
```

## Question Object

```json
{
  "id": "Q-001",
  "text": "The question text",
  "asked_by": "agent caller",
  "asked_at": "ISO-8601",
  "resolved": false,
  "answer": "",
  "resolved_by": "agent caller",
  "resolved_at": "ISO-8601"
}
```

## Status Flow

```
Draft → Ready → In Design → Validated → In Progress → In Review → In Testing → Done
                                              ↓                          ↓
                                           Blocked                    Blocked
Any status → Cancelled
```

## Role Permissions

| Operation | po | pm | tl | dev | qa |
|-----------|----|----|----|----|-----|
| Create US | Y  | Y  | N  | N  | N  |
| Edit US   | Y  | Y  | Y  | N  | N  |
| Status    | Y  | Y  | Y  | Y  | Y  |
| Delete US | Y  | Y  | N  | N  | N  |
| Question  | Y  | Y  | Y  | Y  | Y  |
