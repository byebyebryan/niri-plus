# Resource check and current desktop showcase

Status: resource observation, native capture and site integration accepted,
2026-10-30 UTC. The [execution receipt](resource-and-showcase-receipt.md)
records measured results, the current overview, preserved media and validation.
Exact-head publication and VM preservation evidence are retained outside Git.
Sol owns design/copy and final acceptance; Luna Max handles bounded technical
work. Hardware/device acceptance, optional agent/remote integration and
installed-system diagnostics remain daily-use follow-ups.

## Outcome

Establish a small, honestly scoped resource baseline and make the main native
demonstration represent the everyday desktop. Keep the browser/terminal story,
the selected Neutral Slate identity and the recommended agent setup route.
This pass should produce a concise result, rather than another infrastructure
or theme project.

## Current evidence and reusable work

- Public source is `25539e7f1cb977a82551fde43c40658da1f14489`; the local
  worktree was clean at planning. Components 0.4.1 and the black-workspace
  identity are installed through chezmoi on Carbon, Starship and Snap.
- The [current receipt](black-workspace-receipt.md) records the accepted
  installed-Arch reference, source/input pins, native tasks and hardware limits.
  Preserve its offline `arch-reference-0.4.1` checkpoint and all earlier
  checkpoints. The existing final working disk/EFI variables can be used for
  the new disposable workload and capture; keep the same guarded domain and
  existing network, with autostart disabled.
- The current native desktop still and 35.4-second Audio/Network clip are
  accepted and public. Reuse them with their exact bytes and original pins.
- Four older native clips retain components 0.3.1, their prior identity and
  original dates. They are historical media, not missing current releases.
- The home page's primary demo link currently lands on the controls clip.
  The broader overview and the browser/files, terminal and information clips
  still show the earlier workspace treatment. SSH/Tmux/Agent workflows have
  explanatory content and sample renderings, rather than a complete current
  native workflow recording.
- Public pilot/desktop tooling under `tools/vm/` retains its old input tuple.
  Do not rerun its bootstrap/assembler over the accepted 0.4.1 guest. Reuse
  suitable capture mechanics only after inspecting their assumptions, and
  document a small current capture procedure separately from historical tools.

## 1. Quick resource pass

Answer two practical questions: does the selected desktop do unexplained work
while quiet, and does opening/closing its on-demand UI leave work behind?
This is a short observation, with no performance target or comparison against
another desktop environment.

### Environment and attribution

Measure inside the existing 0.4.1 Arch working guest only. This gives the pass
a controlled application set, repeatable panel/menu interaction and a consistent
starting state, without operating or sampling the user's desktop as a second
benchmark. No physical-host resource baseline is required.

Keep the same vCPU/RAM allocation, virtual graphics, output mode/scale, software
and application content across phases. Run one guest, let startup settle, and
keep recording/encoding off. Host contention can still affect a VM: record host
load as context and guest CPU steal time when exposed. If unrelated host work
is heavy, defer the sample instead of stopping that work or adding CPU-pinning
infrastructure. Do not present these values as laptop, physical GPU/display,
battery or whole-workstation performance.

Only revisit physical-host measurement later for a concrete question that the
guest cannot answer, such as a hardware-specific issue or a disagreement with
ordinary use. It is outside this pass's required work.

List the actual process/unit cohort before sampling: Niri, SwayNC, Kanshi,
Fcitx, Cliphist collectors, idle/battery helpers, authorization, and the selected
portal/audio providers. Attribute Chrome, Kitty/Zsh and any optional Plus
processes separately. Enumerate descendants and process start identities so
forks, replacements and shared helpers are accounted for once. A process outside
the declared cohort is context, not desktop overhead by assumption.

Use low-overhead `/proc` CPU-time counters and memory readings. Report CPU with
100% meaning one guest vCPU, memory in MiB, and sample interval/duration.
Prefer PSS for an aggregate when readable; otherwise show per-process RSS and
explain that summing it double-counts shared pages. Collect PSS at phase
boundaries or a slower interval, not through a heavy profiler at every tick.
Keep the sampler's own work separate. Do not wake a sleeping NVIDIA device
with diagnostic polling or introduce new services/packages for measurements.

