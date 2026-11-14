"""Numbers quoted in the text about max-T improvement tests."""
import json
for m in ("0.5B", "1.5B"):
    d = json.load(open(f"results/dec_{m}.json"))
    fc = [r["maxt_false_claim_rate"] for r in d["claims"]]
    pw = [r["maxt_claim_given_better"] for r in d["claims"] if r["maxt_claim_given_better"] is not None]
    nf = [r["naive_false_claim_rate"] for r in d["claims"] if r["n"] == 200 and r["K"] >= 15]
    sf = [r["split_false_claim_rate"] for r in d["claims"] if r["n"] == 200 and r["K"] >= 15]
    spw = [r["split_claim_given_better"] for r in d["claims"] if r["split_claim_given_better"] is not None]
    npw = [r["naive_claim_given_better"] for r in d["claims"] if r["naive_claim_given_better"] is not None]
    print(m, "maxT false claim range %.3f-%.3f" % (min(fc), max(fc)), "maxT power range %.3f-%.3f" % (min(pw), max(pw)),
          "| naive false (n=200,K>=15):", [round(x, 3) for x in nf], "split false:", [round(x, 3) for x in sf],
          "| split power %.3f-%.3f naive power %.3f-%.3f" % (min(spw), max(spw), min(npw), max(npw)))
