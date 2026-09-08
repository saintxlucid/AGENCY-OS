"""ASTRA OS — Proving slice tests (blocks enforced, happy path receipts)."""
from demos.proving_slice import main


def test_proving_slice_happy_path_with_blocks():
    result = main()
    assert result["brief"].startswith("ag_brief_")
    assert result["receipt"].startswith("ag_rcpt_")
    assert result["blockers"] >= 1  # version-drift block recorded
    assert result["observations"] >= 1
