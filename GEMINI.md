# Gemini Best Practices

This document outlines best practices for contributing to this project, specifically regarding Git commits.

## Git Commit Messages

- When writing a git commit message, wrap lines at 70 columns.
- Indent the continuation lines of "-" bullet points two spaces so they line up.

## Commit Granularity

- Prefer small commits that do exactly one thing. For example, a commit that refactors code and another commit that fixes a bug should be split into two separate commits.
- As an example, the previous commit for `DiaryPage.py` could have been split into two commits:
    1.  One for "Extract layout-specific logic from the 'body' method into dedicated private methods"
    2.  And another for "Reduce code duplication in 'print*WTO' and 'print*WTP' methods and fix simulated dynamic scope".
