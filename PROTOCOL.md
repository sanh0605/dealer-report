# PROTOCOL.md - Strict Operating Guidelines

## 1. Communication & Clarity
- **Clarification First:** If any instruction or requirement is unclear, the agent MUST stop and ask for clarification immediately before proceeding.
- **No Assumptions:** Never assume user intent for architectural or business logic. Surface ambiguity as an inquiry.
- **No Symbols:** The use of the `->` or `$\rightarrow$` symbol is strictly forbidden. Use plain text like "links to," "identifies," or "maps to."

## 2. Workflow & Approval
- **Brainstorming First:** Use the `brainstorming` skill before any creative work or feature addition. Propose 2-3 approaches with tradeoffs and wait for approval.
- **Visual Mockups:** Offer the visual companion when a topic involves UI or complex data layouts.
- **Feature Development:** Use the `feature-dev` skill for systematic implementation: Discovery -> Exploration -> Design -> Implementation -> Testing -> Review.
- **Show Final Result:** Before completing any topic or phase, a complete summary of the result must be presented.
- **Explicit Approval:** The agent is NOT allowed to move to the next step or topic until the user provides explicit approval of the current result.
- **Conflict Review:** After writing any plan or schema, the agent must review it against ALL existing `.md` files to ensure no contradictions or single points of confusion exist.

## 3. Engineering & Quality (Iron Laws)
- **TDD (Test-Driven Development):** NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST. Every feature or bugfix MUST start with a minimal test that fails for the expected reason. Watch it fail, then write minimal code to pass.
- **Systematic Debugging:** NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST. Reproduce the bug, trace the data flow, and find the root cause before proposing any solution.
- **Debugging Limits:** If 3+ fixes fail, STOP and question the architecture with the user. Do not attempt a 4th fix without an architectural discussion.
- **Frontend Design:** Avoid "AI slop" aesthetics. Commit to a bold, distinctive aesthetic direction (typography, color, motion) and execute it with precision. Use `brainstorming` to validate the design first.
- **Context7:** Always use `context7` to fetch up-to-date documentation for libraries/frameworks rather than relying on training data.
- **Think Before Code:** Adhere to Karpathy Guidelines. Define the logic and test cases in the research/strategy phase before implementation.
- **Test All Situations:** Testing must cover edge cases, locale-specific formats (e.g., Vietnamese date/time), and data integrity (e.g., ID fields as text).
- **Zero-Error Presentation:** Code or technical solutions must be verified and error-free before being presented to the user.
- **Permanent Documentation:** All project rules, schemas, and plans must be written in `.md` files, not stored in the agent's session memory.
