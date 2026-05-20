# Issue Template

Use this template when converting planning docs to GitHub issues.

```markdown
---
<!-- Frontmatter for tracking -->
phase: 1 | 2 | 3 | 4 | 5 | 6 | 7
estimated_hours: 
dependencies: #issue_numbers
---

## Objective
Clear statement of what this issue delivers.

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Context
Link to planning doc: `docs/plans/current/...`

Relevant decisions: `docs/plans/decisions/...`

## Implementation Notes
<!-- Add notes as work progresses -->

## Review Request
<!-- Fill this in when moving to review -->
@reviewer Please check:
1. 
2. 

## Related
- Planning doc: 
- Decision record: 
- Previous related issue: #
```

## Workflow

1. **Create**: Copy this template to new GitHub issue
2. **Assign**: Self-assign or assign to agent
3. **Update**: Add implementation notes as you work
4. **Review**: Fill in Review Request section, tag reviewer
5. **Close**: Link PR that closes this issue
