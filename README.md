# Music-theory cadence transportability: reproducible analysis (V3.3)

This public research-code repository reproduces the analyses supporting a working study of expert-annotated authentic cadences in classical keyboard repertoires. The analyses concern **expert symbolic annotations**, not directly measured listener perception or causal effects. The work is a working manuscript and is not described here as accepted or published.

## Source data: third-party, not redistributed

Original DCML score/annotation files are hosted by the Distant Listening Corpus and its composer-specific repositories. **Do not treat the code licence in this repository as a licence for those data.** Individual DCML repositories indicate CC BY-NC-SA 4.0; refer to each repository for the applicable terms. We provide source references, locked commit identifiers, and a per-file hash manifest but do not re-upload the original harmonies TSV files or the derived event-level annotation dataset.

Original data descriptor: Hentschel J, Rammos Y, Neuwirth M, Rohrmeier M (2025). *A corpus and a modular infrastructure for the empirical study of (an)notated music*. *Scientific Data* 12:685. https://doi.org/10.1038/s41597-025-04976-z. Corpus archive: https://doi.org/10.5281/zenodo.15150283.

### Pinned source commits

| DCML repository | Commit |
|---|---|
| `beethoven_piano_sonatas` | `ea7181bff88abc8713257234f7ec4033178c57a9` |
| `cpe_bach_keyboard` | `4b3511eab12b5fbfc7aa5c75819ee02225430da8` |
| `jc_bach_sonatas` | `ac9fd07905eb62c3d8cfbd96811491170a216232` |
| `mozart_piano_sonatas` | `5337257a5318711e6302cfe85c3f1a6ade3c6271` |
| `kozeluh_sonatas` | `23c1983a48809647af1a08d54b1fade39ec93995` |

The Koželuch corpus was excluded from supervised cadence prediction because the inspected harmony files contained no PAC/IAC annotations; this is not evidence that its compositions lack authentic cadences. There are 267 verified selected source files (262 harmonies + five metadata tables). See `provenance/SOURCE_FILES_SHA256_GIT_BLOB.csv`.

## Reproduction

Requires Python 3.10 or newer and scientific libraries in `requirements.txt`. The numeric result archive was computed with the exact versions listed there. Install with `python -m pip install -r requirements.txt` in a dedicated environment.

1. Download each source repository as a ZIP at the **specified commit**, unpack it, and rename the extracted top-level folder to its repository name. The resulting source folder must contain five directories with `metadata.tsv` and `harmonies/*.harmonies.tsv`.
2. Archive these five directories together into `five_corpora.zip`, without adding nested parent directories. Alternatively, use an existing locally held ZIP with that structure.
3. Run:

```bash
python code/01_reproduce_from_zip.py --data-zip five_corpora.zip --out ./reproduction
```

The reproducibility script creates four candidate-event frames (strict I/i, local-applied target, all-endings score coordinate, both extensions), estimates robust associations, evaluates held-out-composer models, calculates grouped bootstrap AP contrasts and freezes local source hashes.

`data_summary/` contains summary-level output values underpinning the reported statistical tables. The study uses 14,740 strict-frame candidate events (2,084 PAC/IAC positive annotations; four composers, 85 work groups). Sensitivity frame sizes: 16,951/2,090; 14,853/2,135; 17,065/2,141 (events/PAC-IAC labels). These numbers must be compared to re-execution output. All-endings is an *alternative notated score coordinate*, not a reconstructed sequence of a performance.

## Permissions, responsibilities and limits

- Repository scripts are made available for public scientific reuse under the [MIT licence](LICENSE) for author-generated scripts only.
- The DCML source annotations and any substantial source-derived annotation tables retain the original third-party licence conditions; this repository does **not** relicense them.
- The source `cadence`, `numeral`, and `localkey` fields share expert analytical provenance. Cross-composer validation of these labels does not independently validate musical perception.
- Some analyses (including alternate sample definitions and ablations) are exploratory or post hoc. This repository is not an ethics approval, publisher acceptance or author-contribution certification.

## Files

- `code/01_reproduce_from_zip.py`: complete orchestration.
- `code/02_rebuild_alternative_frames.py`: event definition and source parsing.
- `code/03_fit_four_frames.py`: regression and validation.
- `code/04_freeze_source.py`: source integrity.
- `data_summary/`: aggregate results for manuscript tables.
- `provenance/`: exact source file and commit hashes.

The study's final publication, if accepted, must cite the specific public code version/commit (and ideally an archival DOI). Author identity, final declaration text, and the journal's submission PDF are *not* part of the reproducibility data.