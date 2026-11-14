# Literature consultation and safety log

Only exact, explicitly permitted starter titles or older statistical/methodological works were retrieved. No broad benchmark-prediction discovery, citation expansion, prohibited-paper identification, or prohibited content was used. Original abstracts and the excerpts below were consulted; no claim of full-text reading is made for abstract-only sources.

Rejected records: a supplied DOI proposed for the spectral-regularization article resolved to an unrelated biomedical article; it was discarded and replaced by the verified JMLR original. An arXiv lookup for a quantile-forecasting article resolved instead to Making and Evaluating Point Forecasts; the distinct, verified article is cited under its own title. An unrelated mechanical-device abstract attached to the EM article was discarded in favor of the publisher abstract. Blocked/redirect-only publisher responses were not treated as reading. Unread metadata-only references were removed. No prohibited content was encountered.

## Candes2009Completion

**Exact Matrix Completion via Convex Optimization**

Source: https://api.openalex.org/works/https://doi.org/10.1007/s10208-009-9045-5

Consulted scope: original/retrieved abstract.

We consider a problem of considerable practical interest: the recovery of a data matrix from a sampling of its entries. Suppose that we observe m entries selected uniformly at random from a matrix M. Can we complete the matrix and recover the entries that we have not seen? We show that one can perfectly recover most low-rank matrices from what appears to be an incomplete set of entries. We prove that if the number m of sampled entries obeys $$m\ge C\,n^{1.2}r\log n$$ for some positive numerical constant C, then with very high probability, most n×n matrices of rank r can be perfectly recovered by solving a simple convex optimization program. This program finds the matrix with minimum nuclear norm that fits the data. The condition above assumes that the rank is not too large. However, if one replaces the 1.2 exponent with 1.25, then the result holds for all values of the rank. Similar results hold for arbitrary rectangular matrices as well. Our results are connected with the recent literature on compressed sensing, and show that objects other than signals and images can be perfectly reconstructed from very limited information.

## Candes2010Noisy

**Matrix Completion With Noise**

Source: https://api.openalex.org/works/https://doi.org/10.1109/JPROC.2009.2035722

Consulted scope: original/retrieved abstract.

On the heels of compressed sensing, a new field has very recently emerged. This field addresses a broad range of problems of significant practical interest, namely, the recovery of a data matrix from what appears to be incomplete, and perhaps even corrupted, information. In its simplest form, the problem is to recover a matrix from a small sample of its entries. It comes up in many areas of science and engineering, including collaborative filtering, machine learning, control, remote sensing, and computer vision, to name a few. This paper surveys the novel literature on matrix completion, which shows that under some suitable conditions, one can recover an unknown low-rank matrix from a nearly minimal set of entries by solving a simple convex optimization problem, namely, nuclear-norm minimization subject to data constraints. Further, this paper introduces novel results showing that matrix completion is provably accurate even when the few observed entries are corrupted with a small amount of noise. A typical result is that one can recover an unknown n x n matrix of low rank r from just about nr log^2 n noisy samples with an error that is proportional to the noise level. We present numerical results that complement our quantitative analysis and show that, in practice, nuclear-norm minimization accurately fills in the many missing entries of large low-rank matrices from just a few noisy samples. Some analogies between matrix completion and compressed sensing are discussed throughout.

## Chaloner1995Design

**Bayesian Experimental Design: A Review**

Source: https://projecteuclid.org/journals/statistical-science/volume-10/issue-3/Bayesian-Experimental-Design-A-Review/10.1214/ss/1177009939.full

Consulted scope: original/retrieved abstract.

This paper reviews the literature on Bayesian experimental design. A unified view of this topic is presented, based on a decision-theoretic approach. This framework casts criteria from the Bayesian literature of design as part of a single coherent approach. The decision-theoretic structure incorporates both linear and nonlinear design problems and it suggests possible new directions to the experimental design problem, motivated by the use of new utility functions. We show that, in some special cases of linear design problems, Bayesian solutions change in a sensible way when the prior distribution and the utility function are modified to allow for the specific structure of the experiment. The decision-theoretic approach also gives a mathematical justification for selecting the appropriate optimality criterion.

## Cohn1996Active

**Active Learning with Statistical Models**

Source: https://api.semanticscholar.org/graph/v1/paper/DOI%3A10.1613%2Fjair.295?fields=title,authors,year,venue,abstract,externalIds,citationStyles,url,openAccessPdf

Consulted scope: original/retrieved abstract.

