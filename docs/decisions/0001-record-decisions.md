# 1. Record architecture decisions

Date: YYYY-MM-DD
Status: Accepted

## Context

A design choice made during the project (why a high-water mark instead of a
fixed time window, why dbt, why this chunk size) is the first thing an
interviewer asks about, and the easiest thing to forget.

## Decision

Every choice with a real alternative gets a short record in this folder,
numbered in order: `0002-use-high-water-mark.md`, `0003-…`.

Each record answers four questions:

1. **Context**: what problem forced a choice?
2. **Options**: what else was possible? (at least two)
3. **Decision**: what was chosen and why?
4. **Consequences**: what does it cost, and what would make you change it?

## Consequences

About ten minutes per decision. In return, the README's "Key decisions" section
writes itself and the interview answer is already prepared.
