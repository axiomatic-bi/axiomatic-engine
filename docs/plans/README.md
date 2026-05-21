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

## Current Status

### NHS Inequality Analysis Project v1

| Phase | Status | Branch | Notes |
|-------|--------|--------|-------|
| 1. Engine ZIP Support | **Done** | `feat/1-zip-streaming` | Implemented, tested, committed |
| 2. RTT Ingestion | **Todo** | TBD | Create `projects/nhs_inequality/` |
| 3. Analysis Models | **Todo** | TBD | dbt models for ICB patterns |
| 4. ODS/IMD | **Deferred v1.1** | - | See ADR-001 |
| 5-7. Models/Docs | **Todo** | TBD | After Phase 2-3 |

### Latest Commit
- Branch: `feat/1-zip-streaming`
- Status: ZIP streaming implemented in `http_stream.py`
- Tests: 53 passed
- Pre-commit: Passed
- Next: Push branch, create PR, start Phase 2

### Bootstrap for New Chat
```
Working on NHS inequality project v1. 
Phase 1 complete (ZIP streaming in http_stream.py).
Starting Phase 2 per docs/plans/current/nhs-inequality-v1.md.
Branch: feat/1-zip-streaming
```

---

**Next Steps**: 
1. Push `feat/1-zip-streaming` branch
2. Create GitHub issue #1 (retroactively) or PR directly
3. Start Phase 2: Create `projects/nhs_inequality/` structure
