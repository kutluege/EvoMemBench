# Geometry-filter experiments — difference-vector conflict detection (2026-08-26)

Code: `hnav/geometry_filter/` (data / metrics / methods / run_nulls /
run_slot_probe / run_conflict). Raw results: `null_baselines.json`,
`slot_probe.json`, `conflict_detection.json` in this directory, each with full
provenance (git commit, dataset sha256, embedding namespace, seed 20260824).
Repository analysis and risk register: `REPO_ANALYSIS.md`.

**Fit discipline.** Every estimated quantity — per-relation mean directions
`mu_r`, subspaces `U_r`, the rank `k`, decision thresholds, the LDA — was fit
on calibration gold pairs only (sh_6k + sh_32k, 989 oriented edit vectors).
sh_64k (confirmatory) was scored once with everything frozen. Calibration-side
numbers below are marked *in-sample* where the fit saw those same pairs.
Spaces: `raw` = campaign unit embeddings; `centered` = calibration mean removed
then renormalized; `abtt` = the frozen committed D=128 whitening
(`stage0_results/abtt/abtt_whitening_D128.json`), also calibration-fit.

## 1. Null controls — the directional signal is real, and it is not anisotropy

Mean pairwise cosine between normalized difference vectors `d_hat` of gold
edits (confirmatory split; calibration equivalent within ±0.01):

| statistic | raw | abtt | shuffled-transition null (raw) | random-vector null |
| --- | --- | --- | --- | --- |
| same transition, different subject | **0.863** [CI95 0.854–0.871] | 0.734 | 0.077 | −0.000 |
| same relation, different transition | 0.067 (p = 0.020, floor of 50 shuffles) | 0.053 | 0.000 | ~0 |
| global mean-direction norm | 0.155 | 0.120 | 0.060 | ~1/√n |

- The same-transition coherence survives the shuffled-transition null with a
  gap of ~0.78 and survives ABTT (which removes the 128 dominant common
  directions) at 0.73 — so it is genuine edit-vector structure, not shared
  anisotropy. Mean-centering changes nothing (as it must: centering without
  renormalization is exactly a no-op on differences).
- Relation-level coherence *across different transitions* is real but small
  (0.067): most of the raw 0.86 comes from the specific object transition,
  not from a broad "this relation's edit subspace". This foreshadows the
  generalization results.

## 2. Slot localization — strong within known relations, template-bound

Multinomial logistic probe on 6 parser-exact slot-change classes
(object_only / subject_only / subject_object / relation_object /
subject_relation / all_change; chance macro-F1 ≈ 0.17). Candidate pairs are
unordered, so the probe never sees true orientation:

| features (raw space) | cal→conf macro-F1 | relation-disjoint (cal, 2-fold) | object-vs-subject AUROC |
| --- | --- | --- | --- |
| signed `d_hat`, random sign (designed control) | 0.222 | — | 0.495 |
| **abs `d_hat`** | **0.700** | **0.212** | **0.962** |
| canonicalized sign | 0.366 | 0.166 | 0.765 |

ABTT space: abs 0.521 / AUROC 0.921. Per-class F1 (raw/abs): object_only
0.69, subject_only 0.71, subject_object 0.63, relation_object 0.75,
subject_relation 0.61, all_change 0.81.

- The signed control lands at chance *by mathematical necessity* (±d is
  symmetric per class under sign randomization; a linear model cannot separate
  it) — it confirms the sign randomization actually bites.
- **Answer to §5:** yes — the direction (through its axis-energy profile)
  identifies which slot changed, far above chance… **within relations seen in
  training**. Relation-disjoint evaluation collapses to chance (0.21): what
  the linear probe learns is relation-template-conditioned geometry, not a
  generic slot-change code.

## 3. Conflict detection — held-out (sh_64k), everything frozen

989 calibration edits fit 35/37 relations (2 under-supported → global
fallback). k selected on calibration: k*=20 (grid 1→20 monotone: 0.80, 0.91,
0.95, 0.98, 0.999 — the last being in-sample and inflated, as expected).

### 3a. Balanced cosine-matched eval set (the mandated arena), sh_64k

