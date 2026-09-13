from src.evaluation.policy import Verdict, decide

cases = [
    ("unfaithful, first try",  Verdict(8.0, 5, False, True), 0, 0, None,  "refine"),
    ("unfaithful, budget out", Verdict(8.0, 5, False, True), 1, 2, None,  "invalid"),
    ("repair damaged it",      Verdict(6.0, 5, False, False), 1, 1, 9.0,  "invalid"),
    ("clean pass",             Verdict(8.0, 9, True, True),   0, 0, None, "ready"),
    ("craft low, first try",   Verdict(6.0, 9, True, False),  0, 0, None, "refine"),
    ("stagnant",               Verdict(6.0, 9, True, False),  1, 0, 6.5,  "ready"),
]

for name, v, it, rep, prev, expected in cases:
    got = decide(v, it, rep, prev)
    print(f"{'ok ' if got and got.outcome == expected else 'FAIL'} {name}: {got.outcome if got else None}")