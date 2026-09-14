"""mail_sync_and_classify: every 15 min. Syncs every enabled IMAP account (INBOX, UID incremental,
7 day backfill on first run) and classifies new mail (Claude via D's classify_emails, rule fallback)."""
from ._runner import run_job


def run(app) -> str:
    def work():
        from ..modules.mail import service
        from ..services import mail_classify

        results = service.sync_all()
        parts = []
        for r in results:
            if r["error"]:
                parts.append(f"{r['label']}: ERROR {r['error'][:120]}")
            else:
                parts.append(f"{r['label']}: +{r['inserted']}/{r['fetched']}")
        classified = mail_classify.classify_pending()
        parts.append(f"classified {classified['classified']} ({classified['by']})")
        errors = sum(1 for r in results if r["error"])
        if errors == len(results) and results:
            raise RuntimeError("all accounts failed: " + "; ".join(parts))
        return "; ".join(parts) if parts else "no enabled accounts"

    return run_job(app, "mail_sync_and_classify", work)
