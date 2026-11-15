"""A stage runs with a watchdog. Whoever finishes first (the stage or the
watchdog timeout) must write exactly one receipt for the run."""
import threading


class ReceiptStore:
    def __init__(self):
        self.rows = []
        self._lock = threading.Lock()

    def has_receipt(self, run_id):
        with self._lock:
            return any(r[0] == run_id for r in self.rows)

    def insert(self, run_id, state):
        with self._lock:
            self.rows.append((run_id, state))


class Run:
    def __init__(self, run_id, store, before_write=None):
        self.run_id = run_id
        self.store = store
        # Test seam: called after the "no receipt yet" check, before the write.
        self.before_write = before_write or (lambda who: None)

    def finish(self, state, who):
        """Called by the stage thread ("done") and by the watchdog ("timeout")."""
        if self.store.has_receipt(self.run_id):
            return False
        self.before_write(who)
        self.store.insert(self.run_id, state)
        return True
