# Decisions

## 2026-07-15: Keep long real-audio fixtures local

`tests/test_data/test*.m4a` remains gitignored because these files are approximately 50-minute recordings with original creation metadata and may contain personal meeting information. They are local integration fixtures, not reproducible or publishable project assets.

Short generated fixtures named `tests/test_data/short*.m4a` are tracked for deterministic repository tests. Tests requiring long recordings must skip clearly when local fixtures are absent or move to an explicit external-fixture workflow.
