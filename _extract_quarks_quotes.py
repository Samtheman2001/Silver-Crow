# One-off: inspect quarks quote extraction (delete after use)
import re
from pathlib import Path

p = Path(__file__).resolve().parent.parent / "quarks.txt"
text = p.read_text(encoding="utf-8")
pat = re.compile(r"\u201c([^\u201d]+)\u201d")
lines = pat.findall(text)
for needle in ("Um", "hell nah", "How dare", "If by"):
    for L in lines:
        if needle.lower() in L.lower():
            print(needle, "=>", repr(L))
            break
