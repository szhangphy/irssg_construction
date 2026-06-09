# IRSSG SSG Output Reference

Use this reference when parsing or explaining `irssg -ssg` / `MOM2SSG` output.

## Primary Command

```bash
irssg -ssg -c INPUT_FILE --tolerance 1e-3 --magtolerance 1e-4 > ssg.out
```

The bundled wrapper runs the same stage, writes `ssg_summary.json`, and then fetches HSP API records into `hsp_group_info.json` unless `--skip-hsp-api` is passed.

## Key Fields

- `The SSG number`: canonical SSG identifier, e.g. a number with suffix indicating magnetic class.
- `The SSG international symbol`: formatted SSG label for reporting.
- `I/II/III ... So`: magnetic configuration class and spin-only group.
- `P (spin part of Go)`: spin point group part of `Go`.
- `H (lattice part of Go)`: lattice space-group part of `Go`.
- `# Number` under `Spin space group operations`: number of SSG operations.
- `Atomic space group`: nonmagnetic atomic SG detected from positions only.
- `N_ASG/N_SSG`: ratio between atomic space-group and spin-space-group operation counts in the reported convention.
- `The MSG number`: OG/BNS/SSG setting identifiers when MSG mapping is available.
- `The MSG international symbol`: MSG label.
- `# Number` under `Magnetic space group operations`: number of MSG operations.
- `hsp_group_identifiers` in `ssg_summary.json`: parsed identifiers used for API lookup:
  - `space_group_number`
  - `magnetic_group_og_number`
  - `magnetic_group_bns_number`
  - `spin_group_number`
- `hsp_api_status` in `ssg_summary.json`: `ok`, `partial_or_failed`, or `skipped_no_group_identifiers`.

## Generated Artifacts

- `ssg.out`: full stdout log; preserve for provenance and operation tables.
- `ssg.data`: IRSSG handoff file for later `irssg -pw` or `irssg -wann` character/corep analysis.
- `msg.data`: MSG-mode handoff file when generated.
- `ssgop.npy`: NumPy pickle of symmetry operation data.
- `POSCAR.symm`: symmetrized input structure with magnetic data.
- `POSCAR.ssg_primitive`: SSG primitive cell, written when the input POSCAR cell is not SSG primitive.
- `ssg_summary.json`: wrapper-generated parsed summary.
- `hsp_group_info.json`: wrapper-generated API payload containing complete HSP records:
  - `space_group`: full `/space-groups/{number}` JSON, including operations, Wyckoff positions, and high-symmetry k-vectors.
  - `magnetic_group`: full `/magnetic-groups/{og_or_bns}` JSON, including MSG operations, Wyckoff positions, and high-symmetry k-vectors.
  - `spin_group`: full `/spin-groups/{ssg_number}` JSON, including spin operations, Wyckoff positions, and high-symmetry k-vectors.
  - `requests`: URL/status/error metadata for each API request.
  - `web_links`: frontend URLs for the matching SG/MSG/SSG pages.

## Reporting Rules

Report values from `ssg_summary.json` first. If a field is missing but present in `ssg.out`, quote or paraphrase the exact relevant line and note that the wrapper did not parse it.

For complete symmetry data, report from `hsp_group_info.json`; do not reconstruct operations, Wyckoff positions, or high-symmetry k-vectors by hand from `ssg.out` unless the API record is missing.

For high-symmetry k-points, read the existing API payload fields:

- `space_group.k_points`
- `magnetic_group.k_points`
- `spin_group.k_points`

For each k-point, report `multiplicity`, `little_cogroup`, `coordinates_primitive`, and `coordinates_conventional` exactly as provided. `multiplicity` follows the HSP/API cell convention and is not required to equal the number of primitive coordinate strings in `coordinates_primitive`.

Do not add a new wrapper output file for each requested subgroup of fields; the wrapper's contract is to fetch complete HSP records once, then the agent extracts the requested fields.

Do not report an SSG number when IRSSG prints `The SG number` only; that means the moments are all below `--magtolerance` or missing.

Treat `ssg.data` as the required checkpoint before band-character or corep workflows. Do not run `-pw` or `-wann` until this file exists in the working directory alongside the required electronic-structure inputs.

## Common Failure Checks

- Input path: ensure the wrapper copied the intended mPOSCAR or `.mcif` into the output directory.
- Magnetic moments: ensure POSCAR rows include moment triplets and moments exceed `--magtolerance`.
- Tolerances: try looser `--tolerance` for slightly distorted coordinates; try looser `--magtolerance` for noisy moments.
- Source checkout imports: pass `--repo-root /path/to/irssg` only when explicitly testing an IRSSG source checkout. The default workflow must not scan parent directories for `src_mom2ssg/MOM2SSG.py`.
- Installed-package imports: run from an isolated output directory so a local source-tree `irssg/` folder does not shadow the installed `irssg.ssg` package.
- HSP API auth: set `HSP_API_KEY` or pass `--hsp-api-key-file`. The default header is `Authorization: Bearer <key>`.
- HSP API base URL: default is `https://cmpdc.iphy.ac.cn/hsp/api/v1`; override with `--hsp-api-base-url` for local development or a different deployment.
- API fetch failures are recorded in `hsp_group_info.json.requests`. They are nonfatal unless `--require-hsp-api` is used.
