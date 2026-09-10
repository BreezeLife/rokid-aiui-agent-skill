import os
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "rokid-aiui-agent" / "scripts" / "smoke_aix.sh"


class AixSmokeScriptTests(unittest.TestCase):
    def run_smoke(self, help_text, list_text, *, pack_succeeds=True):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            (project / "pages" / "index").mkdir(parents=True)
            (project / "app.json").write_text(
                '{"pages":["pages/index/index"]}\n', encoding="utf-8"
            )
            (project / "pages" / "index" / "index.ink").write_text(
                "<page></page>\n", encoding="utf-8"
            )
            fake = root / "aix-fake"
            fake.write_text(
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    case "$1" in
                      --help)
                        printf '%b\\n' {help_text!r}
                        ;;
                      pack)
                        if [ {str(pack_succeeds).lower()!r} != 'true' ]; then
                          exit 9
                        fi
                        shift
                        output=''
                        while [ "$#" -gt 0 ]; do
                          if [ "$1" = '-o' ]; then
                            output="$2"
                            shift 2
                          else
                            shift
                          fi
                        done
                        printf 'fake-aix' > "$output"
                        ;;
                      list|ls)
                        printf '%b\\n' {list_text!r}
                        ;;
                      *) exit 8 ;;
                    esac
                    """
                ),
                encoding="utf-8",
            )
            fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
            env = os.environ.copy()
            env["AIX_BIN"] = str(fake)
            return subprocess.run(
                ["bash", str(SCRIPT), str(project)],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

    def test_packages_and_lists_with_advertised_commands(self):
        result = self.run_smoke(
            "Usage: aix pack <INPUT_DIR>\n  aix list <AIX_FILE>",
            "META-INF/aix/manifest.json\napp.json\npages/index/index.ink",
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("AIX smoke passed", result.stdout)

    def test_accepts_published_aix_list_metadata_format(self):
        result = self.run_smoke(
            "Usage: aix pack <INPUT_DIR>\n  aix list <AIX_FILE>",
            (
                "META-INF/aix/manifest.json: 180 bytes (compressed: 121 bytes)\n"
                "app.json: 37 bytes (compressed: 39 bytes)\n"
                "pages/index/index.ink: 28 bytes (compressed: 24 bytes)"
            ),
        )

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("AIX smoke passed", result.stdout)

    def test_rejects_cli_without_pack(self):
        result = self.run_smoke(
            "Usage: aix preview <INPUT>", "app.json\npages/index/index.ink"
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("does not advertise pack", result.stderr)

    def test_rejects_listing_without_expected_page(self):
        result = self.run_smoke(
            "aix pack\naix list", "META-INF/aix/manifest.json\napp.json"
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("pages/index/index.ink", result.stderr)

    def test_rejects_near_match_for_app_json_entry(self):
        result = self.run_smoke(
            "aix pack\naix list",
            (
                "META-INF/aix/manifest.json\n"
                "not-app.json.backup\n"
                "pages/index/index.ink"
            ),
        )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("app.json", result.stderr)

    def test_rejects_near_match_for_page_entry(self):
        result = self.run_smoke(
            "aix pack\naix list",
            (
                "META-INF/aix/manifest.json\n"
                "app.json\n"
                "prefix/pages/index/index.ink.backup"
            ),
        )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("pages/index/index.ink", result.stderr)

    def test_rejects_listing_without_package_manifest(self):
        result = self.run_smoke(
            "aix pack\naix list", "app.json\npages/index/index.ink"
        )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("META-INF/aix/manifest.json", result.stderr)

    def test_rejects_package_that_contains_reserved_audit_evidence(self):
        for reserved_entry in (
            ".aiui-evidence/device-capture.png",
            ".aiui-evidence/device-capture.png: 42 bytes (compressed: 8 bytes)",
            ".aiui-evidence: 0 bytes (compressed: 0 bytes)",
            ".git: 42 bytes (compressed: 8 bytes)",
            "./.git/config: 42 bytes (compressed: 8 bytes)",
            ".AIUI-EVIDENCE/device-capture.png: 42 bytes (compressed: 8 bytes)",
            "./.Git/config: 42 bytes (compressed: 8 bytes)",
        ):
            with self.subTest(reserved_entry=reserved_entry):
                result = self.run_smoke(
                    "aix pack\naix list",
                    (
                        "META-INF/aix/manifest.json\n"
                        "app.json\n"
                        "pages/index/index.ink\n"
                        f"{reserved_entry}"
                    ),
                )

                self.assertNotEqual(0, result.returncode)
                self.assertIn("reserved", result.stderr.lower())

    def test_force_package_mode_ignores_aix_on_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            (project / "pages" / "index").mkdir(parents=True)
            (project / "app.json").write_text(
                '{"pages":["pages/index/index"]}\n', encoding="utf-8"
            )
            (project / "pages" / "index" / "index.ink").write_text(
                "<page></page>\n", encoding="utf-8"
            )

            fake_bin = root / "bin"
            fake_bin.mkdir()
            path_aix = fake_bin / "aix"
            path_aix.write_text(
                "#!/bin/sh\necho 'unexpected PATH aix' >&2\nexit 97\n",
                encoding="utf-8",
            )
            path_aix.chmod(path_aix.stat().st_mode | stat.S_IXUSR)

            package_runner = fake_bin / "npx"
            package_runner.write_text(
                textwrap.dedent(
                    """\
                    #!/bin/sh
                    set -eu
                    [ "$1" = '--yes' ]
                    [ "$2" = '--package' ]
                    [ "$3" = '@example/aix-cli@1.2.3' ]
                    [ "$4" = 'aix' ]
                    shift 4
                    case "$1" in
                      --help)
                        printf '%s\n' 'aix pack' 'aix list'
                        ;;
                      pack)
                        shift
                        output=''
                        while [ "$#" -gt 0 ]; do
                          if [ "$1" = '-o' ]; then
                            output="$2"
                            shift 2
                          else
                            shift
                          fi
                        done
                        printf 'fake-aix' > "$output"
                        ;;
                      list)
                        printf '%s\n' \
                          'META-INF/aix/manifest.json' \
                          'app.json' \
                          'pages/index/index.ink'
                        ;;
                      *) exit 8 ;;
                    esac
                    """
                ),
                encoding="utf-8",
            )
            package_runner.chmod(package_runner.stat().st_mode | stat.S_IXUSR)

            env = os.environ.copy()
            env.pop("AIX_BIN", None)
            env["AIX_FORCE_PACKAGE"] = "1"
            env["AIX_PACKAGE"] = "@example/aix-cli@1.2.3"
            env["PATH"] = os.pathsep.join(
                (str(fake_bin), str(Path(sys.executable).parent), "/usr/bin", "/bin")
            )

            result = subprocess.run(
                ["bash", str(SCRIPT), str(project)],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertNotIn("unexpected PATH aix", result.stderr)
        self.assertIn("AIX smoke passed", result.stdout)

    def test_propagates_pack_failure(self):
        result = self.run_smoke(
            "aix pack\naix list",
            "app.json\npages/index/index.ink",
            pack_succeeds=False,
        )
        self.assertNotEqual(0, result.returncode)


if __name__ == "__main__":
    unittest.main()
