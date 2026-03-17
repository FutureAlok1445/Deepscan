import asyncio
import os
from pathlib import Path
from typing import List, Tuple

from backend.services.IMageDetector.orchestrator import image_orchestrator


TEST_DIR = Path("test_images")
REPORT_PATH = Path("accuracy_report.md")


class MockFile:
    """Minimal async file wrapper to mimic FastAPI's UploadFile.read()."""

    def __init__(self, path: Path):
        self.path = path

    async def read(self) -> bytes:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._read_sync)

    def _read_sync(self) -> bytes:
        with self.path.open("rb") as f:
            return f.read()


def discover_images() -> List[Tuple[str, str, Path]]:
    """
    Discover test images in TEST_DIR.
    Filenames should start with 'real_' or 'fake_'.
    Returns list of tuples: (filename, expected_label, path)
    """
    if not TEST_DIR.exists():
        TEST_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Test folder: {TEST_DIR.resolve()}")
    print(
        "Add images named like 'real_1.jpg', 'real_2.png', 'fake_1.jpg', 'fake_2.png', etc. "
        "Then run this script again."
    )

    items: List[Tuple[str, str, Path]] = []
    for path in TEST_DIR.iterdir():
        if not path.is_file():
            continue
        name = path.name.lower()
        if name.startswith("real_"):
            items.append((path.name, "Real", path))
        elif name.startswith("fake_"):
            items.append((path.name, "Fake", path))
    return sorted(items, key=lambda x: x[0])


def format_markdown_table(rows: List[Tuple[str, str, float, str, bool]]) -> str:
    lines = [
        "| Image | Expected | Score | Verdict | Correct |",
        "|-------|----------|-------|---------|---------|",
    ]
    for filename, expected, score, verdict, correct in rows:
        score_str = f"{score:.1f}"
        correct_str = "YES" if correct else "NO"
        lines.append(f"| {filename} | {expected} | {score_str} | {verdict} | {correct_str} |")
    return "\n".join(lines)


async def run_accuracy_test():
    images = discover_images()
    if not images:
        print("No test images found in 'test_images/'. Populate the folder and rerun.")
        return

    # Ensure models are loaded
    await image_orchestrator.load_models()

    rows: List[Tuple[str, str, float, str, bool]] = []
    correct_count = 0

    for filename, expected_label, path in images:
        print(f"Analyzing {filename} (expected: {expected_label}) ...")
        mock = MockFile(path)
        # context_caption is optional; pass None for bulk tests
        result = await image_orchestrator.process_image(mock, context_caption=None)

        score = float(result.get("score", 0.0))
        verdict = str(result.get("verdict", "")).upper()

        # Map verdict to simple REAL/FAKE expectation
        is_real = "REAL" in verdict and "FAKE" not in verdict
        predicted_label = "Real" if is_real else "Fake"
        correct = predicted_label.lower() == expected_label.lower()
        if correct:
            correct_count += 1

        rows.append((filename, expected_label, score, verdict, correct))

    table_md = format_markdown_table(rows)
    REPORT_PATH.write_text(table_md, encoding="utf-8")

    total = len(rows)
    accuracy_pct = (correct_count / total) * 100 if total else 0.0

    print()
    print(table_md)
    print()
    print(f"Final accuracy: {correct_count}/{total} correct ({accuracy_pct:.1f}%)")
    print(f"Report saved to: {REPORT_PATH.resolve()}")


if __name__ == "__main__":
    asyncio.run(run_accuracy_test())

