"""
Local-only storage for consent, identity (profile), and session data.

Everything lives under a per-app folder in the user's home directory. Nothing
is ever uploaded anywhere. The end-of-session choices map to explicit
save/delete actions here, so "delete" really deletes.

Layout:
    ~/.<app_id>/
        consent.json        # remembered consent (only if "always")
        profile.json        # identity: calibration / personalization
        sessions/           # saved session artifacts (STL, logs, ...)
"""

import json
import os
import shutil
import time

# End-of-session privacy choices (returned by the SessionEndDialog).
SAVE_SESSION_ONLY   = "session_only"      # keep this session, drop identity
SAVE_IDENTITY_ONLY  = "identity_only"     # keep identity, drop this session
SAVE_BOTH           = "both"              # keep identity + this session
DELETE_ALL          = "delete_all"        # wipe identity + this session


class Store:
    def __init__(self, app_id):
        self.app_id = app_id
        self.root = os.path.join(os.path.expanduser("~"), "." + app_id)
        self.sessions_dir = os.path.join(self.root, "sessions")
        os.makedirs(self.sessions_dir, exist_ok=True)

    # ---- paths ----
    @property
    def consent_path(self):
        return os.path.join(self.root, "consent.json")

    @property
    def profile_path(self):
        return os.path.join(self.root, "profile.json")

    def new_session_dir(self):
        name = time.strftime("session_%Y%m%d_%H%M%S")
        path = os.path.join(self.sessions_dir, name)
        os.makedirs(path, exist_ok=True)
        return path

    # ---- consent ----
    def load_consent(self):
        if os.path.exists(self.consent_path):
            try:
                with open(self.consent_path) as f:
                    return json.load(f)
            except (OSError, json.JSONDecodeError):
                return None
        return None

    def save_consent(self, record):
        with open(self.consent_path, "w") as f:
            json.dump(record, f, indent=2)

    def clear_consent(self):
        _safe_remove(self.consent_path)

    # ---- identity / profile ----
    def load_profile(self):
        if os.path.exists(self.profile_path):
            try:
                with open(self.profile_path) as f:
                    return json.load(f)
            except (OSError, json.JSONDecodeError):
                return None
        return None

    def save_profile(self, profile):
        with open(self.profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    def delete_profile(self):
        _safe_remove(self.profile_path)

    # ---- apply an end-of-session choice ----
    def apply_choice(self, choice, profile=None, session_dir=None):
        """Carry out one of the four privacy choices. Returns a short summary
        string describing exactly what was kept and what was deleted."""
        kept, removed = [], []

        if choice in (SAVE_IDENTITY_ONLY, SAVE_BOTH):
            if profile is not None:
                self.save_profile(profile)
                kept.append("identity profile")
        else:
            if self.delete_profile() or profile is not None:
                removed.append("identity profile")

        if choice in (SAVE_SESSION_ONLY, SAVE_BOTH):
            if session_dir and os.path.isdir(session_dir):
                kept.append(f"session ({os.path.basename(session_dir)})")
        else:
            if session_dir and os.path.isdir(session_dir):
                shutil.rmtree(session_dir, ignore_errors=True)
                removed.append("this session's files")

        if choice == DELETE_ALL:
            # also forget remembered consent on a full wipe
            self.clear_consent()
            removed.append("remembered consent")

        parts = []
        if kept:
            parts.append("Kept: " + ", ".join(kept))
        if removed:
            parts.append("Deleted: " + ", ".join(removed))
        return "  •  ".join(parts) if parts else "Nothing was stored."


def _safe_remove(path):
    try:
        os.remove(path)
        return True
    except OSError:
        return False
