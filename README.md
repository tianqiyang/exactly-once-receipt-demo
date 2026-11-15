# exactly-once receipt: failing test first, then the fix

A stage thread and its watchdog can both try to settle the same run near the
deadline. The old `Run.finish()` does check-then-act ("no receipt yet?" → write),
so both callers can pass the check and both write a receipt.

- Commit 1 adds the code and a deterministic race test. The test fails: two receipts.
- Commit 2 makes settling one atomic compare-and-set, so only the winner writes. The test passes.

The test uses a `before_write` seam and two `threading.Event`s to force the bad
interleaving every run, with no `sleep()`.

Run: `python3 -m unittest -v`