### Controlled sequence

| Phase | Duration / action | Observation |
| --- | --- | --- |
| Settle | About 60 seconds after normal login and opening the public browser/sample terminal | Startup bursts are distinct from steady operation. |
| Quiet desktop | 60 seconds, panel and menus closed | CPU distribution, per-owner memory and process census. |
| SwayNC open | 30 seconds | Expected refresh activity, with only available guest hardware. |
| SwayNC closed | 60 seconds | CPU settles; no unintended panel child or subscription work persists. |
| Ordinary launchers | Open/close application launcher, clipboard, Audio and Network once each, using existing safe guest state | Responsiveness by observation, transient children and callback cleanup. No credential, radio or connection actions. |
| Return to quiet | 60 seconds; repeat the open/close cycle once | No duplicate persistent owners or continuing unexplained growth/work. Bounded caches are not automatically leaks. |

Keep recording and encoding off during these phases. Retain raw samples and a
short summary with median/peak CPU and memory ranges. Existing meaningful
startup measurements may be reused with their original scope; do not build a
new input-to-frame latency harness for this quick pass. Small timing samples
must be called observations, not statistical performance guarantees.

### Stop and follow-up rule

Complete when the sampled scope, environment, observations and limitations are
clear. A stable measured result does not require an optimization commit.
Repeat a suspect phase once only when needed to distinguish activity from a
reproducible problem. Attribute an anomaly before proposing a fix. A larger
investigation or component/release change becomes a separately scoped bug;
do not let it silently expand this pass. No battery rundown, fleet benchmark,
GPU stress, suspend test or sustained soak is required.

Keep the durable result in a short dated resource receipt. Add a small factual
site note only if the observations are useful to a visitor. Do not advertise
VM figures as universal desktop requirements or promise a general memory total.

## 2. Current-theme native showcase

The primary deliverable is one approximately 60–90-second desktop overview.
It should communicate the browser/terminal relationship, Niri navigation and
tools that appear when needed. The existing controls clip remains the focused
controls demonstration, so the overview need only show a brief control action.

### Proposed storyboard

| Approximate span | Native task | What the visitor learns |
| --- | --- | --- |
| 0–12 seconds | Chrome beside Kitty; change focus, enter/leave overview or switch workspace | The two halves, keyboard focus and black workspace with a legible overview surround. |
| 12–32 seconds | Download a public sample, open it in Dolphin, and select the original file in Chrome's GTK chooser | Ordinary graphical file interaction belongs in this terminal-focused desktop. |
| 32–50 seconds | Run a short useful Git/project command in the native shell and return between browser and terminal | Actual prompt, readable Balanced+ output and keyboard-driven work. |
| 50–68 seconds | Open SwayNC, inspect actual available metrics, then retrieve an owned text or image from clipboard history | No permanent bar; information and previous content remain close at hand. |
| 68–82 seconds | Briefly open Audio or Network, then return to the browser/terminal pair | Shared controls, clear status and an uncluttered working desktop. |

These times are a pacing target, not timestamps to publish before the encoded
take is reviewed. Use an unhurried visible pause after each important result.
Prefer a coherent continuous take when practical. Short native segments joined
with simple cuts are acceptable if every source/trim and encoding step is
recorded. No time stretching, invented status, fake agent transcripts or
composited desktop actions.

### Agent and remote scene boundary

Before freezing the storyboard, check whether an already supported, safe demo
environment can show the current Plus tools with disposable session names and
no private accounts, conversations or host inventory. If so, a short insert
can replace part of the terminal segment: open/focus a native agent window or
return to a real sample tmux/SSH session. Use the maintained producers' public
launch contracts and record their additional versions independently.

An actual remote action must use an explicitly owned endpoint. A local demo
endpoint must be labeled local; an interface fixture must be labeled sample
data. A recorded picker alone does not prove a remote connection or agent task.
If safe capture requires new authentication, integration features, infrastructure
or changes to attended sessions, keep the core overview complete and leave
that insert for later daily-use capture. Do not turn this into the deferred
agent/remote integration project or weaken the labels to fill the scene.

