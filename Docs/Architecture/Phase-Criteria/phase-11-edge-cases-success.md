# Phase 11: Evaluation Suite - Edge Cases and Success Criteria

## Detailed Edge Cases
- Eval edge: judge inconsistency across reruns on same case.
- Dataset edge: golden set lacks blended M1+M2 scenario coverage.
- Safety edge: adversarial prompt phrasing bypasses rule-based checks.
- UX edge: voice top-theme mention check not tied to latest pulse snapshot.
- Runtime edge: one failing case aborts full eval run.

## Success Criteria
- Golden dataset includes 5 blended M1+M2 questions with expected evidence.
- Safety dataset includes at least 3 adversarial prompts and reaches 100% refusal for prohibited requests.
- Faithfulness and relevance are scored and reported per case.
- UX checks confirm pulse structure and voice top-theme mention behavior.
- Output report is published to `Docs/Architecture/Evals-Report.md`.
