# Summary-level results only

The tables under this directory are **author-computed statistics**, not DCML source annotations or a substitute for the full pinned source corpus.

All four candidate-event frames were rebuilt from the corresponding source TSV files. The model output is specific to expert-annotated PAC/IAC outcomes and should not be interpreted as listener perception or a causal effect.

| Event definition | Events | PAC/IAC | Interaction OR (95% CI) |
|---|---:|---:|---:|
| Written strict I/i | 14,740 | 2,084 | 9.48 (5.52–16.28) |
| Written applied-target proxy | 16,951 | 2,090 | 8.08 (4.84–13.50) |
| All-endings strict | 14,853 | 2,135 | 7.09 (4.26–11.80) |
| All-endings and applied-target | 17,065 | 2,141 | 6.16 (3.78–10.07) |

Raw DCML files are **not** redistributed. Run the scripts with the pinned upstream source data to reconstruct event-level data, all-composer holdout metrics, bootstrap confidence intervals, and individual file hashes. The all-endings coordinate is not an unfolded performance reconstruction.

The accompanying `adjusted_interaction_across_definitions.csv` supplies machine-readable values underlying this table.
