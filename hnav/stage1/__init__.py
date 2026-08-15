"""Stage-1 (read-path rerank) offline tooling.  [T11]

Like ``hnav/stage0/``, everything here is OFFLINE and may read benchmark
questions and answers; nothing under ``hnav/core/`` or ``hnav/adapters/`` may
import from it (the leakage audit scans those trees). Calibration is bound to
the sh_6k + sh_32k split — the confirmatory subsets are refused by the
scripts themselves.
"""
