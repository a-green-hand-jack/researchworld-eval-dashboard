p = "paper/main.tex"
s = open(p).read()
a = r"In the logistic-normal model the Aitchison score is near-pivotal (Prop.~\ref{prop:pivot}b): gap"
b = r"In the logistic-normal model the Aitchison score is near-pivotal (Prop.~\ref{prop:pivot}b is exact for the oracle centre $f=\mathrm{softmax}(\eta)$; here $f$ is the fitted regression): gap"
print(a in s)
s = s.replace(a, b)
open(p, "w").write(s)