### Capture and review

- Reuse the existing Starship local KVM guest and the accepted 0.4.1 working
  environment. Recheck domain/disk/EFI identity, component/identity pins,
  package versions and scene state before changing it. Do not reinstall the
  desktop, import a private home or mutate the accepted checkpoints.
- Keep the selected theme, normal gaps, fonts and application sizing. Use a
  native 1920×1080 output at scale 1 and target 30 fps, subject to the guest's
  advertised modes. The recording is a staged reference demonstration.
- Use public/local sample content, a guest-only sample project and signed-out
  browser state. Keep notifications, device names and terminal output suitable
  for publication. Real absent hardware stays absent.
- Measure before recording. Stop the resource sampler, then rehearse the native
  sequence without the recorder. Do not let profiling or encoding contaminate
  the resource baseline.
- Retain raw media, source/trim records, exact tool commands/versions and
  capture notes outside Git. Give new public media new paths/records; do not
  overwrite historical source assets or relabel their version/date.
- Review full decode, duration, actual decoded frames, frame timing and color
  metadata. Check representative frames against actual encoded timestamps;
  captions and frame labels must describe the observed action. Preserve any
  measured codec limitations rather than inferring that a requested flag took.
- Sol owns storyboard, framing, copy and final visual review. Native mechanics
  and checks can be delegated during a subsequently authorized execution loop.
  Human playback/appearance acceptance remains a separate recorded status.

## 3. Site integration

Lead the home page's existing native-demo link to the new broad overview. Put
that overview first on the Tour, with concise steps or timestamps and links to
the relevant setup recipes. Keep the accepted controls clip as a focused demo
on Tour and the controls recipe. Reuse the accepted current desktop still.

Move the four older recordings to a clearly labeled earlier-recordings page,
linked from Tour and relevant workflow sections. Preserve their bytes, original
pins, capture dates and detailed receipts. This keeps the main Tour focused
without adding another full set of current focused recordings. A frame or
segment reused from any prior capture must retain its own source record.

Keep the interactive walkthrough and fixture renderings as secondary material,
with their existing labels. Preserve the personal story, Setup navigation to
the human overview, and the prominent recommended agent-guide link. Do not
create a resource dashboard, new theme or full site redesign for these changes.

## Execution sequence and completion gates

1. Recheck source/worktree, current guest state, selected inputs and immutable
   checkpoint receipt. Inspect existing capture mechanics; choose the minimum
   current helpers/procedure without rerunning the historical assembler.
2. Run the controlled guest sequence without recording. Record findings and
   host-contention context; separate any concrete bugs from the showcase work.
3. Review the scene inventory and decide whether the optional agent/remote
   insert is already practical within the stated boundary. Freeze the actual
   storyboard and content before recording.
4. Rehearse, capture, inspect encoded output and finalize media provenance.
5. Integrate the current overview, focused controls, historical recordings and
   any useful measured note. Update only affected site/capture code and docs.
6. Run source/export/link checks and normal/portable builds. Run the owned
   browser suite for desktop/narrow layouts, keyboard operation, reduced
   motion, JavaScript-disabled reading, and every current/historical player's
   playback, seeking and direct download. Review the changed pages visually.
7. Review commits, push/publication authorization and exact local/remote heads.
   If publication is authorized, observe exact-head CI/Pages and verify served
   media, page, identity and provenance bytes. Site publication is distinct
   from a component release or fleet deployment; neither is expected here.
8. Restore capture-only guest settings and disposable device changes, shut down
   normally, and verify autostart remains disabled. Confirm the accepted and
   earlier checkpoint files still match their protected hashes.

Complete with a short resource finding, one current broad overview, the reused
focused controls clip, historical media still inspectable, and a reviewed
coherent site. Record the optional agent/remote insert as included or deferred
with its actual reason. Retain remaining hardware/human checks for ordinary use.
