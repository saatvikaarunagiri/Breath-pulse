"""Knowledge base for the in-app assistant (Breath & Pulse Cam)."""

FAQ = [
    (["start", "begin", "how", "use", "work", "works"],
     "Sit still, face the camera, and keep good even light on your face. Wait a "
     "few seconds for the buffer bar to fill, then your HR and RR appear."),
    (["heart", "hr", "pulse", "bpm", "rate"],
     "Heart rate comes from tiny colour changes in your skin as blood pulses "
     "(rPPG). Hold still and well-lit for the steadiest reading."),
    (["breath", "breathing", "respiration", "rr"],
     "Respiration comes from the gentle rise and fall of your chest below your "
     "face. Keep your upper chest in frame."),
    (["weak", "wrong", "accurate", "accuracy", "off", "confidence"],
     "The reading shows 'ok' or 'weak'. Weak usually means low light, motion, or "
     "flickering bulbs. Face a window or lamp and stay still."),
    (["save", "log", "csv", "export"],
     "Click 'Save readings' to write a CSV of your HR/RR over time into this "
     "session's folder."),
    (["light", "lighting", "dark", "flicker"],
     "Use steady, even light (daylight or a lamp). Avoid flickering overhead "
     "LEDs — they add noise at their own frequency."),
    (["data", "privacy", "stored", "store", "upload", "private", "record"],
     "Everything runs on your computer and nothing is uploaded or recorded as "
     "video. At the end you choose what, if anything, to keep."),
    (["identity", "profile", "baseline", "remember"],
     "If you save your identity, only a small baseline (your typical resting HR "
     "this session) is kept locally to compare next time."),
    (["medical", "doctor", "diagnos", "safe", "real"],
     "This is NOT a medical device — it's a learning demo. Don't use it for any "
     "health decision. See a professional for anything real."),
    (["quit", "exit", "close", "end", "stop"],
     "Click 'End session' (or close the window). You'll choose what to keep "
     "before anything is saved."),
]
