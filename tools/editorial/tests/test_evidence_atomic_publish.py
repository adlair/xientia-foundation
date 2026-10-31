"""F4.3 R2-C: evidence-aware atomic publication guards."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

EDITORIAL = Path(__file__).resolve().parents[1]
SOURCE_REPO = EDITORIAL.parents[1]

sys.path.insert(0, str(EDITORIAL))

from validated_publish import publish_validated


class EvidenceAtomicPublishTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(
            prefix="xientia-r2c-tests-"
        )
        cls.addClassCleanup(cls.temporary.cleanup)

        cls.base = Path(cls.temporary.name)
        cls.repo = cls.base / "repo"

        subprocess.run(
            [
                "git", "clone", "--no-hardlinks",
                "--quiet", str(SOURCE_REPO), str(cls.repo),
            ],
            check=True,
        )

    def args(self, out, allow_dirty=False):
        return SimpleNamespace(
            repo=self.repo,
            out=out,
            volume="XV-001",
            format="all",
            allow_dirty=allow_dirty,
            publish_with_evidence=True,
        )

    def test_existing_destination_rejected(self):
        out = self.base / "existing-destination"
        out.mkdir(exist_ok=True)
        protected = out / "protected.txt"
        protected.write_text("ORIGINAL", encoding="utf-8")

        with self.assertRaises(FileExistsError):
            publish_validated(
                self.args(out),
                EDITORIAL / "render_library.py",
            )

        self.assertEqual(
            protected.read_text(encoding="utf-8"),
            "ORIGINAL",
        )

    def test_dirty_mode_rejected_before_publication(self):
        with tempfile.TemporaryDirectory(
            prefix="xientia-r2c-dirty-"
        ) as temporary:
            out = Path(temporary) / "published"

            with patch(
                "validated_publish.run_supervised",
                side_effect=AssertionError("renderer was invoked"),
            ) as renderer:
                with self.assertRaisesRegex(
                    ValueError,
                    "Evidence publication requires a clean repository",
                ):
                    publish_validated(
                        self.args(out, allow_dirty=True),
                        EDITORIAL / "render_library.py",
                    )

                renderer.assert_not_called()

            self.assertFalse(out.exists())

    def test_evidence_generation_failure_never_publishes(self):
        with tempfile.TemporaryDirectory(
            prefix="xientia-r2c-generator-failure-"
        ) as temporary:
            root = Path(temporary)
            out = root / "published"

            # Renderizado real, con artefactos válidos.
            original_run = subprocess.run

            def render_real(cmd):
                original_run(
                    cmd,
                    check=True,
                    stdout=subprocess.DEVNULL,
                )

            with patch(
                "validated_publish.run_supervised",
                side_effect=render_real,
            ), patch(
                "ci.evidence_generate.generate_and_write_evidence",
                side_effect=RuntimeError(
                    "simulated evidence generation failure"
                ),
            ) as generator, patch(
                "validated_publish.publish_noreplace",
            ) as publisher:
                with self.assertRaisesRegex(
                    RuntimeError,
                    "simulated evidence generation failure",
                ):
                    publish_validated(
                        self.args(out),
                        EDITORIAL / "render_library.py",
                    )

                generator.assert_called_once()
                publisher.assert_not_called()

            self.assertFalse(out.exists())
            self.assertEqual(
                list(root.glob(".xientia-f42-*")),
                [],
            )



    def test_real_concurrent_evidence_publication(self):
        from ci.evidence_verify import verify_package

        with tempfile.TemporaryDirectory(
            prefix="xientia-r2c-concurrent-"
        ) as temporary:
            root = Path(temporary)
            destination = root / "published"

            command = [
                sys.executable,
                str(EDITORIAL / "render_library.py"),
                "--repo", str(self.repo),
                "--volume", "XV-001",
                "--out", str(destination),
                "--validate-publish",
                "--publish-with-evidence",
            ]

            workers = [
                subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    start_new_session=True,
                    env={
                        **os.environ,
                        "PYTHONDONTWRITEBYTECODE": "1",
                    },
                )
                for _ in range(2)
            ]

            results = []

            try:
                for worker in workers:
                    stdout, stderr = worker.communicate(
                        timeout=120
                    )
                    results.append(
                        (worker.returncode, stdout, stderr)
                    )
            finally:
                for worker in workers:
                    if worker.poll() is None:
                        os.killpg(worker.pid, 9)
                        worker.communicate()

            codes = [item[0] for item in results]

            self.assertEqual(codes.count(0), 1)
            self.assertEqual(
                sum(code != 0 for code in codes), 1
            )

            self.assertTrue(destination.is_dir())

            evidence = json.loads(
                (destination / "evidence.json").read_text(
                    encoding="utf-8"
                )
            )

            verified = verify_package(
                self.repo, destination, evidence
            )

            self.assertEqual(
                verified["document"], "XV-001"
            )
            self.assertEqual(
                verified["artifacts_verified"], 3
            )

            self.assertEqual(
                list(root.glob(".xientia-f42-*")),
                [],
            )


    def test_atomic_publish_failure_after_evidence_generation(self):
        with tempfile.TemporaryDirectory(
            prefix="xientia-r2c-publish-failure-"
        ) as temporary:
            root = Path(temporary)
            destination = root / "published"

            def fail_publish(stage, out):
                required = (
                    "manifest.json",
                    "XV-001_consulta.md",
                    "XV-001_consulta.odt",
                    "pdf/XV-001_consulta.pdf",
                    "evidence.json",
                )

                for name in required:
                    self.assertTrue(
                        (stage / name).is_file(),
                        name,
                    )

                raise OSError("simulated atomic publish failure")

            with patch(
                "validated_publish.publish_noreplace",
                side_effect=fail_publish,
            ) as publisher:
                with self.assertRaisesRegex(
                    OSError,
                    "simulated atomic publish failure",
                ):
                    publish_validated(
                        self.args(destination),
                        EDITORIAL / "render_library.py",
                    )

                publisher.assert_called_once()

            self.assertFalse(destination.exists())
            self.assertEqual(
                list(root.glob(".xientia-f42-*")),
                [],
            )


    def test_interrupt_during_render_leaves_no_publication(self):
        import signal
        import time

        with tempfile.TemporaryDirectory(
            prefix="xientia-r2c-interrupt-"
        ) as temporary:
            root = Path(temporary)
            destination = root / "published"
            ready = root / "ready"

            script = """
