import threading
import unittest

from receipts import ReceiptStore, Run


class ExactlyOnceReceiptTest(unittest.TestCase):
    def test_stage_and_watchdog_race_writes_one_receipt(self):
        """Force the bad interleaving: both callers pass the 'no receipt yet'
        check before either one writes. No sleep(); Events order the threads."""
        store = ReceiptStore()
        stage_at_write = threading.Event()
        watchdog_at_write = threading.Event()

        def before_write(who):
            if who == "stage":
                stage_at_write.set()
                watchdog_at_write.wait(timeout=1)
            else:
                watchdog_at_write.set()
                stage_at_write.wait(timeout=1)

        run = Run("run-1", store, before_write=before_write)
        results = {}
        t1 = threading.Thread(target=lambda: results.update(stage=run.finish("done", "stage")))
        t2 = threading.Thread(target=lambda: results.update(watchdog=run.finish("timeout", "watchdog")))
        t1.start(); t2.start(); t1.join(2); t2.join(2)

        receipts = [r for r in store.rows if r[0] == "run-1"]
        self.assertEqual(len(receipts), 1, f"expected exactly one receipt, got {receipts}")
        self.assertEqual(sorted(results.values()), [False, True])


if __name__ == "__main__":
    unittest.main()
