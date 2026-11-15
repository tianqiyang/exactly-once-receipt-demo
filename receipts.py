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

    def insert_if_absent(self, run_id, state):
        """Atomic compare-and-set: check and write under one lock.
        (In Postgres: UNIQUE (run_id) + INSERT ... ON CONFLICT DO NOTHING.)"""
        with self._lock:
            if any(r[0] == run_id for r in self.rows):
                return False
            self.rows.append((run_id, state))
            return True


class Run:
    def __init__(self, run_id, store, before_write=None):
        self.run_id = run_id
        self.store = store
        # Test seam: called after the "no receipt yet" check, before the write.
        self.before_write = before_write or (lambda who: None)

    def finish(self, state, who):
        """Called by the stage thread ("done") and by the watchdog ("timeout")."""
        self.before_write(who)
        # Check and write are one atomic step, so only the winner writes.
        return self.store.insert_if_absent(self.run_id, state)