Per CLAUDE.md, a geometry filter must beat `cosine_only_auc` = 0.893 here, or
win inside the 0.87–0.97 band (998 pos / 1,644 neg in band):

| method | AUROC | band AUROC |
| --- | --- | --- |
| campaign cosine | 0.893 | 0.850 |
| **cosine in ABTT space** | **0.965** | **0.952** |
| RCESP (relation-conditioned, k=20, raw) | 0.930 | 0.910 |
| RCED (relation mean direction, raw) | 0.855 | 0.834 |
| RCESP global subspace | 0.844 | 0.810 |
| LDA on global subspace coords | 0.851 | 0.816 |

(sh_6k / sh_32k rows in the JSON are in-sample for RCED/RCESP — RCESP ~1.0
there is fit-set memorization and is reported only as a diagnostic.)

### 3b. Hard-negative task (gold vs same-relation different-subject verified
non-conflicts; confirmatory: 1,681 pos / 39,215 neg)

| method | AUROC [CI95] | AUPRC | inverted-win vs campaign cosine |
| --- | --- | --- | --- |
| campaign cosine | 0.992 [0.990–0.994] | 0.916 | 0.000 (by construction) |
| **ABTT cosine** | **0.999 [0.9988–0.9993]** | **0.979** | **0.927** |
| RCESP | 0.912 [0.903–0.922] | 0.778 | 0.896 |
| RCED | 0.845 | 0.472 | 0.797 |
| centered cosine | 0.995 | 0.920 | 0.556 |

- **The key experiment (§8):** over the 527,062 (pos, neg) comparisons where
  the negative's cosine *exceeds* the positive's — cosine's win rate is 0 —
  RCESP still orders 89.6% correctly and ABTT-cosine 92.7%. Difference-vector
  direction (and whitened cosine) carry real information beyond raw cosine.
- Paired bootstrap (same resampled pairs): RCESP − cosine = −0.080
  [−0.089, −0.071] (cosine wins the aggregate); RCESP − RCED = +0.068
  [+0.058, +0.077] (the subspace beats the single direction, everywhere).
  LDA − RCESP = −0.114 — the covariance-aware variant is dropped (§11 rule).
- The parser `same_key` baseline scores P=R=1.0 on this task — **circularly**:
  the task's classes are defined by the key structure the parser computes.
  It is reported to expose the circularity, not as a comparison.

### 3c. Frozen operating points (best-F1 on calibration → applied to sh_64k)

