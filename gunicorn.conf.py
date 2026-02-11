"""Gunicorn configuration for the Wealthtender Dashboard.

This file is auto-discovered by gunicorn when present in the working directory.
It handles post-fork warm-up so the API health check runs inside each worker
process (not the master, where threads don't survive fork).
"""

import threading


def post_fork(server, worker):
    """Called in each worker process after Gunicorn forks it.

    We start the API warm-up thread here so it actually runs inside the
    worker.  Module-level threads started during import (in the master
    process) do NOT survive fork -- this was the root cause of the
    dashboard failing to connect to the API after a Render cold start.
    """
    import dashboard.services.api as api_mod
    # Reset the flag inherited from the master process so the worker
    # actually runs its own warm-up.
    api_mod._warm_started = False
    threading.Thread(target=api_mod.warm_api, daemon=True).start()
    server.log.info("Worker %s: warm-up thread started", worker.pid)
