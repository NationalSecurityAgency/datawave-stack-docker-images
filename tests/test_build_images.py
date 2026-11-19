import contextlib
import importlib.util
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "build_images", Path(__file__).resolve().parents[1] / "scripts/build-images.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {"HADOOP_REPO_CONFIG": "synthetic-secret-marker"})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_java_chains_use_built_targets_in_both_registries(self):
        args = build.arguments(["--registry", "ghcr.io/example", "--registry", "registry.example:5000/team"])
        plan = build.plan(args)
        self.assertEqual(len(plan["target"]), 6)
        for java in ("11", "17"):
            base = plan["target"][f"base-{java}"]
            hadoop = plan["target"][f"hadoop-{java}"]
            accumulo = plan["target"][f"accumulo-{java}"]
            self.assertEqual(base["args"]["JAVA_VERSION"], java)
            self.assertEqual(hadoop["contexts"]["stack-base"], f"target:base-{java}")
            self.assertEqual(accumulo["contexts"]["stack-hadoop"], f"target:hadoop-{java}")
            self.assertEqual(hadoop["args"]["BASE_IMAGE"], "stack-base")
            self.assertEqual(accumulo["args"]["HADOOP_IMAGE"], "stack-hadoop")
            for target in (hadoop, accumulo):
                self.assertTrue(all(f"java{java}" in tag for tag in target["tags"]))
                self.assertTrue(any(tag.startswith("registry.example:5000/team/") for tag in target["tags"]))

    def test_secret_is_referenced_without_value_in_plan(self):
        import json
        plan = build.plan(build.arguments([]))
        self.assertNotIn("synthetic-secret-marker", json.dumps(plan))
        self.assertEqual(plan["target"]["hadoop-11"]["secret"],
                         ["id=artifactory_repo,env=HADOOP_REPO_CONFIG"])
        self.assertNotIn("secret", plan["target"]["accumulo-11"])

    def test_source_tags_do_not_replace_release_tags(self):
        args = build.arguments(["--java", "17", "--tag", "2.1.7-SNAPSHOT-dwv-abcdef"])
        tags = build.plan(args)["target"]["accumulo-17"]["tags"]
        self.assertTrue(all(":2.1.7-SNAPSHOT-dwv-abcdef-" in tag for tag in tags))

    def test_debug_images_have_distinct_tags(self):
        args = build.arguments(["--java", "11", "--debug-symbols"])
        plan = build.plan(args)
        for name in ("hadoop-11", "accumulo-11"):
            self.assertTrue(all(tag.endswith("-debug") for tag in plan["target"][name]["tags"]))

    def test_local_rpms_exclude_debug_unrelated_and_wrong_versions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in (*build.HADOOP_PACKAGES, "hadoop-debuginfo", "hadoop-libhdfspp"):
                (root / f"{name}-3.4.3-1.x86_64.rpm").touch()
            (root / "hadoop-3.4.2-1.x86_64.rpm").touch()
            (root / "bigtop-utils-3.3.0-1.noarch.rpm").touch()
            (root / "credentials").touch()
            args = build.arguments(["--hadoop-source", "local", "--rpm-dir", directory])
            selected = [p.name for p in build.selected_rpms(args)]
            self.assertEqual(len(selected), len(build.HADOOP_PACKAGES) + 1)
            self.assertFalse(any("debuginfo" in p or "libhdfspp" in p or "3.4.2" in p for p in selected))
            (root / "hadoop-3.4.3-2.x86_64.rpm").touch()
            with self.assertRaisesRegex(ValueError, "exactly one hadoop"):
                build.selected_rpms(args)

    def test_missing_repo_fails_before_docker(self):
        with patch.dict(os.environ, {}, clear=True), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                build.arguments([])

    def test_invalid_inputs_fail_before_docker(self):
        for argv in (["--java", "21"], ["--registry", "https://registry.example/team"],
                     ["--tag", "feature/x"], ["--hadoop-source", "local"]):
            with self.subTest(argv=argv), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    build.arguments(argv)

    def test_failure_prevents_all_pushes(self):
        import subprocess
        with patch.object(build, "run") as run, patch.object(build, "smoke_tests") as smoke:
            smoke.side_effect = subprocess.CalledProcessError(1, "smoke")
            with self.assertRaises(subprocess.CalledProcessError):
                build.main(["--push"])
            self.assertEqual(run.call_count, 1)
            self.assertEqual(run.call_args.args[0][:3], ["docker", "buildx", "bake"])

    def test_push_uses_loaded_images_after_verification(self):
        calls = []
        with patch.object(build, "run", side_effect=lambda command, **kw: calls.append(command)), \
                patch.object(build, "smoke_tests", side_effect=lambda *a: calls.append(["verified"])), \
                contextlib.redirect_stdout(io.StringIO()):
            build.main(["--java", "17", "--push", "--registry", "ghcr.io/example"])
        self.assertEqual(calls[1], ["verified"])
        self.assertTrue(all(command[:2] == ["docker", "push"] for command in calls[2:]))


if __name__ == "__main__":
    unittest.main()
