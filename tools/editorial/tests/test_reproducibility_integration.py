"""F4.4-R1: integration tests using real editorial packages."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

EDITORIAL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EDITORIAL))

from reproducibility_compare import compare_packages


def require_clean_source(source):
    status = subprocess.check_output(
        [
            "git", "-C", str(source),
            "status", "--porcelain",
            "--untracked-files=all",
        ],
        text=True,
    ).strip()

    if status:
        raise ValueError(
            "Integration source repository must be clean"
        )


class ReproducibilityIntegrationTests(unittest.TestCase):

    def test_real_consultation_packages(self):
        with tempfile.TemporaryDirectory(
            prefix="xientia-f44-r1-integration-"
        ) as temporary:
            root = Path(temporary)
            repo = root / "reference"

            source = EDITORIAL.parents[1]

            require_clean_source(source)

            expected_commit = subprocess.check_output(
                ["git", "-C", str(source), "rev-parse", "HEAD"],
                text=True,
            ).strip()

            subprocess.run(
                [
                    "git", "clone", "--no-hardlinks",
                    "--quiet", str(source), str(repo),
                ],
                check=True,
            )

            commit = subprocess.check_output(
                ["git", "-C", str(repo), "rev-parse", "HEAD"],
                text=True,
            ).strip()

            self.assertEqual(
                commit,
                expected_commit,
            )

            env = {
                **os.environ,
                "PYTHONDONTWRITEBYTECODE": "1",
            }
            env.pop("PYTHONPATH", None)

            for volume in ("XV-001", "XEP-0000"):
                packages = []

                for run in (1, 2):
                    output = root / f"{volume}-{run}"

                    subprocess.run(
                        [
                            sys.executable,
                            str(
                                repo
                                / "tools/editorial/render_library.py"
                            ),
                            "--repo", str(repo),
                            "--volume", volume,
                            "--out", str(output),
                            "--validate-publish",
                            "--publish-with-evidence",
                        ],
                        check=True,
                        env=env,
                        stdout=subprocess.DEVNULL,
                    )

                    packages.append(output)

                result = compare_packages(
                    repo, packages[0], packages[1]
                )

                with self.subTest(volume=volume):
                    self.assertEqual(
                        result["packages_verified"], 2
                    )
                    self.assertTrue(
                        result["levels"]["L1"]["passed"]
                    )
                    self.assertTrue(
                        result["levels"]["L2"]["passed"]
                    )
                    self.assertTrue(
                        result["levels"]["L3"]["passed"]
                    )
                    binary = result["levels"]["L4"]

                    self.assertEqual(
                        binary["passed"],
                        all(
                            item["sha256_a"] == item["sha256_b"]
                            for item in binary["artifacts"].values()
                        ),
                    )

            status = subprocess.check_output(
                [
                    "git", "-C", str(repo),
                    "status", "--porcelain",
                ],
                text=True,
            ).strip()

            self.assertFalse(status)


    def test_dirty_source_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / "repo"

            subprocess.run(
                ["git", "init", "-q", str(repo)],
                check=True,
            )

            (repo / "untracked.txt").write_text(
                "dirty", encoding="utf-8"
            )

            with self.assertRaisesRegex(
                ValueError,
                "Integration source repository must be clean",
            ):
                require_clean_source(repo)


if __name__ == "__main__":
    unittest.main()