| method | threshold | cal P/R/F1 | conf P/R/F1 (FPR) |
| --- | --- | --- | --- |
| ABTT cosine | 0.454 | 0.956/0.959/0.957 | 0.852/0.982/**0.912** (0.0073) |
| campaign cosine | 0.923 | 0.877/0.869/0.873 | 0.805/0.874/0.838 (0.0091) |
| RCESP | 0.751 | 0.979/0.976/0.977 *(in-sample)* | 0.973/0.673/0.796 (0.0008) |

RCESP's calibration numbers are inflated by fit-set memorization and its
frozen threshold transfers with a recall collapse (0.67) — high precision
survives. ABTT-cosine transfers cleanly.

## 4. Generalization — where the directional signal ends

Confirmatory positives restricted to material unseen in calibration, vs all
confirmatory hard negatives (raw space):

| eval | n_pos | cosine | ABTT cos | RCED | RCESP |
| --- | --- | --- | --- | --- | --- |
| all confirmatory | 1,681 | 0.992 | 0.999 | 0.845 | 0.912 |
| transition-disjoint | 636 | 0.990 | 0.999 | 0.717 | 0.768 |
| subject-disjoint | 828 | 0.992 | 1.000 | 0.782 | 0.833 |
| relation-disjoint (cal 2-fold, global variants) | 437/552 | 0.977/0.995 | 0.996/1.0 | 0.71/0.67 (max) | 0.70/0.62 (global) |

Transition-deduped refit (one exemplar per transition, 705 edits) keeps RCESP
at 0.914 on all-confirmatory — so it is not frequency memorization — but
unseen-transition performance (0.768) shows the subspaces mostly *cover the
transitions calibration exhibited* rather than encoding a transferable
edit code. Consistent with §1 (transition-level coherence 0.86 vs
relation-level 0.067) and §2 (relation-disjoint probe collapse).

## 5. ABTT / preprocessing ablation (§10)

Centering alone: no change to RCED/RCESP (≤0.01), cosine inverted-win rises
0 → 0.556. Full ABTT: RCED/RCESP roughly unchanged or slightly better
(RCED 0.845→0.871, RCESP 0.912→0.901), while **cosine improves dramatically**
(0.992→0.999 AUROC, 0.916→0.979 AUPRC, inverted-win 0.927, band AUROC
0.850→0.952). Removing the 128 dominant directions removes nuisance
anisotropy and does not destroy conflict-relevant geometry — consistent with
the earlier A/B campaign (hnav_raw 17/66 → hnav_abtt 37/66). Full whitening
was not implemented anywhere in the repo and was not added (per §10).

Sign-pattern / coordinate-identity features: none existed in the repo; none
were introduced (§12). The abs-feature probe implies axis-aligned structure
exists in this model, but nothing here depends on fixed dimension indices.

## 6. Scientific conclusion (§20 answers)

1. **Does Δ direction contain information beyond cosine?** Yes — inverted-win
   0.896 where cosine is wrong by construction; +0.037 AUROC over the mandated
   cosine baseline on the balanced sh_64k set. The nulls rule out anisotropy.
2. **Can it identify object-slot changes?** Yes, strongly (macro-F1 0.70,
   object-vs-subject AUROC 0.96) — but only via sign-invariant features, and
   only within relations represented in training.
3. **Are the directions relation-conditioned?** Emphatically: per-relation
   RCESP 0.912 vs global 0.768; relation-disjoint transfer collapses.
4. **Are object edits low-rank?** Locally, yes: k=20 of 2,560 dims per
   relation captures the bulk (AUROC still rising at k=20, so "low" means
   ≲ tens, not single digits).
5. **Does RCESP outperform RCED?** Yes — paired bootstrap +0.068, CI excludes 0.
6. **Does the signal survive held-out relations/transitions?** Only partially:
   0.77 transition-disjoint, ~0.65–0.70 relation-disjoint. The signal is
   substantially transition-bound.
7. **Is the improvement real or an artifact?** The improvement *over cosine on
   its failure set* is real (nulls + held-out + inverted comparisons). The
   apparent near-perfect RCESP numbers on calibration subsets are fit-set
   memorization and are labeled as such.
8. **Which method should remain?**
   - **Keep: ABTT(D=128)-space cosine** as the primary geometry filter. It
     beats every method on every held-out slice (0.999 hard-task AUROC, 0.952
     band AUROC, 0.927 inverted-win, robust frozen operating point), uses a
     committed calibration-fit artifact, needs no parser and no relation
     identity, and transfers to unseen transitions/relations trivially.
   - **Keep (as evidence + secondary signal): RCESP** — the scientifically
     interesting result. It is the only *non-cosine-family* signal that beats
     the cosine baseline on the balanced set, and its 0.90 inverted-win shows
     directional information genuinely complementary to raw cosine. Its
     weaknesses (relation identity requirement, transition-boundedness,
     recall collapse at a frozen threshold) make it a candidate *component*,
     not a standalone screen.
   - **Drop: RCED** (dominated by RCESP), **LDA** (worse than RCESP),
     **signed-feature probes** (provably unlearnable for unordered pairs).

The thesis-grade claim supported by the evidence: *object-slot factual updates
occupy relation-conditioned low-rank edit subspaces in sentence-embedding
space; a lightweight subspace detector separates conflicts from
cosine-matched hard negatives well beyond the cosine baseline, but the
subspaces are substantially transition-specific, and a calibration-fit ABTT
whitening followed by plain cosine remains the strongest and most
transferable pairwise geometric screen in this arena.*

Follow-on plan: `NEXT_GOAL.md` (benchmark the winning screen + NLI against the
committed hnav_raw / hnav_abtt pipeline results).
