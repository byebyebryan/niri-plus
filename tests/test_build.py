import importlib.util
import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("niri_plus_build", ROOT / "scripts/build.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def demo_provenance_fixture():
    producer = json.loads((ROOT / "data/components.json").read_text())["producer"]
    identity_hash = hashlib.sha256((ROOT / "design/identity.json").read_bytes()).hexdigest()
    files = [
        {"path": path, "sha256": "0" * 64, "license": builder.DEMO_ASSET_LICENSES[path], "source": "staged Arch guest", "description": "demo media"}
        for path in builder.DEMO_ASSETS
    ]
    clips = []
    for name, contract in builder.DEMO_CLIPS.items():
        clips.append({
            "id": name,
            "video": contract["video"],
            "poster": contract["poster"],
            "width": 1920,
            "height": 1080,
            "duration_seconds": 30.0,
            "frame_count": 900,
            "average_frame_rate": "30000/1001",
            "video_codec": "h264",
            "pixel_format": "yuv420p",
            "capture_date": "2026-10-27",
            "source_capture_sha256": None if name == "overview" else "0" * 64,
            "source_captures": [
                {"path": "assets/demo-browser-files.mp4", "sha256": "0" * 64, "trim_range_seconds": [0, 30]}
            ] if name == "overview" else None,
            "poster_source": {"path": contract["poster"], "sha256": "0" * 64},
            "reuse_reason": "Reuse fixture reason",
            "audio": "none",
            "fixture_label": "Public sample content; guest CPU/RAM/network readings are actual",
            "processing_notes": ["site-ready H.264 derivative"],
            "agent_review": "passed",
            "automated_review": "passed",
            "human_review": "pending",
            **({"additional_source_versions": {"swaync": builder.SWAYNC_PIN}} if name in {"overview", "information"} else {}),
        })
    return {
        "files": files,
        "desktop_demos": {
            "capture_label": "Staged Arch Linux x86_64 guest",
            "source_versions": {
                "niri": "26.04",
                "components": {key: producer[key] for key in ("version", "source_commit", "archive_sha256", "manifest_sha256")},
                "identity": {"sha256": identity_hash},
            },
            "capture_receipt_path": "docs/planning/desktop-demonstration-receipt.md",
            "separate_guest_checks": [{
                "id": "wlr-whole-monitor-sharing",
                "recorded_in_clips": False,
                "scope": "Staged guest only; not a fleet/default adoption",
            }],
            "clips": clips,
        },
    }


class BuildContracts(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="niri-plus-check-")
        self.addCleanup(self.directory.cleanup)
        self.output = Path(self.directory.name) / "site"

    def test_complete_site_has_checked_links_and_only_allowlisted_planning_docs(self):
        result = builder.build(self.output)
        self.assertEqual(result["pages"], 21)
        self.assertGreater(result["local_links"], 200)
        self.assertEqual(
            {path.relative_to(self.output).as_posix() for path in (self.output / "docs").rglob("*") if path.is_file()},
            {
                "docs/planning/arch-installation-receipt.md",
                "docs/planning/desktop-demonstration-receipt.md",
            },
        )
        self.assertTrue((self.output / "tools/vm/desktop/wlr-compat/README.md").is_file())
        self.assertFalse((self.output / "AGENTS.md").exists())
        self.assertIn("I love terminal life", (self.output / "story/index.html").read_text())
        self.assertIn("Illustrated walkthrough", (self.output / "index.html").read_text())
        self.assertIn('href="/niri-plus/tour/#native-reference-demo"', (self.output / "index.html").read_text())
        for page in self.output.rglob("*.html"):
            self.assertNotIn("https://github.com/byebyebryan/dotfiles", page.read_text())

    def test_setup_audiences_share_one_detailed_guide_with_usable_text_links(self):
        builder.build(self.output, portable=True)
        overview = (self.output / "setup/index.html").read_text()
        agent = (self.output / "setup/agent/index.html").read_text()
        plain = (self.output / "setup/agent.md").read_text()
        source = (ROOT / "docs/setup-agent.md").read_text()
        self.assertIn('href="agent/"', overview)
        self.assertIn('href="agent.md"', overview)
        self.assertNotIn("sudo pacman", overview)
        self.assertIn("Execution contract", agent)
        self.assertIn("Completion report", agent)
        self.assertIn("Stage 8 gate", agent)
        self.assertIn('rel="alternate" type="text/markdown" href="../agent.md"', agent)
        # The text export preserves commands while following the generated site's routes.
        fences = r"^```[^\n]*\n(.*?)^```\s*$"
        self.assertEqual(re.findall(fences, plain, re.M | re.S), re.findall(fences, source, re.M | re.S))
        parser = builder.MarkdownIt("commonmark").enable("table")
        checked = 0
        for token in parser.parse(plain):
            for child in token.children or []:
                if child.type != "link_open":
                    continue
                url = urlsplit(urljoin(builder.SITE + "setup/agent.md", child.attrGet("href")))
                if url.netloc != urlsplit(builder.SITE).netloc or not url.path.startswith(builder.BASE):
                    continue
                dest = unquote(url.path[len(builder.BASE):])
                dest += "index.html" if dest.endswith("/") else ""
                target = self.output / dest
                self.assertTrue(target.is_file(), f"unusable agent text link: {url.geturl()}")
                if url.fragment and dest.endswith(".html"):
                    self.assertIn(unquote(url.fragment), builder.Page(target.read_text()).ids)
                checked += 1
        self.assertGreater(checked, 20)

    def test_fresh_replay_evidence_stills_are_public_and_hashed(self):
        builder.build(self.output)
        provenance = json.loads((self.output / "assets/provenance.json").read_text())
        records = {item["path"]: item for item in provenance["files"]}
        captures = {
            "assets/arch-reference/themed-greeter-after-reboot.png": "MIT",
            "assets/arch-reference/gtklock-replay-neutral-slate.png": "GPL-3.0-only",
            "assets/arch-reference/chrome-ime-replay-fractional-preedit.png": "MIT",
        }
        for path, license_name in captures.items():
            record = records[path]
            self.assertEqual(record["capture_date"], "2026-10-28")
            self.assertEqual(record["capture_label"], "Staged Arch Linux x86_64 guest, fresh E3 replay")
            self.assertEqual(record["license"], license_name)
            self.assertEqual(hashlib.sha256((self.output / path).read_bytes()).hexdigest(), record["sha256"])
        login = (self.output / "recipes/login/index.html").read_text()
        self.assertIn(f'src="{builder.BASE}assets/arch-reference/themed-greeter-after-reboot.png"', login)
        self.assertIn("installation receipt", login)
        session = (self.output / "recipes/session/index.html").read_text()
        self.assertIn(f'src="{builder.BASE}assets/arch-reference/gtklock-replay-neutral-slate.png"', session)
        self.assertIn("password field", session)
        input_recipe = (self.output / "recipes/input/index.html").read_text()
        self.assertIn(f'src="{builder.BASE}assets/arch-reference/chrome-ime-replay-fractional-preedit.png"', input_recipe)
        self.assertIn("not a remote page or account", input_recipe)
        ime = records["assets/arch-reference/chrome-ime-replay-fractional-preedit.png"]
        self.assertEqual(ime["captured_components"], "Chrome 156.0.8078.47-1; Fcitx5 5.1.23-1; fcitx5-chinese-addons 5.1.15-2")
        self.assertIn("observed packaging discrepancy", ime["component_license_sources"])
        setup = (self.output / "setup/index.html").read_text()
        self.assertIn(f'href="{builder.BASE}docs/planning/arch-installation-receipt.md"', setup)
        receipt = (self.output / "docs/planning/arch-installation-receipt.md").read_text()
        self.assertIn("https://dev.byebyebryan.com/niri-plus/setup/", receipt)
        self.assertNotIn("arch-installation-pass.md", receipt)

    def test_downloadable_receipts_keep_commands_and_link_to_existing_repository_sources(self):
        builder.build(self.output, portable=True)
        repository_prefix = "https://github.com/byebyebryan/niri-plus/blob/main/"
        linked_sources = set()
        fences = r"^```[^\n]*\n(.*?)^```\s*$"
        for name in builder.PUBLIC_LOCAL_DOCS:
            if not name.endswith(".md"):
                continue
            original = (ROOT / name).read_text()
            exported = (self.output / name).read_text()
            self.assertEqual(re.findall(fences, original, re.M | re.S), re.findall(fences, exported, re.M | re.S))
            for token in builder.MarkdownIt("commonmark").enable("table").parse(exported):
                for child in token.children or []:
                    if child.type == "link_open" and child.attrGet("href").startswith(repository_prefix):
                        path = unquote(urlsplit(child.attrGet("href")).path.split("/blob/main/", 1)[1])
                        self.assertTrue((ROOT / path).is_file())
                        linked_sources.add(path)
        self.assertTrue({"docs/planning/demo-and-adoption-pass.md", "docs/planning/capture-pilot-receipt.md",
                         "tools/vm/desktop/assemble-desktop.sh", "tools/vm/README.md"} <= linked_sources)

    def test_native_demo_provenance_contract_requires_measured_public_evidence(self):
        manifest = demo_provenance_fixture()
        self.assertEqual(builder.validate_desktop_demo_manifest(manifest)["capture_label"], "Staged Arch Linux x86_64 guest")
        manifest["desktop_demos"]["clips"][0]["human_review"] = ""
        with self.assertRaisesRegex(ValueError, "human-review status"):
            builder.validate_desktop_demo_manifest(manifest)
        manifest = demo_provenance_fixture()
        manifest["desktop_demos"]["clips"][0]["human_review"] = "accepted after later review"
        builder.validate_desktop_demo_manifest(manifest)
        manifest = demo_provenance_fixture()
        manifest["desktop_demos"]["clips"][0]["duration_seconds"] = 0
        with self.assertRaisesRegex(ValueError, "measured duration"):
            builder.validate_desktop_demo_manifest(manifest)
        manifest = demo_provenance_fixture()
        manifest["desktop_demos"]["source_versions"]["identity"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "identity hash differs"):
            builder.validate_desktop_demo_manifest(manifest)
        manifest = demo_provenance_fixture()
        manifest["files"] = manifest["files"][:-1]
        with self.assertRaisesRegex(ValueError, "lack provenance hashes"):
            builder.validate_desktop_demo_manifest(manifest)
        manifest = demo_provenance_fixture()
        next(item for item in manifest["files"] if item["path"] == "assets/demo-information.mp4")["license"] = "MIT"
        with self.assertRaisesRegex(ValueError, "license must be GPL-3.0-only"):
            builder.validate_desktop_demo_manifest(manifest)
        manifest = demo_provenance_fixture()
        manifest["desktop_demos"]["clips"] = [next(item for item in manifest["desktop_demos"]["clips"] if item["id"] == "terminal")]
        manifest["files"] = [item for item in manifest["files"] if "demo-terminal." in item["path"]]
        self.assertEqual([item["id"] for item in builder.validate_desktop_demo_manifest(manifest)["clips"]], ["terminal"])
        with self.assertRaisesRegex(ValueError, "exactly the four site clips"):
            builder.validate_desktop_demo_manifest(manifest, require_complete=True)

    def test_reused_terminal_pilot_assets_match_their_source_receipt(self):
        provenance = builder.desktop_demo_provenance()
        clip = next(item for item in provenance["clips"] if item["id"] == "terminal")
        self.assertEqual(clip["capture_date"], "2026-10-27")
        self.assertEqual(clip["source_capture_sha256"], "b6c3c63e3d60b0fe079d8d3a74f0f8a038813c16fa27453838c77cb1f43aa240")
        self.assertEqual(clip["reuse_reason"].startswith("Reused because Niri 26.04"), True)
        self.assertEqual((clip["width"], clip["height"], clip["duration_seconds"], clip["frame_count"], clip["average_frame_rate"]), (1920, 1080, 24.467, 735, "11025/367"))
        self.assertEqual((clip["agent_review"], clip["automated_review"], clip["human_review"]), ("passed", "passed", "pending"))
        records = {item["path"]: item for item in json.loads((ROOT / "assets/provenance.json").read_text())["files"]}
        for path in (clip["video"], clip["poster"]):
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), records[path]["sha256"])
            self.assertEqual(records[path]["license"], "MIT")

    def test_native_demos_have_static_steps_controls_and_staged_provenance(self):
        builder.build(self.output)
        tour = (self.output / "tour/index.html").read_text()
        self.assertEqual(tour.count("<video "), 4)
        self.assertEqual(tour.count('controls preload="none"'), 4)
        self.assertEqual(tour.count('type="video/mp4"'), 4)
        self.assertEqual(tour.count('class="native-demo-download"'), 4)
        self.assertEqual(tour.count("Open or download MP4"), 4)
        self.assertNotIn(" autoplay", tour)
        self.assertIn("Mod+N", tour)
        self.assertIn("Mod+Y", tour)
        self.assertIn("public sample content", tour)
        self.assertIn("Media provenance", tour)
        self.assertIn("Capture receipt", tour)
        self.assertIn("sharing is not shown in any clip", tour)
        self.assertIn('href="/niri-plus/recipes/files/"', tour)
        self.assertIn('href="/niri-plus/recipes/terminal/"', tour)
        self.assertIn('href="/niri-plus/recipes/notifications/"', tour)
        self.assertIn('href="/niri-plus/recipes/clipboard/"', tour)
        design = (self.output / "design/index.html").read_text()
        self.assertIn('src="/niri-plus/assets/demo-overview.png"', design)
        self.assertIn('href="/niri-plus/tour/#native-reference-demo"', design)
        provenance = json.loads((self.output / "assets/provenance.json").read_text())
        self.assertEqual(len(provenance["desktop_demos"]["clips"]), 4)
        self.assertTrue(all(item["human_review"] == "pending" for item in provenance["desktop_demos"]["clips"]))
        self.assertTrue(all(item["automated_review"] == "passed" for item in provenance["desktop_demos"]["clips"]))
        sharing = provenance["desktop_demos"]["separate_guest_checks"][0]
        self.assertFalse(sharing["recorded_in_clips"])
        self.assertIn("not a fleet/default", sharing["scope"])
        self.assertEqual(provenance["desktop_demos"]["clips"][0]["source_capture_sha256"], None)
        self.assertEqual(len(provenance["desktop_demos"]["clips"][0]["source_captures"]), 3)
        for path in builder.DEMO_ASSETS:
            self.assertTrue((self.output / path).is_file(), path)

    def test_component_source_map_pins_the_release_and_records_appearance_closeout(self):
        producer = json.loads((ROOT / "data/components.json").read_text())
        self.assertEqual(producer["producer"]["version"], "0.3.1")
        self.assertEqual(producer["producer"]["api_version"], 1)
        self.assertEqual(producer["producer"]["source_commit"], "014a14241bd722186ae9248e71162e75cf7af7b1")
        self.assertEqual(producer["producer"]["archive_url"], "https://github.com/byebyebryan/niri-plus/releases/download/components-v0.3.1/niri-plus-components-0.3.1.tar.gz")
        self.assertEqual(producer["producer"]["archive_sha256"], "868d9de46f54af9b9f563dd52cd94df9358fafaf9c9b33666c557c05d318a843")
        self.assertEqual(producer["producer"]["manifest_sha256"], "de3e981f8bb76d2b4ccfbf7f2722e81fc9f73edf7b62de11cad55f7a209e7ed3")
        self.assertEqual(producer["producer"]["publication_status"], "published and direct-download verified")
        self.assertEqual(producer["producer"]["changed_payloads"], ["components/shell/p10k-custom-segments.zsh"])
        self.assertEqual(producer["producer"]["deterministic_builds"], 2)
        self.assertEqual(producer["consumer"]["final_source_revision"], "43d84fe54a8b07c405fc4461fda5fa14f605043e")
        self.assertEqual(producer["consumer"]["shell_adoption_revision"], "c8e058ed491b63b734c591c6dcff2d21ede7f03e")
        appearance = producer["modules"]["appearance"]
        self.assertTrue(appearance["fleet_rollout_complete"])
        self.assertIn("converged", appearance["consumer_status"])
        self.assertEqual(producer["consumer"]["appearance_adoption_revision"], "9f2bf9689d27a5698c25c0e604a835b5370b0624")
        self.assertEqual(appearance["verified_derived_outputs_per_host"], 39)
        self.assertEqual(appearance["native_isolated_checks"]["qualification_release"], "0.3.0")
        self.assertIn("Historical 0.3.0 appearance qualification", appearance["evidence"])
        self.assertIn("no toolkit, image, or physical qualification was rerun", appearance["evidence"])
        self.assertEqual(appearance["guarded_greeter_checks"]["profiles"], 3)
        self.assertEqual(appearance["guarded_greeter_checks"]["privileged_write_requests"], 0)
        self.assertIn("not rerun for 0.3.1", appearance["native_isolated_checks"]["status"])

        shell = producer["modules"]["shell"]
        maintenance = shell["maintenance_acceptance"]
        self.assertIn("4d4066b", maintenance["regression_provenance"])
        self.assertEqual(maintenance["fixture"], {
            "capacity_percent": 75,
            "power": "10.0W",
            "eta": "3:00",
            "stderr": "empty",
        })
        self.assertEqual(
            (maintenance["selected_targets_per_host"], maintenance["target_drift_per_host"], maintenance["unchanged_other_targets_per_host"]),
            (35, 0, 34),
        )
        self.assertEqual(maintenance["owned_full_prompt_pty_hosts"], ["Carbon", "Starship", "Snap"])
        self.assertEqual(maintenance["repeat_apply"], "no writes")
        self.assertFalse(maintenance["hosts"]["carbon"]["official_prompt_target_changed"])
        self.assertTrue(maintenance["hosts"]["carbon"]["trial_removed"])
        self.assertTrue(maintenance["hosts"]["carbon"]["trial_bytes_match_official_payload"])
        self.assertTrue(maintenance["hosts"]["snap"]["preexisting_package_manifest_edit_preserved"])

        self.assertTrue(producer["modules"]["shell"]["headless"])
        self.assertFalse(producer["modules"]["shell"]["requires_niri_or_wayland"])
        self.assertIn("0.3.1 staging reverified", shell["runtime_cache_evidence"])
        self.assertIn("synthetic cache layout and tamper checks", shell["runtime_cache_evidence"])
        self.assertIn("no plugin revision changed", shell["runtime_cache_evidence"])
        self.assertIn("every loaded byte", producer["modules"]["shell"]["runtime_cache_evidence"])
        self.assertIn("alignment bytes", producer["modules"]["shell"]["runtime_cache_evidence"])

        builder.build(self.output)
        self.assertEqual(
            (self.output / "data/components.json").read_bytes(),
            (ROOT / "data/components.json").read_bytes(),
        )
        source_map = (self.output / "components/index.html").read_text()
        self.assertIn("independent selections", source_map.lower())
        self.assertIn("private chezmoi", source_map.lower())
        self.assertIn("0.3.1 shell maintenance acceptance", source_map.lower())
        self.assertIn("historical 0.3.0", source_map.lower())
        self.assertIn("014a14241bd722186ae9248e71162e75cf7af7b1", source_map)
        self.assertIn("c8e058ed491b63b734c591c6dcff2d21ede7f03e", source_map)
        self.assertIn("43d84fe54a8b07c405fc4461fda5fa14f605043e", source_map)
        self.assertIn("generated files keep their existing public paths", source_map.lower())

    def test_broken_local_anchor_is_rejected(self):
        builder.build(self.output)
        page = self.output / "index.html"
        page.write_text(page.read_text().replace("#browser-and-files", "#missing-workflow"))
        with self.assertRaisesRegex(ValueError, "missing anchor"):
            builder.validate(self.output)

    def test_changed_attributed_media_is_rejected(self):
        builder.build(self.output)
        (self.output / "assets/agent-plus.png").write_bytes(b"not the attributed image")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            builder.validate(self.output)

    def test_changed_example_is_rejected(self):
        builder.build(self.output)
        (self.output / "examples/niri/config.kdl").write_text("changed example")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            builder.validate(self.output)

    def test_unexpected_public_file_is_rejected(self):
        builder.build(self.output)
        (self.output / "private-note.txt").write_text("not public")
        with self.assertRaisesRegex(ValueError, "public inventory"):
            builder.validate(self.output)

    def test_identity_is_one_theme_from_the_reviewed_source(self):
        builder.build(self.output)
        identity = json.loads((self.output / "data/identity.json").read_text())
        self.assertEqual(identity["selected_candidate"], "neutral-slate")
        self.assertEqual(identity["direction"]["id"], "neutral-slate")
        self.assertEqual(identity["direction"]["ui_font"], "Noto Sans")
        self.assertEqual(identity["direction"]["mono_font"], "MesloLGS Nerd Font")
        self.assertEqual(identity["theme_scope"]["supported_target_count"], 1)
        self.assertNotIn("candidates", identity)
        self.assertEqual(len(identity["terminal"]["ansi"]), 16)
        self.assertEqual(len(identity["terminal"]["ansi_names"]), 16)
        self.assertEqual(len(identity["terminal"]["ansi_roles"]), 16)
        fragment = (self.output / "examples/kitty/neutral-slate.conf").read_text()
        self.assertEqual(identity["schema_version"], 2)
        self.assertEqual(identity["terminal"]["variant"], "balanced-plus")
        self.assertIn("background #000000", fragment)
        self.assertIn("background_opacity 1", fragment)
        self.assertIn("cursor #a6ceff", fragment)
        self.assertIn("selection_background #294e75", fragment)
        self.assertIn("color1 #e76c75", fragment)
        self.assertIn("color2 #99c070", fragment)
        self.assertIn("color3 #deb05c", fragment)
        self.assertIn("color4 #74aae9", fragment)
        self.assertIn("color12 #a7cefc", fragment)
        self.assertNotIn("font_family", fragment)
        design = (self.output / "design/index.html").read_text()
        self.assertIn("Noto Sans", design)
        self.assertIn("MesloLGS Nerd Font", design)
        self.assertIn("bright supplemental violet", design)
        self.assertEqual(design.count('class="ansi-slot"'), 16)
        self.assertEqual(design.count('data-surface-panel='), 4)
        self.assertNotIn("Slate Blue", design)
        self.assertNotIn("Inter Variable", design)
        self.assertFalse((self.output / "assets/fonts/inter.woff2").exists())
        self.assertTrue((self.output / "assets/fonts/noto.woff2").is_file())
        self.assertTrue((self.output / "assets/fonts/noto-medium.woff2").is_file())
        self.assertTrue((self.output / "assets/fonts/noto-semibold.woff2").is_file())
        (self.output / "assets/identity.css").write_text(":root{--bg:red}")
        with self.assertRaisesRegex(ValueError, "generated appearance"):
            builder.validate(self.output)

    def test_native_theme_examples_are_bound_to_the_canonical_identity(self):
        manifest = json.loads((ROOT / "examples/manifest.json").read_text())
        records = [item for item in manifest["files"] if item["path"].startswith("examples/theme/")]
        self.assertEqual(len(records), 7)
        identity = json.loads((ROOT / "design/identity.json").read_text())
        digest = hashlib.sha256((ROOT / "design/identity.json").read_bytes()).hexdigest()
        self.assertEqual({item["identity_sha256"] for item in records}, {digest})
        self.assertIn("not a deployed artifact", " ".join(item.get("notes", "") for item in records))
        stale = [dict(item) for item in records]
        stale[0]["identity_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "stale identity association"):
            builder.validate_identity_associations(stale)
        self.assertEqual(identity["selected_candidate"], "neutral-slate")
        builder.build(self.output)
        public_manifest = json.loads((self.output / "examples/manifest.json").read_text())
        self.assertEqual(len([item for item in public_manifest["files"] if item["path"].startswith("examples/theme/")]), 7)

    def test_contrast_study_keeps_the_selected_identity_and_isolates_black_only(self):
        builder.build(self.output)
        study = json.loads((self.output / "data/contrast-study.json").read_text())
        identity = json.loads((self.output / "data/identity.json").read_text())
        self.assertEqual(study["status"], "comparison")
        self.assertEqual(study["selected_terminal"], "black-balanced-plus")
        self.assertEqual(study["baseline_sha256"], hashlib.sha256((ROOT / study["baseline_source"]).read_bytes()).hexdigest())
        current = study["baseline"]["terminal"]
        black = study["baseline"]["terminal_on_black"]
        balanced, balanced_plus, rich, vivid = study["terminal_variants"]
        self.assertEqual({key for key in current if current[key] != black[key]}, {"id", "name", "background"})
        self.assertEqual(black["background"], "#000000")
        self.assertEqual(vivid["background"], "#000000")
        self.assertEqual(vivid["foreground"], current["foreground"])
        self.assertEqual(len(vivid["ansi"]), 16)
        self.assertEqual(balanced["background"], "#000000")
        self.assertEqual(balanced["foreground"], current["foreground"])
        self.assertEqual(len(balanced["ansi"]), 16)
        for slot in range(1, 7):
            self.assertGreaterEqual(builder.contrast_ratio(balanced["ansi"][slot], "#000000"), 4.5)
            self.assertGreater(builder.contrast_ratio(balanced["ansi"][slot], balanced["ansi"][slot + 8]), builder.contrast_ratio(current["ansi"][slot], current["ansi"][slot + 8]))
        for model in (balanced_plus, rich):
            self.assertEqual(model["background"], balanced["background"])
            self.assertEqual(model["foreground"], balanced["foreground"])
            self.assertEqual(len(model["ansi"]), 16)
            for slot in range(1, 7):
                self.assertGreaterEqual(builder.contrast_ratio(model["ansi"][slot], "#000000"), 4.5)
                self.assertGreaterEqual(builder.contrast_ratio(model["ansi"][slot], model["ansi"][slot + 8]), 1.45)
        self.assertEqual(identity["direction"]["colors"]["surface"], "#1b1d1f")
        self.assertEqual(identity["terminal"]["colors"]["background"], "#000000")
        self.assertEqual(identity["terminal"]["ansi"], balanced_plus["ansi"])
        fragment = (self.output / "examples/kitty/neutral-slate.conf").read_text()
        self.assertIn("background #000000", fragment)
        study["terminal_variants"][0]["background"] = "#111111"
        (self.output / "data/contrast-study.json").write_text(json.dumps(study))
        with self.assertRaisesRegex(ValueError, "contrast study differs"):
            builder.validate(self.output)

    def test_contrast_study_rejects_a_changed_selected_baseline(self):
        identity = builder.working_identity()
        identity["source_sha256"] = "0" * 64
        with patch.object(builder, "working_identity", return_value=identity):
            with self.assertRaisesRegex(ValueError, "reviewed baseline"):
                builder.contrast_study()

    def test_portable_review_keeps_links_valid_without_the_project_mount(self):
        builder.build(self.output, portable=True)
        text = (self.output / "design/index.html").read_text()
        self.assertIn('href="../assets/identity.css"', text)
        self.assertIn('href="../recipes/terminal/"', text)
        self.assertIn('href="../recipes/appearance/"', text)
        self.assertIn('href="https://dev.byebyebryan.com/niri-plus/design/"', text)
        tour = (self.output / "tour/index.html").read_text()
        self.assertIn('poster="../assets/demo-overview.png"', tour)
        self.assertIn('src="../assets/demo-overview.mp4"', tour)
        self.assertIn('href="../assets/demo-overview.mp4"', tour)
        self.assertIn('href="../docs/planning/desktop-demonstration-receipt.md"', tour)
        self.assertIn('href="../tools/vm/desktop/wlr-compat/README.md"', tour)
        self.assertIn('href="https://dev.byebyebryan.com/niri-plus/tour/"', tour)
        for path in ("docs/planning/desktop-demonstration-receipt.md", "tools/vm/desktop/wlr-compat/README.md"):
            self.assertTrue((self.output / path).is_file(), path)

    def test_portable_native_media_rewrites_and_validates_source_fallback_and_poster(self):
        media_paths = {"assets/demo-terminal.mp4", "assets/demo-terminal.png"}
        self.assertTrue(media_paths <= builder.public_files())
        source = f'''<video poster="{builder.BASE}assets/demo-terminal.png"><source src="{builder.BASE}assets/demo-terminal.mp4" type="video/mp4"><a href="{builder.BASE}assets/demo-terminal.mp4"><img src="{builder.BASE}assets/demo-terminal.png" alt="Native sample"></a></video><link rel="canonical" href="{builder.SITE}tour/">'''
        portable = builder.portable_links(source, "tour")
        self.assertIn('poster="../assets/demo-terminal.png"', portable)
        self.assertIn('src="../assets/demo-terminal.mp4"', portable)
        self.assertIn('href="../assets/demo-terminal.mp4"', portable)
        self.assertIn('src="../assets/demo-terminal.png"', portable)
        self.assertIn(f'href="{builder.SITE}tour/"', portable)
        self.assertNotIn(builder.BASE + "assets/demo-terminal", portable)
        page = builder.Page(portable)
        media_links = [target for target in page.links if "demo-terminal." in target]
        self.assertCountEqual(media_links, [
            "../assets/demo-terminal.png",
            "../assets/demo-terminal.mp4",
            "../assets/demo-terminal.mp4",
            "../assets/demo-terminal.png",
        ])
        for target in media_links:
            url = builder.urlsplit(builder.urljoin(builder.SITE + "tour/", target))
            destination = builder.unquote(url.path[len(builder.BASE):])
            self.assertIn(destination, builder.public_files())

    def test_terminal_and_utility_recipes_export_pinned_sources_and_isolated_check(self):
        builder.build(self.output)
        terminal = (self.output / "recipes/terminal/index.html").read_text()
        utilities = (self.output / "recipes/desktop-utilities/index.html").read_text()
        self.assertIn("zsh-neutral-slate", terminal)
        self.assertIn("does not edit", terminal)
        self.assertIn("UDisks2", utilities)
        self.assertIn("desktop-lock.service", utilities)
        for relative in (
            "examples/terminal/fetch.py",
            "examples/terminal/init.zsh",
            "examples/terminal/pins.json",
            "examples/terminal/THIRD_PARTY_NOTICES.md",
            "examples/desktop/desktop-session-menu",
            "examples/desktop/niri-plus-network.desktop",
            "examples/desktop/power.toml.example",
            "scripts/check-terminal.py",
        ):
            self.assertTrue((self.output / relative).is_file(), relative)
        manifest = json.loads((self.output / "examples/manifest.json").read_text())
        metadata = json.loads((ROOT / "components/metadata.json").read_text())
        terminal_exports = {item["path"] for item in metadata["exports"] if item["path"].startswith("examples/terminal/")}
        self.assertEqual({item["path"] for item in manifest["files"] if item["path"].startswith("examples/terminal/")}, terminal_exports)
        self.assertIn("scripts/check-terminal.py", {item["path"] for item in manifest["files"]})

    def test_old_slate_blue_terminal_example_remains_a_historical_file(self):
        builder.build(self.output)
        historical = (self.output / "examples/kitty/slate-blue.conf").read_text()
        self.assertIn("Slate Blue - appearance proposal, not deployed", historical)
        self.assertIn("background #202326", historical)
        self.assertIn("color4 #83b8f5", historical)

    def test_nonempty_output_is_preserved(self):
        self.output.mkdir()
        recovery = self.output / "recovery.txt"
        recovery.write_text("keep this")
        with self.assertRaisesRegex(ValueError, "empty"):
            builder.build(self.output)
        self.assertEqual(recovery.read_text(), "keep this")

    def test_personal_notes_have_not_been_embedded_in_examples(self):
        manifest = json.loads((ROOT / "examples/manifest.json").read_text())
        for item in manifest["files"]:
            text = (ROOT / item["path"]).read_text()
            self.assertNotIn("/home/bryan", text)
            self.assertNotIn("tmux-observer-desktop", text)
            self.assertNotIn("honor-xdg-activation-with-invalid-serial", text)


if __name__ == "__main__":
    unittest.main()
