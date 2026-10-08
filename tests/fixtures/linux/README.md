# Linux rule reference corpus

These are pinned source examples, not interchangeable input/output golden pairs.
No equivalent pair was established among the four selected comparisons. Similar titles or ATT&CK tags do not establish detection equivalence.

| Topic | Elastic source | Sigma reference | Relationship | Material difference |
| --- | --- | --- | --- | --- |
| base64 | [Elastic](https://github.com/elastic/detection-rules/blob/7e37a41b1e5008faddffef37c8ddd56a8a3398e7/rules/linux/defense_evasion_base64_decoding_activity.toml) | [Sigma](https://github.com/SigmaHQ/sigma/blob/8a4813404ea3074890e0cda9272d4d1a8b2941d6/rules/linux/process_creation/proc_creation_lnx_base64_decode.yml) | overlapping | Elastic covers several utilities and aggregates rare activity; Sigma checks /base64 plus -d only. |
| chattr | [Elastic](https://github.com/elastic/detection-rules/blob/7e37a41b1e5008faddffef37c8ddd56a8a3398e7/rules/linux/defense_evasion_chattr_immutable_file.toml) | [Sigma](https://github.com/SigmaHQ/sigma/blob/8a4813404ea3074890e0cda9272d4d1a8b2941d6/rules/linux/process_creation/proc_creation_lnx_chattr_immutable_removal.yml) | overlapping | Elastic covers both -i and +i patterns with parent exclusions; Sigma covers literal -i removal only. |
| insmod | [Elastic](https://github.com/elastic/detection-rules/blob/7e37a41b1e5008faddffef37c8ddd56a8a3398e7/rules/linux/persistence_insmod_kernel_module_load.toml) | [Sigma](https://github.com/SigmaHQ/sigma/blob/8a4813404ea3074890e0cda9272d4d1a8b2941d6/rules/linux/auditd/syscall/lnx_auditd_load_module_insmod.yml) | related | Elastic process events cover kmod/insmod/modprobe with exclusions; Sigma requires auditd SYSCALL, comm insmod, and /usr/bin/kmod. |
| bpf | [Elastic](https://github.com/elastic/detection-rules/blob/7e37a41b1e5008faddffef37c8ddd56a8a3398e7/rules/linux/persistence_bpf_probe_write_user.toml) | [Sigma](https://github.com/SigmaHQ/sigma/blob/8a4813404ea3074890e0cda9272d4d1a8b2941d6/rules/linux/builtin/lnx_potential_susp_ebpf_activity.yml) | near_match | Both look for bpf_probe_write_user; Elastic additionally constrains Linux, system.syslog, kernel process, and message field. Sigma uses an unfielded keyword. |

## Provenance and preparation

- Elastic commit: `7e37a41b1e5008faddffef37c8ddd56a8a3398e7` from the existing submodule.
- Sigma commit: `8a4813404ea3074890e0cda9272d4d1a8b2941d6` from its master branch when inspected.
- Each Elastic JSON fixture contains the entire `[rule]` table parsed with Python tomllib from the pinned TOML file. Only the repository wrapper/serialization changed; queries, language, type, and rule values were not simplified. Repository `[metadata]` is outside the flat input contract.
- Sigma YAML references are byte-for-byte copies, including author/attribution and comments. License notices/text are retained in `licenses/`.
- `manifest.json` records paths, source links, hashes of original Elastic TOML, normalized JSON, query text, and Sigma reference bytes. Tests run offline without a submodule checkout or network.

## What tests expect

R-01 (base64), R-02 (chattr), and R-03 (insmod) use unsupported ES|QL/EQL detection methods. R-04 (BPF) uses KQL but needs fields/unquoted syntax outside the approved subset. All four must preserve supported metadata, log limitations, omit detection, and report an incomplete draft. They must never substitute the related Sigma rule, its UUID, its severity, or its narrower/broader conditions.

The BPF pair shares the exact helper indicator, but Elastic additionally scopes the dataset, host OS, process, and message field. The base64 pair differs in utilities and statistical aggregation; chattr differs in attribute direction and exclusions; insmod differs in telemetry and executable coverage.

The supplied PowerShell pair remains the exact successful conversion fixture. A separate synthetic Linux KQL case tests successful contains-all conversion; it is explicitly labeled synthetic and does not claim to be the upstream ES|QL rule.

## Scope implications

Full successful translation of these real Linux rules would require more KQL field/operator coverage, EQL or ES|QL support, or new event-source mappings. Those are future scope changes requiring design review. This test corpus exercises the approved best-effort behavior without broadening production semantics.
