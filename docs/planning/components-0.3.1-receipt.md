# Components 0.3.1 adoption receipt

Historical record. For current release and host status, see the [component source map](../components.md). These results retain their original release and date.

## 0.3.1 shell maintenance acceptance

The portable helper's redirection diagnostic regression was introduced in the
[adaptation at `4d4066b`](https://github.com/byebyebryan/niri-plus/commit/4d4066b1916cf49e14d146cd4ef1a337c7e9e5da).
Carbon normal Kitty use exposed missing optional sysfs reads on stderr even
though the probes failed safely. Release `components-v0.3.1` fixes that Zsh
redirection boundary; it changes only `components/shell/p10k-custom-segments.zsh`
among 27 bundle files and was verified against two deterministic builds.

The producer and consumer checks require quiet missing/empty/unterminated reads
and an energy-only battery result of 75%, 10.0W and `3:00`. Host sysfs probes
and owned full-prompt PTYs passed on Carbon, Starship and Snap. Each host had
zero drift across all 35 selected targets, preserved 34 other targets, seven
protected files, 25 protected root files and eleven service identities, and
repeat applies made no writes. Captured process identities remained intact
(Carbon 11, Starship 14, Snap 34). Carbon's temporary trial was removed while
the installed prompt already matched the official payload; the user confirmed
normal Kitty use of the trial with those same bytes. Starship and Snap changed
only the selected prompt target. Snap's pre-existing package-manifest edit and
installed package state were preserved.

Appearance source and identity did not change in 0.3.1, and all 39 derived
output records per host remain byte-identical to the approved 0.3.0 receipt.
The six toolkit checks, four reviewed images and 45 pre-change/native
comparisons remain historical 0.3.0 evidence. For 0.3.1, shell staging
reverified the existing dependency pins and all known present Powerlevel10k
caches on each host; no plugin revision changed. The full consumer suite reran
synthetic cache layout/tamper checks and guarded greeter checks for three
profiles with zero privileged-write requests. No new toolkit, image or physical
qualification was run. Carbon's normal use is recorded for the corrected
prompt; normal new Kitty/tmux/SSH use elsewhere and physical device acceptance
remain separate follow-ups. Consumer shell adoption is revision
`c8e058ed491b63b734c591c6dcff2d21ede7f03e`; the final consumer source and
documentation revision is `43d84fe54a8b07c405fc4461fda5fa14f605043e`.

## 0.3.1 adoption checkpoint

| Module | Evidence at this checkpoint |
| --- | --- |
| Desktop | Deployed and converged on Carbon, Starship and Snap. Sixteen shared files matched byte-for-byte; scoped repeat runs made no writes and preserved services, processes and captured policy. |
| Shell | The 0.3.1 quiet-read correction is deployed and PTY-qualified on all three hosts; see the maintenance acceptance above for fixture results, scoped target preservation and repeat behavior. |
| Appearance | Original qualification remains at adoption revision `9f2bf9689d27a5698c25c0e604a835b5370b0624` under producer 0.3.0. Its 39 outputs remain identical in 0.3.1; toolkit and image evidence remains historical. The 0.3.1 guarded greeter checks requested zero privileged writes. |

These dated checkpoints are distinct. The 0.3.1 consumer source revision is
`43d84fe54a8b07c405fc4461fda5fa14f605043e`; it follows shell adoption revision
`c8e058ed491b63b734c591c6dcff2d21ede7f03e`. The earlier desktop delivery in
[`data/history/setup-20261026.json`](../../data/history/setup-20261026.json) remains its dated record; it does not
stand in for qualification or rollout of the current shared appearance
consumer. The same rule applies to source parity, package verification and
normal-use or physical acceptance: each is recorded at the evidence level it
actually covers.
