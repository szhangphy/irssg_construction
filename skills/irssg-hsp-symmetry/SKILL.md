---
name: irssg-hsp-symmetry
description: Determine material space, magnetic, and spin space group information from magnetic POSCAR-like mPOSCAR files or magnetic CIF/mcif files using IRSSG, then fetch full related HSP web/API records for the identified SG, MSG, and SSG. Use when Codex needs to run or guide IRSSG-based symmetry identification, extract SG/MSG/SSG numbers and symbols, output complete symmetry operations, Wyckoff positions, high-symmetry k-vectors, generated ssg.data/msg.data artifacts, or prepare downstream spin-group workflows from mPOSCAR or mcif input.
---

# IRSSG HSP Symmetry

## Purpose

Use this skill to derive a material's spin space group from a magnetic structure file and then fetch the matching Huairou Symmetry Platform (HSP) records. Treat IRSSG as the source of truth for SG/MSG/SSG identification; do not infer group numbers or symbols by hand when an input file is available.

## Inputs

Accept either:

- mPOSCAR/POSCAR-like files whose coordinate rows include magnetic moments after positions, typically `x y z mx my mz`.
- `.mcif` files containing magnetic structure data readable by IRSSG.

Confirm that magnetic moments are present and nonzero. If IRSSG reports only a nonmagnetic SG, report that no SSG was identified because the input is nonmagnetic under the selected `--magtolerance`.

## Workflow

1. Choose tolerances. Start with `--tolerance 1e-3` for spatial symmetry and `--magtolerance 1e-4` for moment matching unless the user provides stricter values or the structure is numerically noisy.
2. If the HSP deployment requires an API key, provide it through `HSP_API_KEY`, `HSP_WEB_API_KEY`, `CMPDC_API_KEY`, `--hsp-api-key`, or `--hsp-api-key-file`. The wrapper sends it as `Authorization: Bearer <key>` by default.
3. Run the bundled wrapper when an input file is available:

```bash
python skills/irssg-hsp-symmetry/scripts/run_irssg_ssg.py INPUT_FILE --output-dir ssg-analysis --overwrite
```

4. Do not point the workflow at the IRSSG source tree by default. The wrapper first uses the installed `irssg` command and then the installed `irssg.ssg.MOM2SSG` Python module. Use `--repo-root PATH` only when the user explicitly asks to test an IRSSG source checkout:

```bash
python skills/irssg-hsp-symmetry/scripts/run_irssg_ssg.py INPUT_FILE --repo-root . --output-dir ssg-analysis --overwrite
```

5. Inspect `ssg-analysis/ssg_summary.json` first, then `ssg-analysis/hsp_group_info.json`, then `ssg-analysis/ssg.out` for full IRSSG operation tables or debugging details.
6. Report the SG, MSG, and SSG identifiers, symbols, HSP API fetch status, generated files, and the locations of full HSP records. When the user asks for high-symmetry k-points, read and report `space_group.k_points`, `magnetic_group.k_points`, and `spin_group.k_points` from `hsp_group_info.json`. Treat each k-point `multiplicity` as the HSP/API multiplicity in its cell convention; do not compare it against the number of `coordinates_primitive` entries as a data-validity check. When the user asks for all group information, summarize `hsp_group_info.json` and cite the file path rather than pasting very large operation tables unless requested.

## HSP API Fetch

The wrapper fetches these records after successful IRSSG identification unless `--skip-hsp-api` is passed:

- Space group: `GET /space-groups/{number}` using the leading number from `Atomic space group`.
- Magnetic group: `GET /magnetic-groups/{og_or_bns}` using OG first from `The MSG number`, then BNS if OG is absent.
- Spin group: `GET /spin-groups/{ssg_number}` using `The SSG number`.

Defaults:

- `--hsp-api-base-url https://cmpdc.iphy.ac.cn/hsp/api/v1`
- `--hsp-web-base-url https://cmpdc.iphy.ac.cn/hsp`
- API key header: `Authorization: Bearer <key>`

Use `--hsp-api-key-header`, `--hsp-api-key-prefix`, or `--hsp-api-key-query-param` if the deployment expects a different API-key convention. Use `--require-hsp-api` when missing HSP records should make the command fail.

## Direct IRSSG Command

Run IRSSG directly when the wrapper is unnecessary:

```bash
irssg -ssg -c INPUT_FILE --tolerance 1e-3 --magtolerance 1e-4 > ssg.out
```

Do not search the IRSSG source tree for implementation details unless the task is explicitly about debugging IRSSG itself. For normal material analysis, treat `irssg` as an installed external tool and use HSP API output for database-side group details.

Expect IRSSG to write `ssg.data` for later plane-wave or Wannier-band character/corep analysis. The wrapper additionally writes `hsp_group_info.json` with complete HSP API records. IRSSG may also write `msg.data`, `ssgop.npy`, `POSCAR.symm`, and `POSCAR.ssg_primitive`.

## Output Interpretation

Read `references/irssg-output.md` when you need the exact output field mapping, artifact meanings, parse rules, or failure triage.

Prefer citing identifiers and run status from `ssg_summary.json`, and detailed database records from `hsp_group_info.json`, when using the wrapper. For high-symmetry k-points, use the `k_points` field under each fetched group record rather than adding a new wrapper output mode. Report `multiplicity`, `little_cogroup`, and coordinate lists as provided by HSP; do not infer missing primitive coordinates from multiplicity. If parsing misses a field, cite the relevant line from `ssg.out` and mark the JSON field as unavailable instead of guessing.

## Extension Points

Keep later property workflows layered on top of this identification/API-fetch step:

- Use `ssg.data` as the handoff artifact for `irssg -pw` or `irssg -wann`.
- Add deterministic scripts for specific SSG properties only after their expected input/output contract is clear.
- Preserve the original mPOSCAR/mcif, `ssg.out`, `ssg_summary.json`, and `hsp_group_info.json` so downstream checks remain reproducible.