import os
import signal
import sys
import time
from pathlib import Path

ready = Path(sys.argv[1])

def fake_render(cmd):
    stage = Path(cmd[cmd.index("--out") + 1])
    stage.mkdir(parents=True, exist_ok=True)
    ready.write_text("ready", encoding="utf-8")
    while True:
        time.sleep(0.1)

import validated_publish
validated_publish.run_supervised = fake_render

from types import SimpleNamespace

args = SimpleNamespace(
    repo=Path(sys.argv[2]),
    out=Path(sys.argv[3]),
    volume="XV-001",
    format="all",
    allow_dirty=False,
    publish_with_evidence=True,
)

validated_publish.publish_validated(
    args,
    Path(sys.argv[4]),
)
"""

            runner = root / "runner.py"
            runner.write_text(script, encoding="utf-8")

            process = subprocess.Popen(
                [
                    sys.executable,
                    str(runner),
                    str(ready),
                    str(self.repo),
                    str(destination),
                    str(EDITORIAL / "render_library.py"),
                ],
                cwd=EDITORIAL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
                env={
                    **os.environ,
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "PYTHONPATH": str(EDITORIAL),
                },
            )

            try:
                deadline = time.monotonic() + 10

                while not ready.exists():
                    if process.poll() is not None:
                        raise AssertionError(
                            "Supervisor exited before readiness"
                        )
                    if time.monotonic() >= deadline:
                        raise TimeoutError("Render readiness timeout")
                    time.sleep(0.05)

                os.killpg(process.pid, signal.SIGINT)
                process.communicate(timeout=10)

                self.assertNotEqual(process.returncode, 0)
                self.assertFalse(destination.exists())
                self.assertEqual(
                    list(root.glob(".xientia-f42-*")),
                    [],
                )
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.communicate()


if __name__ == "__main__":
    unittest.main()