For many types of machine learning algorithms, one can    compute the statistically `optimal' way to select training data.  In    this paper, we review how optimal data selection techniques have been    used with feedforward neural networks.  We then show how the same    principles may be used to select data for two alternative,    statistically-based learning architectures: mixtures of Gaussians and    locally weighted regression.  While the techniques for neural networks    are computationally expensive and approximate, the techniques for    mixtures of Gaussians and locally weighted regression are both    efficient and accurate.  Empirically, we observe that the optimality    criterion sharply decreases the number of training examples the    learner needs in order to achieve good performance.

## Dempster1977EM

**Maximum Likelihood from Incomplete Data Via the
                    <i>EM</i>
                    Algorithm**

Source: https://api.semanticscholar.org/graph/v1/paper/DOI%3A10.1111%2Fj.2517-6161.1977.tb01600.x?fields=title,authors,year,venue,abstract,externalIds,citationStyles,url,openAccessPdf

Consulted scope: original/retrieved abstract.

Summary A broadly applicable algorithm for computing maximum likelihood estimates from incomplete data is presented at various levels of generality. Theory showing the monotone behaviour of the likelihood and convergence of the algorithm is derived. Many examples are sketched, including missing value situations, applications to grouped, censored or truncated data, finite mixture models, variance component estimation, hyperparameter estimation, iteratively reweighted least squares and factor analysis.

## Ghahramani1996Mixture

**The EM algorithm for mixtures of factor analyzers**

Source: https://www.cs.toronto.edu/~hinton/absps/tr-96-1.pdf

Consulted scope: original full-text excerpt or original abstract page.

The
EM
Algorithm
for
Mixtures
of
F
actor
Analyzers
Zoubin
Ghahramani
Georey
E.
Hin
ton
Departmen
t
of
Computer
Science
Univ
ersit
y
of
T
oron
to

King's
College
Road
T
oron
to,
Canada
MS
A
Email:
zoubin@cs.toron
to.edu
T
ec
hnical
Rep
ort
CR
G-TR-	-
Ma
y
,
		
(revised
F
eb
,
		)
Abstract
F
actor
analysis,
a
statistical
metho
d
for
mo
deling
the
co
v
ariance
structure
of
high
dimensional
data
using
a
small
n
um
b
er
of
laten
t
v
ariables,
can
b
e
extended
b
y
allo
wing
dieren
t
lo
cal
factor
mo
dels
in
dieren
t
regions
of
the
input
space.
This
results
in
a
mo
del
whic
h
concurren
tly
p
erforms
clustering
and
dimensionalit
y
reduction,
and
can
b
e
though
t
of
as
a
reduced
dimension
mixture
of
Gaussians.
W
e
presen
t
an
exact
Exp
ectation{Maximization
algorithm
for
tting
the
parameters
of
this
mixture
of
factor
analyzers.

In
tro
duction
Clustering
and
dimensionalit
y
reduction
ha
v
e
long
b
een
considered
t
w
o
of
the
fundamen
tal
problems
in
unsup
ervised
learning
(Duda
&
Hart,
	;
Chapter
).
In
clustering,
the
goal
is
to
group
data
p
oin
ts
b
y
similarit
y
b
et
w
een
their
features.
Con
v
ersely
,
in
dimensionalit
y
reduction,
the
goal
is
to
group
(or
compress)
features
that
are
highly
correlated.
In
this
pap
er
w
e
presen
t
an
EM
learning
algorithm
for
a
metho
d
whic
h
com
bines
one
of
the
basic
forms
of
dimensionalit
y
reduction|factor
analysis|with
a
basic
metho
d
for
clustering|the
Gaussian
mixture
mo
del.
What
results
is
a
statistical
metho
d
whic
h
concurren
tly
p
erforms
clustering
and,
within
eac
h
cluster,
lo
cal
dimensionalit
y
reduction.
Lo
cal
dimensionalit
y
reduction
presen
ts
sev
eral
b
enets
o
v
er
a
sc
heme
in
whic
h
clustering
and
dimensionalit
y
reduction
are
p
erformed
separately
.
First,
dieren
t
features
ma
y
b
e
correlated
within
dieren
t
clusters
and
th
us
the
metric
for
dimensionalit
y
reduction
ma
y
need
to
v
ary
b
et
w
een
dieren
t
clusters.
Con
v
ersely
,
the
metric
induced
in
dimensionalit
y
reduction
ma
y
guide
the
pro
cess
of
cluster
formation|i.e.
dieren
t
clusters
ma
y
app
ear
more
separated
dep
ending
on
the
lo
cal
metric.
Recen
tly
,
there
has
b
een
a
great
deal
of
researc
h
on
the
topic
of
lo
cal
dimensionalit
y
reduction,
resulting
in
sev
eral
v
arian
ts
on
the
basic
concept
with
successful
applications
to
c
haracter
and
face
recognition
(Bregler
and
Omoh
undro,
		;
Kam
bhatla
and
Leen,
		;
Sung
and
P
oggio,
		;
Sc
h
w
enk
and
Milgram,
		;
Hin
ton
et
al.,
		).
The
algorithm
used
b
y
these
authors
for
dimensionalit
y
reduction
is
principal
comp
onen
ts
analysis
(PCA).



z


x
	
?
-

Figure
:
The
factor
analysis
generativ
e
mo
del
(in
v
ector
form).
PCA,
unlik
e
maxim
um
lik
eliho
o
d
factor
analysis
(F
A),
do
es
not
dene
a
prop
er
densit
y
mo
del
for
the
data,
as
the
cost
of
co
ding
a
data
p
oin
t
is
equal
an
ywhere
along
the
principal
comp
onen
t
subspace
(i.e.
the
densit
y
is
un-normalized
along
these
directions).
F
urthermore,
PCA
is
not
robust
to
indep
enden
t
noise
in
the
features
of
the
data
(see
Hin
ton
et
al.,
		,
for
a
comparison
of
PCA
and
F
A
mo
dels)
.
Hin
ton,
Da
y
an,
and
Rev
o
w
(		),
also
exploring
an
application
to
digit
recognition,
w
ere
the
rst
to
extend
mixtures
of
principal
comp
onen
ts
analyzers
to
a
mixture
of
factor
analyzers.
Their
learning
algorithm
consisted
of
an
outer
lo
op
of
appro
ximate
EM
to
t
the
mixture
comp
onen
ts,
com
bined
with
an
inner
lo
op
of
gradien
t
descen
t
to
t
eac
h
individual
factor
mo
del.
In
this
note
w
e
presen
t
an
exact
EM
algorithm
for
mixtures
of
factor
analyzers
whic
h
ob
viates
the
need
for
an
outer
and
inner
lo
op.
This
simplies
the
implem
en
tati
on,
reduces
the
n
um
b
er
of
heuristic
parameters
(i.e.
learning
rates
or
steps
of
conjugate
gradien
t
descen
t),
and
can
p
oten
tially
result
in
sp
eed-ups.
In
the
next
section
w
e
presen
t
bac
kground
material
on
factor
analysis
and
the
EM
al-
gorithm.
This
is
follo
w
ed
b
y
the
deriv
ation
of
the
learning
algorithm
for
mixture
of
factor
analyzers
in
section
.
W
e
close
with
a
discussion
in
section
.

F
actor
Analysis
In
maxim
um
lik
eliho
o
d
factor
analysis
(F
A),
a
p-dimensional
real-v
alued
data
v
ector
x
is
mo
deled
using
a
k
-dimensional
v
ector
of
real-v
alued
factors,
z,
where
k
is
generally
m
uc
h
smaller
than
p
(Ev
eritt,
	).
The
generativ
e
mo
del
is
giv
en
b
y:
x
=
z
+
u;
()
where

is
kno
wn
as
the
factor
lo
ading
matrix
(see
Figure
).
The
factors
z
are
assumed
to
b
e
N
(0;
I
)
distributed
(zero-mean
indep
enden
t
normals,
with
unit
v
ariance).
The
p-
dimensional
random
v
ariable
u
is
distributed
N
(0;
	),
where
	
is
a
diagonal
matrix.
The
diagonalit
y
of
	
is
one
of
the
k
ey
assumptions
of
factor
analysis:
The
observ
ed
v
ariables
are
indep
enden
t
giv
en
the
factors.
According
to
this
mo
del,
x
is
therefore
distributed
with
zero
mean
and
co
v
ariance

0
+
	;
and
the
goal
of
factor
analysis
is
to
nd
the

and
	
that
b
est
mo
del
the
co
v
ariance
structure
of
x.
The
factor
v
ariables
z
mo
del
correlations
b
et
w
een
the
elemen
ts
of
x,
while
the
u
v
ariables
accoun
t
for
indep
enden
t
noise
in
eac
h
elemen
t
of
x.
The
k
factors
pla
y
the
same
role
as
the
principal
comp
onen
ts
in
PCA:
They
are
infor-
mativ
e
pro
jections
of
the
data.
Giv
en

and
	,
the
exp
ected
v
alue
of
the
factors
can
b
e

computed
through
the
linear
pro
jection:
E
(zjx)
=

x;
()
where



0
(	
+

0
)
 
,
a
fact
that
results
from
the
join
t
normalit
y
of
data
and
factors:
P
 
"
x
z
#!
=
N
 "
0
0
#
;
"

0
+
	


0
I
#!
:
()
Note
that
since
	
is
diagonal,
the
p

p
matrix
(	
+

0
),
can
b
e
ecien
tly
in
v
erted
using
the
matrix
in
v
ersion
lemma:
(	
+

0
)
 
=
	
 
 	
 
(I
+

0
	
 
)
 

0
	
 
;
where
I
is
the
k

k
iden
tit
y
matrix.
F
urthermore,
it
is
p
ossible
(and
in
fact
necessary
for
EM)
to
compute
the
second
momen
t
of
the
factors,
E
(zz
0
jx)
=
V
ar(zjx)
+
E
(zjx)E
(zjx)
0
=
I
 

+

xx
0

0
;
()
whic
h
pro
vides
a
measure
of
uncertain
t
y
in
the
factors,
a
qua

## Gneiting2011Forecasts

**Making and Evaluating Point Forecasts**

Source: https://arxiv.org/abs/0912.0902

Consulted scope: original/retrieved abstract.

Abstract: Typically, point forecasting methods are compared and assessed by means of an error measure or scoring function, such as the absolute error or the squared error. The individual scores are then averaged over forecast cases, to result in a summary measure of the predictive performance, such as the mean absolute error or the (root) mean squared error. I demonstrate that this common practice can lead to grossly misguided inferences, unless the scoring function and the forecasting task are carefully matched. Effective point forecasting requires that the scoring function be specified ex ante, or that the forecaster receives a directive in the form of a statistical functional, such as the mean or a quantile of the predictive distribution. If the scoring function is specified ex ante, the forecaster can issue the optimal point forecast, namely, the Bayes rule. If the forecaster receives a directive in the form of a functional, it is critical that the scoring function be consistent for it, in the sense that the expected score is minimized when following the directive. A functional is elicitable if there exists a scoring function that is strictly consistent for it. Expectations, ratios of expectations and quantiles are elicitable. For example, a scoring function is consistent for the mean functional if and only if it is a Bregman function. It is consistent for a quantile if and only if it is generalized piecewise linear. Similar characterizations apply to ratios of expectations and to expectiles. Weighted scoring functions are consistent for functionals that adapt to the weighting in peculiar ways. Not all functionals are elicitable; for instance, conditional value-at-risk is not, despite its popularity in quantitative finance.

## Hendrycks2021MMLU

**Measuring Massive Multitask Language Understanding**

Source: https://arxiv.org/abs/2009.03300

Consulted scope: original/retrieved abstract.

Abstract: We propose a new test to measure a text model's multitask accuracy. The test covers 57 tasks including elementary mathematics, US history, computer science, law, and more. To attain high accuracy on this test, models must possess extensive world knowledge and problem solving ability. We find that while most recent models have near random-chance accuracy, the very largest GPT-3 model improves over random chance by almost 20 percentage points on average. However, on every one of the 57 tasks, the best models still need substantial improvements before they can reach expert-level accuracy. Models also have lopsided performance and frequently do not know when they are wrong. Worse, they still have near-random accuracy on some socially important subjects such as morality and law. By comprehensively evaluating the breadth and depth of a model's academic and professional understanding, our test can be used to analyze models across many tasks and to identify important shortcomings.

## Keshavan2010Completion

**Matrix Completion From a Few Entries**

Source: https://arxiv.org/abs/0901.3150

Consulted scope: original full-text excerpt or original abstract page.

[0901.3150] Matrix Completion from a Few Entries
Abstract: Let M be a random (alpha n) x n matrix of rank r<<n, and assume that a uniformly random subset E of its entries is observed. We describe an efficient algorithm that reconstructs M from |E| = O(rn) observed entries with relative root mean square error RMSE <= C(rn/|E|)^0.5 . Further, if r=O(1), M can be reconstructed exactly from |E| = O(n log(n)) entries. These results apply beyond random matrices to general low-rank incoherent matrices. This settles (in the case of bounded rank) a question left open by Candes and Recht and improves over the guarantees for their reconstruction algorithm. The complexity of our algorithm is O(|E|r log(n)), which opens the way to its use for massive data sets. In the process of proving these statements, we obtain a generalization of a celebrated result by Friedman-Kahn-Szemeredi and Feige-Ofek on the spectrum of sparse random matrices.

## Kipnis2024Meta

**metabench -- A Sparse Benchmark of Reasoning and Knowledge in Large Language Models**

Source: https://api.semanticscholar.org/graph/v1/paper/ARXIV%3A2407.12844?fields=title,authors,year,venue,abstract,externalIds,citationStyles,url,openAccessPdf

Consulted scope: original/retrieved abstract.

Large Language Models (LLMs) vary in their abilities on a range of tasks. Initiatives such as the Open LLM Leaderboard aim to quantify these differences with several large benchmarks (sets of test items to which an LLM can respond either correctly or incorrectly). However, high correlations within and between benchmark scores suggest that (1) there exists a small set of common underlying abilities that these benchmarks measure, and (2) items tap into redundant information and the benchmarks may thus be considerably compressed. We use data from n>5000 LLMs to identify the most informative items of six benchmarks, ARC, GSM8K, HellaSwag, MMLU, TruthfulQA and WinoGrande (with d = 28,632 items in total). From them we distill a sparse benchmark, metabench, that has less than 3% of the original size of all six benchmarks combined. This new sparse benchmark goes beyond point scores by yielding estimators of the underlying benchmark-specific abilities. We show that these estimators (1) can be used to reconstruct each original individual benchmark score with, on average, 1.24% root mean square error (RMSE), (2) reconstruct the original total score with 0.58% RMSE, and (3) have a single underlying common factor whose Spearman correlation with the total score is r = 0.94.

## Koenker2001Quantiles

**Quantile Regression**

Source: https://api.crossref.org/works/10.1257/jep.15.4.143

Consulted scope: original/retrieved abstract.

Quantile regression, as introduced by Koenker and Bassett (1978), may be viewed as an extension of classical least squares estimation of conditional mean models to the estimation of an ensemble of models for several conditional quantile functions. The central special case is the median regression estimator which minimizes a sum of absolute errors. Other conditional quantile functions are estimated by minimizing an asymmetrically weighted sum of absolute errors. Quantile regression methods are illustrated with applications to models for CEO pay, food expenditure, and infant birthweight.

## Koren2009Factors

**Matrix Factorization Techniques for Recommender Systems**

Source: https://www.cs.columbia.edu/~blei/fogm/2020F/readings/KorenBellVolinsky2009.pdf

Consulted scope: original full-text excerpt or original abstract page.

    COVER FEATURE
          MATRIX
           FACTORIZATION
          TECHNIQUES FOR
         RECOMMENDER
         SYSTEMS

     Yehuda Koren, Yahoo Research
     Robert Bell and Chris Volinsky, AT&T Labs—Research


   As the Netflix Prize competition has dem-
    onstrated,  matrix  factorization  models       Such systems are particularly useful for entertainment
    are superior to classic nearest-neighbor     products such as movies, music, and TV shows. Many cus-
                                                          tomers will view the same movie, and each customer is    techniques for producing product recom-
                                                                            likely to view numerous different movies. Customers have
    mendations, allowing the  incorporation                                                          proven willing to indicate their level of satisfaction with
    of additional information such as implicit                                                                    particular movies, so a huge volume of data is available
    feedback, temporal effects, and confidence     about which movies appeal to which customers. Com-
    levels.                                                panies can analyze this data to recommend movies to
                                                                     particular customers.

                odern consumers are inundated with   Recommender system strategies
                    choices. Electronic retailers and content        Broadly speaking, recommender systems are based
                   providers offer a huge selection of prod-     on one of two strategies. The content filtering approach
                     ucts, with unprecedented opportunities      creates a profile for each user or product to characterize
                    to meet a variety of special needs and        its nature. For example, a movie profile could include at-      tastes.MMatching consumers with the most appropriate      tributes regarding its genre, the participating actors, its
     products is key to enhancing user satisfaction and loy-     box office popularity, and so forth. User profiles might
      alty. Therefore, more retailers have become interested in      include demographic information or answers provided
    recommender systems, which analyze patterns of user     on a suitable questionnaire. The profiles allow programs
      interest in products to provide personalized recommenda-      to associate users with matching products. Of course,
     tions that suit a user’s taste. Because good personalized      content-based strategies require gathering external infor-
    recommendations can add another dimension to the user     mation that might not be available or easy to collect.
     experience, e-commerce leaders like Amazon.com and      A known successful realization of content filtering is
     Netflix have made recommender systems a salient part      the Music Genome Project, which is used for the Internet
     of their websites.                                             radio service Pandora.com. A trained music analyst scores

42    computer                                            Published by the IEEE Computer Society                      0018-9162/09/$26.00 © 2009 IEEEeach song in the Music Genome Project                                                                                       #3
based on hundreds of distinct musical
characteristics. These attributes, or genes,
capture not only a song’s musical identity
but also many significant qualities that are
                                                                                                                                      #2relevant to understanding listeners’ musi-
cal preferences.
  An alternative to content filtering relies
only on past user behavior—for example,
previous transactions or product ratings—
without requiring the creation of explicit                                                                                        #1
profiles. This approach is known as col-
laborative filtering, a term coined by the         Joe
developers of Tapestry, the first recom-
mender system.1 Collaborative filtering
analyzes relationships between users and                                                                                        #4
interdependencies among products to
identify new user-item associations.
  A major appeal of collaborative fil-
tering is that it is domain free, yet it can
address data aspects that are often elusive      Figure 1. The user-oriented neighborhood method. Joe likes the three
and difficult to profile using content filter-     movies on the left. To make a prediction for him, the system finds similar
                                               users who also liked those movies, and then determines which other moviesing. While generally more accurate than
                                             they liked. In this case, all three liked Saving Private Ryan, so that is the firstcontent-based techniques, collaborative
                                          recommendation. Two of them liked Dune, so that is next, and so on.
filtering suffers from what is called the cold
start problem, due to its inability to ad-
dress the system’s new products and users. In this aspect,     well-defined dimensions such as depth of character de-
content filtering is superior.                              velopment or quirkiness; or completely uninterpretable
  The two primary areas of collaborative filtering are the     dimensions. For users, each factor measures how much
neighborhood methods and latent factor models. Neighbor-     the user likes movies that score high on the correspond-
hood methods are centered on computing the relationships     ing movie factor.
between items or, alternatively, between users. The item-        Figure 2 illustrates this idea for a simplified example
oriented app

## Liang2023HELM

**Holistic Evaluation of Language Models**

Source: https://arxiv.org/abs/2211.09110

Consulted scope: original/retrieved abstract.

Abstract: Language models (LMs) are becoming the foundation for almost all major language technologies, but their capabilities, limitations, and risks are not well understood. We present Holistic Evaluation of Language Models (HELM) to improve the transparency of language models. First, we taxonomize the vast space of potential scenarios (i.e. use cases) and metrics (i.e. desiderata) that are of interest for LMs. Then we select a broad subset based on coverage and feasibility, noting what's missing or underrepresented (e.g. question answering for neglected English dialects, metrics for trustworthiness). Second, we adopt a multi-metric approach: We measure 7 metrics (accuracy, calibration, robustness, fairness, bias, toxicity, and efficiency) for each of 16 core scenarios when possible (87.5% of the time). This ensures metrics beyond accuracy don't fall to the wayside, and that trade-offs are clearly exposed. We also perform 7 targeted evaluations, based on 26 targeted scenarios, to analyze specific aspects (e.g. reasoning, disinformation). Third, we conduct a large-scale evaluation of 30 prominent language models (spanning open, limited-access, and closed models) on all 42 scenarios, 21 of which were not previously used in mainstream LM evaluation. Prior to HELM, models on average were evaluated on just 17.9% of the core HELM scenarios, with some prominent models not sharing a single scenario in common. We improve this to 96.0%: now all 30 models have been densely benchmarked on the same core scenarios and metrics under standardized conditions. Our evaluation surfaces 25 top-level findings. For full transparency, we release all raw model prompts and completions publicly for further analysis, as well as a general modular toolkit. We intend for HELM to be a living benchmark for the community, continuously updated with new scenarios, metrics, and models.

## Mazumder2010Spectral

**Spectral Regularization Algorithms for Learning Large Incomplete Matrices**

Source: https://jmlr.org/papers/v11/mazumder10a.html

Consulted scope: original full-text excerpt or original abstract page.

Spectral Regularization Algorithms for Learning Large Incomplete Matrices Home Page Papers Submissions News Editorial Board Special Issues Open Source Software Proceedings (PMLR) Data (DMLR) Transactions (TMLR) Search Statistics Login Frequently Asked Questions Contact Us Spectral Regularization Algorithms for Learning Large Incomplete Matrices Rahul Mazumder, Trevor Hastie, Robert Tibshirani ; 11(80):2287−2322, 2010. Abstract We use convex relaxation techniques to provide a sequence of
regularized low-rank solutions for large-scale matrix completion
problems. Using the nuclear norm as a regularizer, we provide a
simple and very efficient convex algorithm for minimizing the
reconstruction error subject to a bound on the nuclear norm. Our
algorithm SOFT-IMPUTE iteratively replaces the missing
elements with those obtained from a soft-thresholded SVD. With warm
starts this allows us to efficiently compute an entire
regularization path of solutions on a grid of values of the
regularization parameter. The computationally intensive part of our
algorithm is in computing a low-rank SVD of a dense matrix.
Exploiting the problem structure, we show that the task can be
performed with a complexity of order linear in the matrix dimensions.  Our
semidefinite-programming algorithm is readily scalable to large
matrices; for example SOFT-IMPUTE takes a few hours to compute low-rank approximations
of a 10 6 X 10 6 incomplete matrix with 10 7 observed entries, and fits a rank- 95 approximation to the
full Netflix training set in 3.3 hours.
Our methods achieve good training and test errors and exhibit superior timings when compared to other competitive state-of-the-art
techniques. [abs] [ pdf ][ bib ] © JMLR 2010. 
( edit , beta ) Mastodon

## Muennighoff2023MTEB

**MTEB: Massive Text Embedding Benchmark**

Source: https://arxiv.org/abs/2210.07316

Consulted scope: original/retrieved abstract.

Abstract: Text embeddings are commonly evaluated on a small set of datasets from a single task not covering their possible applications to other tasks. It is unclear whether state-of-the-art embeddings on semantic textual similarity (STS) can be equally well applied to other tasks like clustering or reranking. This makes progress in the field difficult to track, as various models are constantly being proposed without proper evaluation. To solve this problem, we introduce the Massive Text Embedding Benchmark (MTEB). MTEB spans 8 embedding tasks covering a total of 58 datasets and 112 languages. Through the benchmarking of 33 models on MTEB, we establish the most comprehensive benchmark of text embeddings to date. We find that no particular text embedding method dominates across all tasks. This suggests that the field has yet to converge on a universal text embedding method and scale it up sufficiently to provide state-of-the-art results on all embedding tasks. MTEB comes with open-source code and a public leaderboard at this https URL .

## Polo2024Sloth

**Sloth: scaling laws for LLM skills to predict multi-benchmark performance across families**

Source: https://api.semanticscholar.org/graph/v1/paper/ARXIV%3A2412.06540?fields=title,authors,year,venue,abstract,externalIds,citationStyles,url,openAccessPdf

Consulted scope: original/retrieved abstract.

Scaling laws for large language models (LLMs) predict model performance based on parameters like size and training data. However, differences in training configurations and data processing across model families lead to significant variations in benchmark performance, making it difficult for a single scaling law to generalize across all LLMs. On the other hand, training family-specific scaling laws requires training models of varying sizes for every family. In this work, we propose Skills Scaling Laws (SSLaws, pronounced as Sloth), a novel scaling law that leverages publicly available benchmark data and assumes LLM performance is driven by low-dimensional latent skills, such as reasoning and instruction following. These latent skills are influenced by computational resources like model size and training tokens, but with varying efficiencies across model families. Sloth exploits correlations across benchmarks to provide more accurate and interpretable predictions while alleviating the need to train multiple LLMs per family. We present both theoretical results on parameter identification and empirical evaluations on 12 prominent benchmarks, from Open LLM Leaderboard v1/v2, demonstrating that Sloth predicts LLM performance accurately and offers insights into scaling behaviors for complex downstream tasks, increased test-time compute, and compute-optimal scaling of skills.

## Polo2024Tiny

**tinyBenchmarks: evaluating LLMs with fewer examples**

Source: https://arxiv.org/abs/2402.14992

Consulted scope: original/retrieved abstract.

Abstract: The versatility of large language models (LLMs) led to the creation of diverse benchmarks that thoroughly test a variety of language models' abilities. These benchmarks consist of tens of thousands of examples making evaluation of LLMs very expensive. In this paper, we investigate strategies to reduce the number of evaluations needed to assess the performance of an LLM on several key benchmarks. For example, we show that to accurately estimate the performance of an LLM on MMLU, a popular multiple-choice QA benchmark consisting of 14K examples, it is sufficient to evaluate this LLM on 100 curated examples. We release evaluation tools and tiny versions of popular benchmarks: Open LLM Leaderboard, MMLU, HELM, and AlpacaEval 2.0. Our empirical analysis demonstrates that these tools and tiny benchmarks are sufficient to reliably and efficiently reproduce the original evaluation results.

## Ruan2024Scaling

**Observational Scaling Laws and the Predictability of Language Model Performance**

Source: https://api.semanticscholar.org/graph/v1/paper/ARXIV%3A2405.10938?fields=title,authors,year,venue,abstract,externalIds,citationStyles,url,openAccessPdf

Consulted scope: original/retrieved abstract.

Understanding how language model performance varies with scale is critical to benchmark and algorithm development. Scaling laws are one approach to building this understanding, but the requirement of training models across many different scales has limited their use. We propose an alternative, observational approach that bypasses model training and instead builds scaling laws from ~100 publically available models. Building a single scaling law from multiple model families is challenging due to large variations in their training compute efficiencies and capabilities. However, we show that these variations are consistent with a simple, generalized scaling law where language model performance is a function of a low-dimensional capability space, and model families only vary in their efficiency in converting training compute to capabilities. Using this approach, we show the surprising predictability of complex scaling phenomena: we show that several emergent phenomena follow a smooth, sigmoidal behavior and are predictable from small models; we show that the agent performance of models such as GPT-4 can be precisely predicted from simpler non-agentic benchmarks; and we show how to predict the impact of post-training interventions like Chain-of-Thought and Self-Consistency as language model capabilities continue to improve.

## Rubin1976Missing

**Inference and missing data**

Source: https://api.openalex.org/works/https://doi.org/10.1093/biomet/63.3.581

Consulted scope: original/retrieved abstract.

When making sampling distribution inferences about the parameter of the data, θ, it is appropriate to ignore the process that causes missing data if the missing data are ‘missing at random’ and the observed data are ‘observed at random’, but these inferences are generally conditional on the observed pattern of missing data. When making direct-likelihood or Bayesian inferences about θ, it is appropriate to ignore the process that causes missing data if the missing data are missing at random and the parameter of the missing data process is ‘distinct’ from θ. These conditions are the weakest general conditions under which ignoring the process that causes missing data always leads to correct inferences.

## Subedi2012Mixture

**Clustering and classification via cluster-weighted factor analyzers**

Source: https://api.semanticscholar.org/graph/v1/paper/694ad2bbb3c55cac461f737ed994fd32082bfe8b?fields=title,authors,year,venue,abstract,externalIds,citationStyles,url,openAccessPdf

Consulted scope: original/retrieved abstract.

In model-based clustering and classification, the cluster-weighted model is a convenient approach when the random vector of interest is constituted by a response variable \documentclass[12pt]{minimal} \usepackage{amsmath} \usepackage{wasysym} \usepackage{amsfonts} \usepackage{amssymb} \usepackage{amsbsy} \usepackage{mathrsfs} \usepackage{upgreek} \setlength{\oddsidemargin}{-69pt} \begin{document}$$Y$$\end{document} and by a vector \documentclass[12pt]{minimal} \usepackage{amsmath} \usepackage{wasysym} \usepackage{amsfonts} \usepackage{amssymb} \usepackage{amsbsy} \usepackage{mathrsfs} \usepackage{upgreek} \setlength{\oddsidemargin}{-69pt} \begin{document}$${\varvec{X}}$$\end{document} of \documentclass[12pt]{minimal} \usepackage{amsmath} \usepackage{wasysym} \usepackage{amsfonts} \usepackage{amssymb} \usepackage{amsbsy} \usepackage{mathrsfs} \usepackage{upgreek} \setlength{\oddsidemargin}{-69pt} \begin{document}$$p$$\end{document} covariates. However, its applicability may be limited when \documentclass[12pt]{minimal} \usepackage{amsmath} \usepackage{wasysym} \usepackage{amsfonts} \usepackage{amssymb} \usepackage{amsbsy} \usepackage{mathrsfs} \usepackage{upgreek} \setlength{\oddsidemargin}{-69pt} \begin{document}$$p$$\end{document} is high. To overcome this problem, this paper assumes a latent factor structure for \documentclass[12pt]{minimal} \usepackage{amsmath} \usepackage{wasysym} \usepackage{amsfonts} \usepackage{amssymb} \usepackage{amsbsy} \usepackage{mathrsfs} \usepackage{upgreek} \setlength{\oddsidemargin}{-69pt} \begin{document}$${\varvec{X}}$$\end{document} in each mixture component, under Gaussian assumptions. This leads to the cluster-weighted factor analyzers (CWFA) model. By imposing constraints on the variance of \documentclass[12pt]{minimal} \usepackage{amsmath} \usepackage{wasysym} \usepackage{amsfonts} \usepackage{amssymb} \usepackage{amsbsy} \usepackage{mathrsfs} \usepackage{upgreek} \setlength{\oddsidemargin}{-69pt} \begin{document}$$Y$$\end{document} and the covariance matrix of \documentclass[12pt]{minimal} \usepackage{amsmath} \usepackage{wasysym} \usepackage{amsfonts} \usepackage{amssymb} \usepackage{amsbsy} \usepackage{mathrsfs} \usepackage{upgreek} \setlength{\oddsidemargin}{-69pt} \begin{document}$${\varvec{X}}$$\end{document}, a novel family of sixteen CWFA models is introduced for model-based clustering and classification. The alternating expectation-conditional maximization algorithm, for maximum likelihood estimation of the parameters of all models in the family, is described; to initialize the algorithm, a 5-step hierarchical procedure is proposed, which uses the nested structures of the models within the family and thus guarantees the natural ranking among the sixteen likelihoods. Artificial and real data show that these models have very good clustering and classification performance and that the algorithm is able to recover the parameters very well.

## Tipping1999PPCA

**Probabilistic Principal Component Analysis**

Source: https://api.semanticscholar.org/graph/v1/paper/DOI%3A10.1111%2F1467-9868.00196?fields=title,authors,year,venue,abstract,externalIds,citationStyles,url,openAccessPdf

Consulted scope: original/retrieved abstract.

Summary Principal component analysis (PCA) is a ubiquitous technique for data analysis and processing, but one which is not based on a probability model. We demonstrate how the principal axes of a set of observed data vectors may be determined through maximum likelihood estimation of parameters in a latent variable model that is closely related to factor analysis. We consider the properties of the associated likelihood function, giving an EM algorithm for estimating the principal subspace iteratively, and discuss, with illustrative examples, the advantages conveyed by this probabilistic approach to PCA.

## Viroli2010Mixture

**Dimensionally Reduced Model-Based Clustering Through Mixtures of Factor Mixture Analyzers**

Source: https://link.springer.com/article/10.1007/s00357-010-9063-7

Consulted scope: original full-text excerpt or original abstract page.

Abstract Dimensionally reduced model-based clustering methods are recently receiving a wide interest in statistics as a tool for performing simultaneously clustering and dimension reduction through one or more latent variables. Among these, Mixtures of Factor Analyzers assume that, within each component, the data are generated according to a factor model, thus reducing the number of parameters on which the covariance matrices depend. In Factor Mixture Analysis clustering is performed through the factors of an ordinary factor analysis which are jointly modelled by a Gaussian mixture. The two approaches differ in genesis, parameterization and consequently clustering performance. In this work we propose a model which extends and combines them. The proposed Mixtures of Factor Mixture Analyzers provide a unified class of dimensionally reduced mixture models which includes the previous ones as special cases and could offer a powerful tool for modelling non-Gaussian latent variables. 

## Viroli2017Deep

**Deep Gaussian mixture models**

Source: https://arxiv.org/abs/1711.06929

Consulted scope: original full-text excerpt or original abstract page.

[1711.06929] Deep Gaussian Mixture Models
Abstract: Deep learning is a hierarchical inference method formed by subsequent multiple layers of learning able to more efficiently describe complex relationships. In this work, Deep Gaussian Mixture Models are introduced and discussed. A Deep Gaussian Mixture model (DGMM) is a network of multiple layers of latent variables, where, at each layer, the variables follow a mixture of Gaussian distributions. Thus, the deep mixture model consists of a set of nested mixtures of linear models, which globally provide a nonlinear model able to describe the data in a very flexible way. In order to avoid overparameterized solutions, dimension reduction by factor models can be applied at each layer of the architecture thus resulting in deep mixtures of factor analysers.

## Wei2017Missing

**Flexible High-Dimensional Unsupervised Learning with Missing Data**

Source: https://api.semanticscholar.org/graph/v1/paper/ae045e3c800e73999080a31bff4dee5dfdfbc152?fields=title,authors,year,venue,abstract,externalIds,citationStyles,url,openAccessPdf

Consulted scope: original/retrieved abstract.

The mixture of factor analyzers (MFA) model is a famous mixture model-based approach for unsupervised learning with high-dimensional data. It can be useful, inter alia, in situations where the data dimensionality far exceeds the number of observations. In recent years, the MFA model has been extended to non-Gaussian mixtures to account for clusters with heavier tail weight and/or asymmetry. The generalized hyperbolic factor analyzers (MGHFA) model is one such extension, which leads to a flexible modelling paradigm that accounts for both heavier tail weight and cluster asymmetry. In many practical applications, the occurrence of missing values often complicates data analyses. A generalization of the MGHFA is presented to accommodate missing values. Under a missing-at-random mechanism, we develop a computationally efficient alternating expectation conditional maximization algorithm for parameter estimation of the MGHFA model with different patterns of missing values. The imputation of missing values under an incomplete-data structure of MGHFA is also investigated. The performance of our proposed methodology is illustrated through the analysis of simulated and real data.

## Zhao2008ECM

**Fast ML Estimation for the Mixture of Factor Analyzers via an ECM Algorithm**

Source: https://api.crossref.org/works?rows=1&query.title=Fast%20ML%20Estimation%20for%20the%20Mixture%20of%20Factor%20Analyzers%20via%20an%20ECM%20Algorithm

Consulted scope: original/retrieved abstract.

In this brief, we propose a fast expectation conditional maximization (ECM) algorithm for maximum-likelihood (ML) estimation of mixtures of factor analyzers (MFA). Unlike the existing expectation-maximization (EM) algorithms such as the EM in Ghahramani and Hinton, 1996, and the alternating ECM (AECM) in McLachlan and Peel, 2003, where the missing data contains component-indicator vectors as well as latent factors, the missing data in our ECM consists of component-indicator vectors only. The novelty of our algorithm is that closed-form expressions in all conditional maximization (CM) steps are obtained explicitly, instead of resorting to numerical optimization methods. As revealed by experiments, the convergence of our ECM is substantially faster than EM and AECM regardless of whether assessed by central processing unit (CPU) time or number of iterations.
