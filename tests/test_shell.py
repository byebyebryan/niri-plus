import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import tarfile
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
FETCHER_PATH = ROOT / "components/shell/fetch.py"
spec = importlib.util.spec_from_file_location("niri_plus_shell_fetcher", FETCHER_PATH)
fetcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetcher)


def archive_for(project, destination):
    with tarfile.open(destination, "w:gz") as archive:
        root = project["archive_root"]
        directory = tarfile.TarInfo(root + "/")
        directory.type = tarfile.DIRTYPE
        directory.mode = 0o755
        archive.addfile(directory)

        entrypoint = tarfile.TarInfo(f"{root}/{project['entrypoint']}")
        entrypoint.mode = 0o755
        entrypoint_data = f"# fixture {project['name']}\n".encode()
        entrypoint.size = len(entrypoint_data)
        archive.addfile(entrypoint, io.BytesIO(entrypoint_data))

        license_file = tarfile.TarInfo(f"{root}/LICENSE")
        license_file.mode = 0o644
        license_data = f"License for {project['name']}\n".encode()
        license_file.size = len(license_data)
        archive.addfile(license_file, io.BytesIO(license_data))

        if project["name"] == "zsh-autosuggestions":
            link = tarfile.TarInfo(f"{root}/docs/license-link")
            link.type = tarfile.SYMTYPE
            link.linkname = "../LICENSE"
            archive.addfile(link)


class ShellDependencyFetcher(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="niri-plus-shell-fetch-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.home = self.base / "home"
        self.home.mkdir()
        self.source = self.base / "source"
        self.source.mkdir()
        self.archives = self.base / "archives"
        self.archives.mkdir()
        self.projects = []

        entries = {
            "zsh-autosuggestions": "zsh-autosuggestions.zsh",
            "zsh-history-substring-search": "zsh-history-substring-search.zsh",
            "zsh-syntax-highlighting": "zsh-syntax-highlighting.zsh",
            "powerlevel10k": "powerlevel10k.zsh-theme",
        }
        for index, (name, entrypoint) in enumerate(entries.items(), start=1):
            commit = f"{index:040x}"
            project = {
                "name": name,
                "repository": f"https://github.com/example/{name}",
                "commit": commit,
                "archive_url": f"https://codeload.github.com/example/{name}/tar.gz/{commit}",
                "sha256": "0" * 64,
                "archive_root": f"{name}-{commit}",
                "install_directory": name,
                "entrypoint": entrypoint,
                "license": "Fixture",
                "license_file": "LICENSE",
                "attribution": "Test fixture",
            }
            archive_path = self.archives / f"{name}.tar.gz"
            archive_for(project, archive_path)
            project["sha256"] = hashlib.sha256(archive_path.read_bytes()).hexdigest()
            self.projects.append(project)

        (self.source / "pins.json").write_text(json.dumps({"schema_version": 1, "plugins": self.projects}, indent=2) + "\n")
        (self.source / "THIRD_PARTY_NOTICES.md").write_text("Fixture notices\n")
        for name in fetcher.LOCAL_FILES:
            if name in {"pins.json", "THIRD_PARTY_NOTICES.md"}:
                continue
            (self.source / name).write_text(f"local shell file: {name}\n")

        by_url = {project["archive_url"]: self.archives / f"{project['name']}.tar.gz" for project in self.projects}

        def download_fixture(url, destination):
            shutil.copyfile(by_url[url], destination)
            return hashlib.sha256(destination.read_bytes()).hexdigest()

        self.download_patch = mock.patch.object(fetcher, "download", side_effect=download_fixture)
        self.root_patch = mock.patch.object(fetcher, "ROOT", self.source)
        self.download_patch.start()
        self.root_patch.start()
        self.addCleanup(self.download_patch.stop)
        self.addCleanup(self.root_patch.stop)

    def test_dependencies_only_leaf_has_pins_receipt_all_trees_and_no_shell_config(self):
        destination = self.home / "niri-plus-zsh-dependencies"
        with mock.patch.dict(os.environ, {"HOME": str(self.home)}):
            installed = fetcher.main(["--dependencies-only", str(destination)])
        self.assertEqual(installed, 0)

        self.assertEqual(
            {path.name for path in destination.iterdir()},
            {"plugins", "pins.json", "THIRD_PARTY_NOTICES.md", "receipt.json"},
        )
        receipt = json.loads((destination / "receipt.json").read_text())
        pins_bytes = (destination / "pins.json").read_bytes()
        self.assertEqual(receipt["schema_version"], 1)
        self.assertEqual(receipt["pins_sha256"], hashlib.sha256(pins_bytes).hexdigest())
        self.assertEqual({item["name"] for item in receipt["plugins"]}, {project["name"] for project in self.projects})
        self.assertIn("powerlevel10k", {item["name"] for item in receipt["plugins"]})

        paths = {item["path"]: item for item in receipt["files"]}
        self.assertIn("pins.json", paths)
        self.assertIn("THIRD_PARTY_NOTICES.md", paths)
        for project in self.projects:
            base = destination / "plugins" / project["install_directory"]
            self.assertTrue((base / project["entrypoint"]).is_file())
            self.assertTrue((base / "LICENSE").is_file())
            self.assertIn(f"plugins/{project['install_directory']}/LICENSE", paths)

        for relative, record in paths.items():
            path = destination / relative
            if record["type"] == "file":
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), record["sha256"])
            else:
                self.assertTrue(path.is_symlink())
                target = os.readlink(path)
                self.assertEqual(target, record["target"])
                self.assertEqual(hashlib.sha256(os.fsencode(target)).hexdigest(), record["sha256"])
        self.assertEqual(paths["plugins/zsh-autosuggestions/docs/license-link"]["type"], "symlink")

        forbidden = {"zshrc", "init.zsh", "p10k.zsh", "p10k-custom-segments.zsh", "fetch.py"}
        self.assertFalse(forbidden & {path.name for path in destination.iterdir()})

    def test_regular_installer_still_copies_the_portable_starter_files(self):
        destination = self.home / "niri-plus-zsh-bundle"
        with mock.patch.dict(os.environ, {"HOME": str(self.home)}):
            installed = fetcher.install(destination)
        self.assertEqual(installed, destination)
        for name in fetcher.LOCAL_FILES:
            self.assertTrue((destination / name).is_file(), name)
        self.assertTrue((destination / "plugins/powerlevel10k/powerlevel10k.zsh-theme").is_file())
        self.assertEqual((destination / "init.zsh").read_text(), (self.source / "init.zsh").read_text())


if __name__ == "__main__":
    unittest.main()
