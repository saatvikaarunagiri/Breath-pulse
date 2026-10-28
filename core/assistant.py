"""
Offline, local help assistant.

It answers only from a fixed knowledge base about the app (passed in as `faq`),
does light friendly small talk, and refuses anything outside safe, on-topic use.
Because it has no generative model, it literally cannot be talked into producing
explicit, harmful, or off-limits content — it can only reply from its own list.

The content filter is a keyword/pattern guard. It is a reasonable guardrail, not
a perfect classifier: it can miss cleverly-worded input and can occasionally
be over-cautious. It is deliberately simple so its behavior is predictable.

Optional: set use_llm=True and run a local Ollama server to get smarter replies
for ON-TOPIC questions only (the filter still runs first). Off by default so the
app works with zero extra setup.
"""

import re

# --- content filter -------------------------------------------------------

_BLOCKED = {
    "sexual / explicit": [
        r"\bsex\b", r"\bsexual\b", r"\bnsfw\b", r"\bporn", r"\bnude", r"\bnaked\b",
        r"\berotic", r"\bfetish", r"\bgenital",
    ],
    "violence / harm to others": [
        r"\bkill\b", r"\bmurder", r"\bweapon", r"\bbomb\b", r"\bshoot", r"\bassault",
    ],
    "self-harm": [
        r"\bsuicide\b", r"\bself.?harm", r"\bkill myself\b", r"\bhurt myself\b",
    ],
    "hate / harassment": [
        r"\bslur\b", r"\bracist\b", r"\bhate speech\b",
    ],
    "illegal": [
        r"\bhack\b", r"\bmalware\b", r"\bmake drugs\b", r"\bbuy drugs\b",
        r"\bcredit card number\b", r"\bsteal\b",
    ],
    "personal data of others": [
        r"\bhome address of\b", r"\bphone number of\b", r"\btrack (a|this|that) person\b",
        r"\bfind someone'?s\b",
    ],
}

_SELF_HARM_REPLY = (
    "I'm just a little in-app helper and not able to help with that — but please "
    "don't go through it alone. If you're in the US you can call or text 988 to "
    "reach people who want to help, any time."
)

_REFUSAL = (
    "Sorry, I can only chat about this app and how to use it — I can't help with "
    "that one. Ask me how to draw, save, use your voice, or about your privacy "
    "options. 🤍"
)


def _matches(text, patterns):
    return any(re.search(p, text) for p in patterns)


def check_content(text):
    """Return (ok: bool, reply_if_blocked: str|None)."""
    t = text.lower()
    if _matches(t, _BLOCKED["self-harm"]):
        return False, _SELF_HARM_REPLY
    for cat, pats in _BLOCKED.items():
        if cat == "self-harm":
            continue
        if _matches(t, pats):
            return False, _REFUSAL
    return True, None


# --- FAQ matching ---------------------------------------------------------

_SMALL_TALK = {
    r"\b(hi|hello|hey|yo)\b": "Hi! 🤍 Ask me anything about using the app.",
    r"\bthank": "You're so welcome!",
    r"\b(bye|goodbye|see you)\b": "Bye! Have fun creating. 🤍",
    r"\bwho are you\b": "I'm the app's little offline helper. I answer questions "
                        "about how this app works — all on your computer.",
    r"\byour name\b": "You can just call me Buddy. I live inside this app.",
}

_FALLBACK = (
    "I'm not sure about that one — I only know this app. Try asking things like "
    "\"how do I save?\", \"what does the pinch do?\", or \"what happens to my data?\""
)


class Assistant:
    def __init__(self, faq, use_llm=False, llm_model="llama3.2"):
        """faq: list of (keywords:list[str], answer:str)."""
        self.faq = faq
        self.use_llm = use_llm
        self.llm_model = llm_model

    def reply(self, text):
        text = (text or "").strip()
        if not text:
            return ""

        ok, blocked_reply = check_content(text)
        if not ok:
            return blocked_reply

        t = text.lower()

        # small talk first
        for pat, ans in _SMALL_TALK.items():
            if re.search(pat, t):
                return ans

        # score FAQ entries by whole-word keyword hits (so "draw" does not
        # match "drawing" and steal a more specific answer)
        best, best_score = None, 0
        for keywords, answer in self.faq:
            score = sum(1 for k in keywords
                        if re.search(r"\b" + re.escape(k) + r"\b", t))
            if score > best_score:
                best, best_score = answer, score
        if best_score > 0:
            return best

        # optional local LLM for on-topic-but-unmatched questions
        if self.use_llm:
            llm = self._ask_llm(text)
            if llm:
                return llm

        return _FALLBACK

    def _ask_llm(self, text):
        """Best-effort call to a local Ollama server. Returns None on any
        problem so the app never breaks if Ollama isn't running."""
        try:
            import json
            import urllib.request
            prompt = ("You are a friendly help bot embedded in a local computer-"
                      "vision app. Answer briefly and ONLY about using the app. "
                      "If asked anything off-topic or unsafe, politely decline.\n\n"
                      f"User: {text}\nAssistant:")
            req = urllib.request.Request(
                "http://localhost:11434/api/generate",
                data=json.dumps({"model": self.llm_model, "prompt": prompt,
                                 "stream": False}).encode(),
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=20) as r:
                out = json.loads(r.read()).get("response", "").strip()
            # run the filter on the model's output too
            ok, _ = check_content(out)
            return out if ok else None
        except Exception:
            return None
