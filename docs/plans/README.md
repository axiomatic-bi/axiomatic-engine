# Planning Documentation

This directory contains planning documents and architecture decision records (ADRs) for the Axiomatic Engine and associated projects.

## Structure

```
docs/plans/
├── README.md                    # This file
├── current/                     # Active plans
│   └── nhs-inequality-v1.md    # Current project plan
├── decisions/                   # Architecture Decision Records (ADRs)
│   ├── 001-ods-deferred.md
│   └── 002-zip-api-design.md
└── templates/                   # Templates for GitHub issues
    └── issue-template.md
```

## Workflow

### Phase 1: Planning (Markdown)
1. Create/edit planning docs in `current/`
2. Record significant decisions in `decisions/`
3. Iterate on scope until clear

### Phase 2: Tickets (GitHub Issues)
Once planning is solid:
1. Create GitHub issue using template from `templates/issue-template.md`
2. Use `.github/ISSUE_TEMPLATE/` for structured issues
3. Link planning doc in issue body
4. Add to GitHub Project board

### Phase 3: Active Work (Issues + PRs)
1. Self-assign issue
2. Create branch
3. Open PR referencing issue (`Closes #42`)
4. Move issue to "In Progress" on project board
5. Merge when approved, issue auto-closes

## Status Definitions

- **Planning**: Documented but not yet ticketed
- **Todo**: Ticket created, ready to start
- **In Progress**: Assigned, work underway
- **Review**: Awaiting code review
- **Done**: Completed, merged

## Creating New Issues

From a planning doc, create GitHub issues with:

```bash
# Manual approach
gh issue create \
  --title "[ENGINE] Add ZIP archive streaming" \
  --body "See docs/plans/current/nhs-inequality-v1.md\n\n## Objective..." \
  --label "area/engine,kind/enhancement"
```

Or use GitHub web UI with issue templates.

## Decision Records

Format: `NNN-title.md`

- Record significant architectural choices
- Include context, decision, rationale, consequences
- Reference from planning docs and issues

---

**Next Steps**: Create GitHub issues for Phase 1 work (ZIP streaming)
