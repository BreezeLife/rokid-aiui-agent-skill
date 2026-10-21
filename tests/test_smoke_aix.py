import hashlib
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
    def run_smoke(
        self,
        help_text,
        list_text,
        *,
        pack_succeeds=True,
        list_includes_app_entry=True,
    ):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            (project / "pages" / "index").mkdir(parents=True)
            (project / "app.json").write_text(
                '{"pages":["pages/index/index"]}\n', encoding="utf-8"
            )
            (project / "app.js").write_text("App({});\n", encoding="utf-8")
            (project / "pages" / "index" / "index.ink").write_text(
                "<page></page>\n", encoding="utf-8"
            )
            if list_includes_app_entry:
                list_text = f"app.js\n{list_text}"
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

    def run_delivery(
        self,
        *,
        list_text=(
            "META-INF/aix/manifest.json\n"
            "app.json\n"
            "app.js\n"
            "pages/index/index.ink\n"
            "pages/details/index.ink"
        ),
        list_succeeds=True,
        output_location="external",
        create_existing=False,
        create_broken_symlink=False,
        include_repository_root=True,
        output_suffix=".aix",
        mutate_source_during_pack=False,
        aba_source_during_pack=False,
        replace_destination_with_directory=False,
        replace_destination_with_symlink=False,
        replace_destination_with_file_on_final_list=False,
        replacement_list_succeeds=False,
        project_is_repository=False,
        empty_pages=False,
        fail_on_list_call=None,
    ):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = root / ("ProjectRoot" if project_is_repository else "repository")
            project = repository if project_is_repository else repository / "project"
            (project / "pages" / "index").mkdir(parents=True)
            (project / "pages" / "details").mkdir(parents=True)
            (project / "AGENTS.md").write_text("# Agent\n", encoding="utf-8")
            (project / "app.js").write_text("App({});\n", encoding="utf-8")
            manifest = (
                '{"pages":[]}\n'
                if empty_pages
                else '{"pages":["pages/index/index","pages/details/index"]}\n'
            )
            (project / "app.json").write_text(manifest, encoding="utf-8")
            (project / "pages" / "index" / "index.ink").write_text(
                "<page></page>\n", encoding="utf-8"
            )
            (project / "pages" / "details" / "index.ink").write_text(
                "<page></page>\n", encoding="utf-8"
            )

            case_alias_supported = False
            if output_location == "inside":
                output = project / "dist" / f"agent{output_suffix}"
            elif output_location == "inside_case_alias":
                alias = project.with_name(project.name.swapcase())
                case_alias_supported = alias.exists() and os.path.samefile(alias, project)
                output = alias / ".aiui-evidence" / f"agent{output_suffix}"
            else:
                output = root / "deliveries" / f"agent{output_suffix}"
            if create_existing:
                output.parent.mkdir(parents=True)
                output.write_bytes(b"keep-existing")
            if create_broken_symlink:
                output.parent.mkdir(parents=True)
                output.symlink_to(output.parent / "missing-target.aix")
            attacker_directory = root / "attacker"
            if replace_destination_with_symlink:
                attacker_directory.mkdir()

            list_log = root / "list-paths.log"
            fake = root / "aix-fake"
            fake.write_text(
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    case "$1" in
                      --help)
                        printf '%s\\n' 'aix pack' 'aix list'
                        ;;
                      pack)
                        shift
                        input="$1"
                        output=''
                        while [ "$#" -gt 0 ]; do
                          if [ "$1" = '-o' ]; then
                            output="$2"
                            shift 2
                          else
                            shift
                          fi
                        done
                        if [ "$AIX_FAKE_ABA_SOURCE" = '1' ]; then
                          cp "$AIX_FAKE_PROJECT/app.js" "$AIX_FAKE_BACKUP"
                          printf 'transient source\n' > "$AIX_FAKE_PROJECT/app.js"
                          cat "$input/app.js" > "$output"
                          cp "$AIX_FAKE_BACKUP" "$AIX_FAKE_PROJECT/app.js"
                        else
                          printf 'fake-aix' > "$output"
                        fi
                        if [ "$AIX_FAKE_MUTATE_SOURCE" = '1' ]; then
                          printf '\\nchanged during pack\\n' >> "$AIX_FAKE_PROJECT/app.js"
                        fi
                        ;;
                      list)
                        printf '%s\\n' "$2" >> "$AIX_FAKE_LIST_LOG"
                        if [ {str(list_succeeds).lower()!r} != 'true' ]; then
                          exit 7
                        fi
                        list_calls="$(wc -l < "$AIX_FAKE_LIST_LOG" | tr -d '[:space:]')"
                        if [ "$AIX_FAKE_DESTINATION_DIRECTORY" = '1' ] && [ "$list_calls" = '1' ]; then
                          mkdir -p "$AIX_FAKE_DELIVERY_OUTPUT"
                        fi
                        if [ "$AIX_FAKE_DESTINATION_SYMLINK" = '1' ] && [ "$list_calls" = '1' ]; then
                          ln -s "$AIX_FAKE_ATTACKER_DIRECTORY" "$AIX_FAKE_DELIVERY_OUTPUT"
                        fi
                        if [ "$AIX_FAKE_DESTINATION_FILE" = '1' ] && [ "$list_calls" = '2' ]; then
                          rm -f "$AIX_FAKE_DELIVERY_OUTPUT"
                          printf 'concurrent replacement' > "$AIX_FAKE_DELIVERY_OUTPUT"
                          if [ "$AIX_FAKE_REPLACEMENT_LIST_SUCCEEDS" != '1' ]; then
                            exit 6
                          fi
                        fi
                        if [ -n "$AIX_FAKE_FAIL_ON_LIST_CALL" ] && [ "$list_calls" = "$AIX_FAKE_FAIL_ON_LIST_CALL" ]; then
                          exit 6
                        fi
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
            env["AIX_FAKE_LIST_LOG"] = str(list_log)
            env["AIX_FAKE_PROJECT"] = str(project)
            env["AIX_FAKE_MUTATE_SOURCE"] = (
                "1" if mutate_source_during_pack else "0"
            )
            env["AIX_FAKE_ABA_SOURCE"] = "1" if aba_source_during_pack else "0"
            env["AIX_FAKE_BACKUP"] = str(root / "source-backup.js")
            env["AIX_FAKE_DELIVERY_OUTPUT"] = str(output)
            env["AIX_FAKE_DESTINATION_DIRECTORY"] = (
                "1" if replace_destination_with_directory else "0"
            )
            env["AIX_FAKE_DESTINATION_SYMLINK"] = (
                "1" if replace_destination_with_symlink else "0"
            )
            env["AIX_FAKE_ATTACKER_DIRECTORY"] = str(attacker_directory)
            env["AIX_FAKE_DESTINATION_FILE"] = (
                "1" if replace_destination_with_file_on_final_list else "0"
            )
            env["AIX_FAKE_REPLACEMENT_LIST_SUCCEEDS"] = (
                "1" if replacement_list_succeeds else "0"
            )
            env["AIX_FAKE_FAIL_ON_LIST_CALL"] = (
                "" if fail_on_list_call is None else str(fail_on_list_call)
            )
            command = ["bash", str(SCRIPT), str(project), str(output)]
            if include_repository_root:
                command.append(str(repository))
            result = subprocess.run(
                command,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            return {
                "result": result,
                "output": output.resolve(),
                "exists": output.exists(),
                "is_symlink": output.is_symlink(),
                "bytes": output.read_bytes() if output.is_file() else None,
                "list_paths": (
                    list_log.read_text(encoding="utf-8").splitlines()
                    if list_log.is_file()
                    else []
                ),
                "case_alias_supported": case_alias_supported,
                "nested_fixture_exists": (output / "fixture.aix").exists(),
                "attacker_nested_exists": (attacker_directory / "fixture.aix").exists(),
            }

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

    def test_uses_advertised_ls_alias(self):
        result = self.run_smoke(
            "Usage: aix pack <INPUT_DIR>\n  aix ls <AIX_FILE>",
            "META-INF/aix/manifest.json\napp.json\npages/index/index.ink",
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

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

    def test_rejects_listing_without_application_entry(self):
        result = self.run_smoke(
            "aix pack\naix list",
            "META-INF/aix/manifest.json\napp.json\npages/index/index.ink",
            list_includes_app_entry=False,
        )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("app.js", result.stderr)

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
            (project / "app.js").write_text("App({});\n", encoding="utf-8")
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
                          'app.js' \
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

    def test_delivery_preserves_verified_archive_and_reports_identity(self):
        delivery = self.run_delivery()
        result = delivery["result"]
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertTrue(delivery["exists"])
        self.assertEqual(b"fake-aix", delivery["bytes"])
        self.assertEqual(str(delivery["output"]), delivery["list_paths"][-1])
        self.assertIn(f"AIUI source fingerprint: WORKTREE:", result.stdout)
        self.assertIn(f"AIX artifact: {delivery['output']}", result.stdout)
        self.assertIn("AIX bytes: 8", result.stdout)
        self.assertIn(
            f"AIX SHA-256: {hashlib.sha256(b'fake-aix').hexdigest()}",
            result.stdout,
        )

    def test_delivery_requires_explicit_repository_root(self):
        delivery = self.run_delivery(include_repository_root=False)
        self.assertNotEqual(0, delivery["result"].returncode)
        self.assertFalse(delivery["exists"])
        self.assertIn("repository root", delivery["result"].stderr.lower())

    def test_delivery_refuses_destination_inside_import_root(self):
        delivery = self.run_delivery(output_location="inside")
        self.assertNotEqual(0, delivery["result"].returncode)
        self.assertFalse(delivery["exists"])
        self.assertIn("outside", delivery["result"].stderr.lower())

    def test_delivery_refuses_to_overwrite_existing_archive(self):
        delivery = self.run_delivery(create_existing=True)
        self.assertNotEqual(0, delivery["result"].returncode)
        self.assertEqual(b"keep-existing", delivery["bytes"])
        self.assertIn("already exists", delivery["result"].stderr.lower())

    def test_delivery_refuses_broken_destination_symlink(self):
        delivery = self.run_delivery(create_broken_symlink=True)
        self.assertNotEqual(0, delivery["result"].returncode)
        self.assertTrue(delivery["is_symlink"])
        self.assertIn("already exists", delivery["result"].stderr.lower())

    def test_delivery_requires_lowercase_aix_suffix(self):
        delivery = self.run_delivery(output_suffix=".zip")
        self.assertNotEqual(0, delivery["result"].returncode)
        self.assertFalse(delivery["exists"])
        self.assertIn(".aix", delivery["result"].stderr)

    def test_delivery_failure_leaves_no_archive(self):
        delivery = self.run_delivery(list_succeeds=False)
        self.assertNotEqual(0, delivery["result"].returncode)
        self.assertFalse(delivery["exists"])

    def test_final_listing_failure_removes_new_delivery(self):
        delivery = self.run_delivery(fail_on_list_call=2)
        self.assertNotEqual(0, delivery["result"].returncode)
        self.assertFalse(delivery["exists"])
        self.assertFalse(delivery["is_symlink"])
        self.assertIn("final AIX artifact listing failed", delivery["result"].stderr)

    def test_source_change_during_pack_rejects_delivery(self):
        delivery = self.run_delivery(mutate_source_during_pack=True)
        self.assertNotEqual(0, delivery["result"].returncode)
        self.assertFalse(delivery["exists"])
        self.assertIn("fingerprint changed", delivery["result"].stderr.lower())

    def test_delivery_packages_a_verified_snapshot_not_aba_live_source(self):
        delivery = self.run_delivery(aba_source_during_pack=True)
        result = delivery["result"]
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(b"App({});\n", delivery["bytes"])

    def test_destination_directory_race_cannot_create_a_nested_archive(self):
        delivery = self.run_delivery(replace_destination_with_directory=True)
        self.assertNotEqual(0, delivery["result"].returncode)
        self.assertFalse(delivery["nested_fixture_exists"])

    def test_destination_symlink_race_cannot_leak_a_nested_archive(self):
        delivery = self.run_delivery(replace_destination_with_symlink=True)
        self.assertNotEqual(0, delivery["result"].returncode)
        self.assertFalse(delivery["attacker_nested_exists"])

    def test_failed_cleanup_preserves_a_concurrent_replacement(self):
        delivery = self.run_delivery(replace_destination_with_file_on_final_list=True)
        self.assertNotEqual(0, delivery["result"].returncode)
        self.assertTrue(delivery["exists"])
        self.assertEqual(b"concurrent replacement", delivery["bytes"])

    def test_cleanup_preserves_changed_bytes_when_inode_is_reused(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "agent.aix"
            original = b"original-aix"
            replacement = b"replaced-aix"
            self.assertEqual(len(original), len(replacement))
            output.write_bytes(replacement)
            reused = output.stat()
            # Reproduce a recycled Linux inode deterministically on every host:
            # the old publication identity now names different, same-size bytes.
            identity = (
                f"{reused.st_dev}:{reused.st_ino}:{len(original)}:"
                f"{hashlib.sha256(original).hexdigest()}"
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT.with_name("aix_delivery_guard.py")),
                    "cleanup",
                    str(output),
                    identity,
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertTrue(output.exists())
            self.assertEqual(replacement, output.read_bytes())

    def test_final_listing_cannot_validate_replaced_artifact_bytes(self):
        delivery = self.run_delivery(
            replace_destination_with_file_on_final_list=True,
            replacement_list_succeeds=True,
        )
        self.assertNotEqual(0, delivery["result"].returncode)
        self.assertTrue(delivery["exists"])
        self.assertEqual(b"concurrent replacement", delivery["bytes"])
        self.assertIn("changed during listing", delivery["result"].stderr.lower())

    def test_case_alias_cannot_place_delivery_inside_import_root(self):
        delivery = self.run_delivery(
            output_location="inside_case_alias", project_is_repository=True
        )
        if not delivery["case_alias_supported"]:
            self.skipTest("filesystem is case-sensitive")
        self.assertNotEqual(0, delivery["result"].returncode)
        self.assertFalse(delivery["exists"])
        self.assertIn("outside", delivery["result"].stderr.lower())

    def test_delivery_requires_every_declared_page(self):
        delivery = self.run_delivery(
            list_text=(
                "META-INF/aix/manifest.json\n"
                "app.json\n"
                "app.js\n"
                "pages/index/index.ink"
            )
        )
        self.assertNotEqual(0, delivery["result"].returncode)
        self.assertFalse(delivery["exists"])
        self.assertIn("pages/details/index.ink", delivery["result"].stderr)

    def test_delivery_rejects_an_empty_pages_manifest(self):
        delivery = self.run_delivery(empty_pages=True)
        self.assertNotEqual(0, delivery["result"].returncode)
        self.assertFalse(delivery["exists"])
        self.assertIn("pages", delivery["result"].stderr.lower())


if __name__ == "__main__":
    unittest.main()
