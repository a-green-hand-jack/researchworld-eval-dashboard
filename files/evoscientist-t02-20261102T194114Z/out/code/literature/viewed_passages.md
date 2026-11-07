# Exact source-text passages displayed before the conservative stop

AUDIT ONLY: contains related-work passages and the accidental bibliography exposure. Do not treat this as a safe reading recommendation. Text is reconstructed from the saved extraction with the same page limits and cuts as the completed tool calls. PDF metadata headers and tool wrapper messages are not source-text passages and are not reproduced.

## Initial display: 2201.02177, PDF page 1, first 5000 extracted characters

```text
GROKKING : G ENERALIZATION BEYOND OVERFIT -
TING ON SMALL ALGORITHMIC DATASETS
Alethea Power, Yuri Burda, Harri Edwards, Igor Babuschkin
OpenAI
Vedant Misra∗
Google
ABSTRACT
In this paper we propose to study generalization of neural networks on small al-
gorithmically generated datasets. In this setting, questions about data efﬁciency,
memorization, generalization, and speed of learning can be studied in great de-
tail. In some situations we show that neural networks learn through a process
of “grokking” a pattern in the data, improving generalization performance from
random chance level to perfect generalization, and that this improvement in general-
ization can happen well past the point of overﬁtting. We also study generalization as
a function of dataset size and ﬁnd that smaller datasets require increasing amounts
of optimization for generalization. We argue that these datasets provide a fertile
ground for studying a poorly understood aspect of deep learning: generalization
of overparametrized neural networks beyond memorization of the ﬁnite training
dataset.
1 I NTRODUCTION
The generalization of overparameterized neural networks has long been a source of interest to the
machine learning community since it deﬁes intuitions derived from classical learning theory. In
this paper we show that training networks on small algorithmically generated datasets can reliably
exhibit unusual generalization patterns, clearly decoupled from performance on the training set, in a
signiﬁcantly more pronounced way than such effects manifest on datasets derived from natural data
(see Figure 1, left, for an example). Such experiments can be quickly reproduced on a single GPU,
and this makes them convenient testbeds for theories of generalization.
Figure 1: Left. Grokking: A dramatic example of generalization far after overﬁtting on an algorithmic
dataset. We train on the binary operation of division mod 97 with 50% of the data in the training set.
Each of the 97 residues is presented to the network as a separate symbol, similar to the representation
in the ﬁgure to the right. The red curves show training accuracy and the green ones show validation
accuracy. Training accuracy becomes close to perfect at < 103 optimization steps, but it takes
close to 106 steps for validation accuracy to reach that level, and we see very little evidence of any
generalization until 105 steps. Center. Training time required to reach 99% validation accuracy
increases rapidly as the training data fraction decreases. Right. An example of a small binary
operation table. We invite the reader to make their guesses as to which elements are missing.
∗Vedant was at OpenAI at the time of this work
1
arXiv:2201.02177v1  [cs.LG]  6 Jan 2022
```

## Initial display: 2301.05217, PDF page 1, first 5000 extracted characters

```text
Published as a conference paper at ICLR 2023
PROGRESS MEASURES FOR GROKKING VIA
MECHANISTIC INTERPRETABILITY
Neel Nanda∗, † Lawrence Chan‡ Tom Lieberum† Jess Smith† Jacob Steinhardt‡
ABSTRACT
Neural networks often exhibit emergent behavior, where qualitatively new capa-
bilities arise from scaling up the amount of parameters, training data, or training
steps. One approach to understanding emergence is to find continuous progress
measures that underlie the seemingly discontinuous qualitative changes. We ar-
gue that progress measures can be found via mechanistic interpretability: reverse-
engineering learned behaviors into their individual components. As a case study,
we investigate the recently-discovered phenomenon of “grokking” exhibited by
small transformers trained on modular addition tasks. We fully reverse engineer
the algorithm learned by these networks, which uses discrete Fourier transforms
and trigonometric identities to convert addition to rotation about a circle. We
confirm the algorithm by analyzing the activations and weights and by perform-
ing ablations in Fourier space. Based on this understanding, we define progress
measures that allow us to study the dynamics of training and split training into
three continuous phases: memorization, circuit formation, and cleanup. Our re-
sults show that grokking, rather than being a sudden shift, arises from the gradual
amplification of structured mechanisms encoded in the weights, followed by the
later removal of memorizing components.
1 I NTRODUCTION
Neural networks often exhibit emergent behavior, in which qualitatively new capabilities arise from
scaling up the model size, training data, or number of training steps (Steinhardt, 2022; Wei et al.,
2022a). This has led to a number of breakthroughs, via capabilities such as in-context learning (Rad-
ford et al., 2019; Brown et al., 2020) and chain-of-thought prompting (Wei et al., 2022b). However,
it also poses risks: Pan et al. (2022) show that scaling up the parameter count of models by as little
as 30% can lead to emergent reward hacking.
Emergence is most surprising when it is abrupt, as in the case of reward hacking, chain-of-thought
reasoning, or other phase transitions (Ganguli et al., 2022; Wei et al., 2022a). We could better
understand and predict these phase transitions by finding hidden progress measures (Barak et al.,
2022): metrics that precede and are causally linked to the phase transition, and which vary more
smoothly. For example, Wei et al. (2022a) show that while large language models show abrupt
jumps in their performance on many benchmarks, their cross-entropy loss decreases smoothly with
model scale. However, cross-entropy does not explain why the phase changes happen.
In this work, we introduce a different approach to uncovering hidden progress measures: via mech-
anistic explanations.1 A mechanistic explanation aims to reverse engineer the mechanisms of the
network, generally by identifying the circuits (Cammarata et al., 2020; Elhage et al., 2021) within
a model that implement a behavior. Using such explanations, we study grokking, where models
abruptly transition to a generalizing solution after a large number of training steps, despite initially
overfitting (Power et al., 2022). Specifically, we study modular addition, where a model takes inputs
a, b∈ {0, . . . , P− 1} for some prime P and predicts their sum c mod P . Small transformers trained
with weight decay on this task consistently exhibit grokking (Figure 2, Appendix C.2).
∗Corresponding author, please direct correspondence to: neelnanda27@gmail.com
†Independent researcher.
‡University of California, Berkeley.
1Interactive versions of figures, as well as the code to reproduce our results, are available at https:
//neelnanda.io/grokking-paper.
1
arXiv:2301.05217v3  [cs.LG]  19 Oct 2023
```

## Initial display: 2210.01117, PDF page 1, first 5000 extracted characters

```text
Published as a conference paper at ICLR 2023
OMNIGROK : G ROKKING BEYOND ALGORITHMIC
DATA
Ziming Liu, Eric J. Michaud & Max Tegmark
Department of Physics, Institute for AI and Fundamental Interactions
Massachusetts Institute of Technology
{zmliu,ericjm,tegmark}@mit.edu
ABSTRACT
Grokking, the unusual phenomenon for algorithmic datasets where generalization
happens long after overﬁtting the training data, has remained elusive. We aim to un-
derstand grokking by analyzing the loss landscapes of neural networks, identifying
the mismatch between training and test loss landscapes as the cause for grokking.
We refer to this as the "LU mechanism" because training and test losses (against
model weight norm) typically resemble "L" and "U", respectively. This simple
mechanism can nicely explain many aspects of grokking: data size dependence,
weight decay dependence, the emergence of representations, etc. Guided by the
intuitive picture, we are able to induce grokking on tasks involving images, lan-
guage and molecules. In the reverse direction, we are able to eliminate grokking for
algorithmic datasets. We attribute the dramatic nature of grokking for algorithmic
datasets to representation learning.
1 I NTRODUCTION
Generalization lies at the heart of machine learning. A good machine learning model should arguably
be able to generalize fast, and behave in a smooth/predictable way under changes of (hyper)parameters.
Grokking, the phenomenon where the model generalizes long after overﬁtting the training set, has
raised interesting questions after it was observed on algorithmic datasets by (Power et al., 2022):
Q1 The origin of grokking: Why is generalization much delayed after overﬁtting?
Q2 The prevalence of grokking: Can grokking occur on datasets other than algorithmic datasets?
This paper aims to answer these questions by analyzing neural loss landscapes:
A1 Grokking is caused by the mismatch between training and test loss landscapes. Speciﬁcally,
(reduced) training and test losses plotted against model weight norm resemble "L" and "U",
respectively, as shown in Figure 1b. We refer to this phenomenon as the "LU mechanism",
which we elaborate on in Section 2 and 3.
A2 Yes . Indeed, we demonstrate grokking for a wide range of machine learning tasks in Section 4,
including image classiﬁcation, sentiment analysis and molecule property prediction. Grokking
signals observed for these tasks are usually less dramatic than for algorithmic datasets, which
we attribute to representation learning in Section 5.
Partial answers to Q1 are provided in recent studies: Liu et al. (2022) attribute grokking to the slow
formation of good representations, Thilak et al. (2022) attempts to link grokking to the slingshot
mechanism of adaptive optimizers, and Barak et al. (2022) uses Fourier gap to describe hidden
progress. This paper aims to understand grokking through the lens of neural loss landscapes. Our
landscape analysis is able to explain many aspects of grokking: data size dependence, weight decay
dependence, emergence of representations, etc.
The paper is organized as follows: In Section 2, we review background on generalization, and
introduce the LU mechanism. In Section 3, we show how the LU mechanism leads to grokking for a
toy teacher-student setup. In Section 4, we show that the intuition gained from the toy problem can
1
arXiv:2210.01117v2  [cs.LG]  23 Mar 2023
```

## Initial display: 2309.02390, PDF page 1, first 5000 extracted characters

```text
5 September 2023
Explaining grokking through circuit efficiency
Vikrant Varma*, 1, Rohin Shah*, 1, Zachary Kenton1, János Kramár1 and Ramana Kumar1
*Equal contributions,1Google DeepMind
One of the most surprising puzzles in neural network generalisation isgrokking: a network with perfect
training accuracy but poor generalisation will, upon further training, transition to perfect generalisation.
Weproposethatgrokkingoccurswhenthetaskadmitsageneralisingsolutionandamemorisingsolution,
where the generalising solution is slower to learn but moreefficient, producing larger logits with the
same parameter norm. We hypothesise that memorising circuits become more inefficient with larger
training datasets while generalising circuits do not, suggesting there is a critical dataset size at which
memorisation and generalisation are equally efficient. We make and confirm four novel predictions about
grokking, providing significant evidence in favour of our explanation. Most strikingly, we demonstrate
two novel and surprising behaviours:ungrokking, in which a network regresses from perfect to low test
accuracy, andsemi-grokking, in which a network shows delayed generalisation to partial rather than
perfect test accuracy.
1. Introduction
When training a neural network, we expect that once training loss converges to a low value, the
network will no longer change much. Power et al. (2021) discovered a phenomenon dubbedgrokking
that drastically violates this expectation. The network first “memorises” the data, achieving low
and stable training loss with poor generalisation, but with further training transitions to perfect
generalisation. We are left with the question: why does the network’s test performance improve
dramatically upon continued training, having already achieved nearly perfect training performance?
Recent answers to this question vary widely, including the difficulty of representation learning (Liu
et al., 2022), the scale of parameters at initialisation (Liu et al., 2023), spikes in loss ("slingshots") (Thi-
lak et al., 2022), random walks among optimal solutions (Millidge, 2022), and the simplicity of
the generalising solution (Nanda et al., 2023, Appendix E). In this paper, we argue that the last
explanation is correct, by stating a specific theory in this genre, deriving novel predictions from the
theory, and confirming the predictions empirically.
We analyse the interplay between the internal mechanisms that the neural network uses to
calculate the outputs, which we loosely call “circuits” (Olah et al., 2020). We hypothesise that there
are two families of circuits that both achieve good training performance: one which generalises well
(𝐶gen) and one which memorises the training dataset (𝐶mem). The key insight is thatwhen there
are multiple circuits that achieve strong training performance, weight decay prefers circuits with high
“efficiency”, that is, circuits that require less parameter norm to produce a given logit value.
Efficiency answers our question above: if𝐶genis more efficient than𝐶mem, gradient descent can
reduce nearly perfect training loss even further by strengthening𝐶genwhile weakening𝐶mem, which
then leads to a transition in test performance. With this understanding, we demonstrate in Section 3
that three key properties are sufficient for grokking: (1)𝐶gengeneralises well while𝐶memdoes not,
(2)𝐶genis more efficient than𝐶mem, and (3)𝐶genis learned more slowly than𝐶mem.
Since 𝐶gengeneralises well, it automatically works for any new data points that are added to
the training dataset, and so its efficiency should be independent of the size of the training dataset.
In contrast,𝐶memmust memorise any additional data points added to the training dataset, and so
Corresponding author(s): vikrantvarma@deepmind.com, rohinmshah@deepmind.com
arXiv:2309.02390v1  [cs.LG]  5 Sep 2023
```

## Initial display: 2310.06110, PDF page 1, first 5000 extracted characters

```text
Published as a conference paper at ICLR 2024
GROKKING AS THE TRANSITION FROM LAZY TO RICH
TRAINING DYNAMICS
Tanishq Kumar Blake Bordelon Samuel J. Gershman ∗ Cengiz Pehlevan∗
Harvard University
ABSTRACT
We propose that the grokking phenomenon, where the train loss of a neural net-
work decreases much earlier than its test loss, can arise due to a neural network
transitioning from lazy training dynamics to a rich, feature learning regime. To il-
lustrate this mechanism, we study the simple setting of vanilla gradient descent on
a polynomial regression problem with a two layer neural network which exhibits
grokking without regularization in a way that cannot be explained by existing the-
ories. We identify sufficient statistics for the test loss of such a network, and track-
ing these over training reveals that grokking arises in this setting when the network
first attempts to fit a kernel regression solution with its initial features, followed
by late-time feature learning where a generalizing solution is identified after train
loss is already low. We find that the key determinants of grokking are the rate of
feature learning—which can be controlled precisely by parameters that scale the
network output—and the alignment of the initial features with the target function
y(x). We argue this delayed generalization arises when (1) the top eigenvectors
of the initial neural tangent kernel and the task labels y(x) are misaligned, but (2)
the dataset size is large enough so that it is possible for the network to generalize
eventually, but not so large that train loss perfectly tracks test loss at all epochs,
and (3) the network begins training in the lazy regime so does not learn features
immediately. We conclude with evidence that this transition from lazy (linear
model) to rich training (feature learning) can control grokking in more general
settings, like on MNIST, one-layer Transformers, and student-teacher networks.
1 I NTRODUCTION
The goal of a machine learning system is to learn models that generalize beyond their training set.
Typically, a practitioner hopes that a model’s performance on its training set will be an indicator of
its generalization capabilities on unseen data. However, this may not happen in practice. Grokking,
discovered by Power et al. (2022), is a phenomenon where the train loss of a network falls initially
with no corresponding decrease in test loss, then the network generalizes later during training. There
has been much recent work studying this phenomenon not only because it challenges the widely-
used approaches of early stopping or train loss termination criteria, but also because some Nanda
et al. (2023) see grokking as an example of sudden, emergent behavior in a neural network, and a
principle aim of the field of ML interpretability is to understand model internals well enough that
they do not exhibit such unexpected and unpredictable changes in behavior.
For these reasons, the phenomenology of grokking has been under close empirical study since its
discovery (Nanda et al., 2023; Davies et al., 2023; Thilak et al., 2022; Varma et al., 2023; Liu et al.,
2022a;b; Gromov, 2023). A limited number of theories have been proposed to explain the causes of
grokking, most notably those that attribute grokking to weight decay and weight norm decrease (Liu
et al., 2022a; Varma et al., 2023). However, we give counterexamples to such theories, implying a
need to explain grokking in a way that is consistent with empirical observations in current and past
work.
In this paper, we propose the idea that grokking is caused by delayed feature learning during training.
Our theoretical framework relies on the idea of lazy training where a network can fit its training
∗Equal Senior Authors. Correspondence to cpehlevan@seas.harvard.edu.
1
arXiv:2310.06110v3  [stat.ML]  11 Apr 2024
```

## Initial display: 2303.06173, PDF page 1, first 5000 extracted characters

```text
Unifying Grokking and Double Descent
Xander Davies∗
Harvard University
Lauro Langosco∗
University of Cambridge
David Krueger
University of Cambridge
Abstract
A principled understanding of generalization in deep learning may require unifying
disparate observations under a single conceptual framework. Previous work has
studied grokking, a training dynamic in which a sustained period of near-perfect
training performance and near-chance test performance is eventually followed by
generalization, as well as the superﬁcially similar double descent. These topics
have so far been studied in isolation. We hypothesize that grokking and double
descent can be understood as instances of the same learning dynamics within a
framework of pattern learning speeds. We propose that this framework also applies
when varying model capacity instead of optimization steps, and provide the ﬁrst
demonstration of model-wise grokking.
1 Introduction
102 103 104 105
Training steps
0.0
0.2
0.4
0.6
0.8
1.0
Training Accuracy
T est Accuracy
(a) Typical grokking on a modular
division task.
102 103 104 105
Training steps
10 2
10 1
100
Training Accuracy
T est Accuracy
(b) Plotting log accuracy reveals a
small double descent.
102 103 104 105
Training steps
0.0
2.5
5.0
7.5
10.0
12.5
15.0
17.5
Training Loss
T est Loss
(c) The double descent is more pro-
nounced in loss.
Figure 1: Three views of the same training run, replicated from Power et al. (2022).
On some datasets, neural networks exhibit surprising training dynamics termed grokking by Power
et al. (2022). In grokking, the model initially overﬁts, achieving perfect performance on the training
set while remaining at near-chance performance on the test set. Later in training, test performance
improves and the model eventually achieves perfect test accuracy. Grokking is reminiscent of the
double descent phenomenon (Belkin et al., 2018; Nakkiran et al., 2021), in which test performance
initially improves, then worsens as the model overﬁts, and then eventually improves again as model
capacity increases.
We argue that double descent and grokking are best viewed as two instances of the same phenomenon,
in which inductive biases prefer better-generalizing but slower to learn patterns, leading to a transition
from poorly-generalizing to well-generalizing patterns. This transition happens both epoch-wise as a
function of training time (Figure 1) and model-wise as a function of model size (Figure 4).
∗Equal contribution. Correspondence to alexander_davies@college.harvard.edu.
ML Safety Workshop, 36th Conference on Neural Information Processing Systems (NeurIPS 2022).
arXiv:2303.06173v1  [cs.LG]  10 Mar 2023
```

## Initial display: 1711.05101, PDF page 1, first 5000 extracted characters

```text
Published as a conference paper at ICLR 2019
DECOUPLED WEIGHT DECAY REGULARIZATION
Ilya Loshchilov & Frank Hutter
University of Freiburg
Freiburg, Germany,
{ilya,fh}@cs.uni-freiburg.de
ABSTRACT
L2 regularization and weight decay regularization are equivalent for standard
stochastic gradient descent (when rescaled by the learning rate), but as we demon-
strate this is not the case for adaptive gradient algorithms, such as Adam. While
common implementations of these algorithms employ L 2 regularization (often
calling it “weight decay” in what may be misleading due to the inequivalence we
expose), we propose a simple modiﬁcation to recover the original formulation of
weight decay regularization bydecoupling the weight decay from the optimization
steps taken w.r.t. the loss function. We provide empirical evidence that our pro-
posed modiﬁcation (i) decouples the optimal choice of weight decay factor from
the setting of the learning rate for both standard SGD and Adam and (ii) substan-
tially improves Adam’s generalization performance, allowing it to compete with
SGD with momentum on image classiﬁcation datasets (on which it was previously
typically outperformed by the latter). Our proposed decoupled weight decay has
already been adopted by many researchers, and the community has implemented
it in TensorFlow and PyTorch; the complete source code for our experiments is
available at https://github.com/loshchil/AdamW-and-SGDW
1 I NTRODUCTION
Adaptive gradient methods, such as AdaGrad (Duchi et al., 2011), RMSProp (Tieleman & Hinton,
2012), Adam (Kingma & Ba, 2014) and most recently AMSGrad (Reddi et al., 2018) have become
a default method of choice for training feed-forward and recurrent neural networks (Xu et al., 2015;
Radford et al., 2015). Nevertheless, state-of-the-art results for popular image classiﬁcation datasets,
such as CIFAR-10 and CIFAR-100 Krizhevsky (2009), are still obtained by applying SGD with
momentum (Gastaldi, 2017; Cubuk et al., 2018). Furthermore, Wilson et al. (2017) suggested that
adaptive gradient methods do not generalize as well as SGD with momentum when tested on a
diverse set of deep learning tasks, such as image classiﬁcation, character-level language modeling
and constituency parsing. Different hypotheses about the origins of this worse generalization have
been investigated, such as the presence of sharp local minima (Keskar et al., 2016; Dinh et al.,
2017) and inherent problems of adaptive gradient methods (Wilson et al., 2017). In this paper, we
investigate whether it is better to use L 2 regularization or weight decay regularization to train deep
neural networks with SGD and Adam. We show that a major factor of the poor generalization of the
most popular adaptive gradient method, Adam, is due to the fact that L2 regularization is not nearly
as effective for it as for SGD. Speciﬁcally, our analysis of Adam leads to the following observations:
L2 regularization and weight decay are not identical. The two techniques can be made equiv-
alent for SGD by a reparameterization of the weight decay factor based on the learning
rate; however, as is often overlooked, this is not the case for Adam. In particular, when
combined with adaptive gradients, L 2 regularization leads to weights with large historic
parameter and/or gradient amplitudes being regularized less than they would be when us-
ing weight decay.
L2 regularization is not effective in Adam. One possible explanation why Adam and other
adaptive gradient methods might be outperformed by SGD with momentum is that common
deep learning libraries only implement L 2 regularization, not the original weight decay.
Therefore, on tasks/datasets where the use of L2 regularization is beneﬁcial for SGD (e.g.,
1
arXiv:1711.05101v3  [cs.LG]  4 Jan 2019
```

## Batch 1: 2201.02177, PDF page 2

```text
The datasets we consider are binary operation tables of the forma◦b =c wherea,b,c are discrete
symbols with no internal structure, and◦ is a binary operation. Examples of binary operations include
addition, composition of permutations, and bivariate polynomials. Training a neural network on a
proper subset of all possible equations then amounts to ﬁlling in the blanks of the binary op table,
much like solving a Sudoku puzzle. An example is shown on the right in Figure 1. Since we use
distinct abstract symbols for all distinct elementsa,b,c involved in the equations, the network is not
made aware of any internal structure of the elements, and has to learn about their properties only
from their interactions with other elements. For example the network doesn’t see numbers in decimal
notation, or permutations in line notation.
Our contributions are as follows:
• We show that neural networks are capable of generalizing to the empty slots in a variety of
binary op tables.
• We show that, long after severely overﬁtting, validation accuracy sometimes suddenly
begins to increase from chance level toward perfect generalization. We call this phenomenon
‘grokking’. An example is shown in Figure 1.
• We present the data efﬁciency curves for a variety of binary operations.
• We show empirically that the amount of optimization required for generalization quickly
increases as the dataset size decreases.
• We compare various optimization details to measure their impact on data efﬁciency. We ﬁnd
that weight decay is particularly effective at improving generalization on the tasks we study.
• We visualize the symbol embeddings learned by these networks and ﬁnd that they sometimes
uncover recognizable structure of the mathematical objects represented by the symbols.
2 M ETHOD
All of our experiments used a small transformer trained on datasets of equations of the forma◦b =c,
where each of “a”, “◦”, “b”, “=”, and “c” is a separate token. Details of the operations studied, the
architecture, training hyperparameters and tokenization can be found in Appendix A.1.
3 E XPERIMENTS
3.1 G ENERALIZATION BEYOND OVERFITTING
Deep learning practitioners are used to seeing small improvements in validation accuracy after
validation loss stops decreasing. A double descent of validation loss has been documented in
some circumstances, but is considered unusual among practitioners Nakkiran et al. (2019); Belkin
et al. (2018); d’Ascoli et al. (2020). On the small algorithmic datasets that we study, improved
generalization after initial overﬁtting occurs for a range of models, optimizers, and dataset sizes,
and in some cases these effects are extremely pronounced. A typical example is shown for modular
division in Figure 1. There we see that validation accuracy starts increasing beyond chance level
only after 1000 times more optimization steps than are required for training accuracy to get close to
optimal. In Figure 4 the training/validation losses are also plotted and we see the double descent of
the validation loss.
We found these behaviors to be typical for all the binary operations for dataset sizes that were close
to the minimal dataset size for which the network generalized within the allotted optimization budget.
For larger dataset sizes, the training and validation curves tend to track each other more closely.
3.1.1 L EARNING TIME CURVES
In a typical supervised learning problem, decreasing the amount of training data decreases the
converged generalization performance of the model when the optimization procedure is capable of
interpolating the training data. In our setting, we observe a different phenomenon: while the converged
performance stays constant at 100% within a range of training dataset sizes, the optimization time
required to achieve that performance grows quicky as the dataset size is decreased.
2
```

## Batch 1: 2201.02177, PDF page 3

```text
Figure 2: Left. Different optimization algorithms lead to different amounts of generalization within
an optimization budget of 105 steps for the problem of learning the product in the abstract groupS5.
Weight decay improves generalization the most, but some generalization happens even with full batch
optimizers and models without weight or activation noise at high percentages of training data. Subop-
timal choice hyperparameters severely limit generalization. Not shown: training accuracy reaches
100% after 103-104 updates for all optimization methods. Right. Best validation accuracy achieved
after 105 steps on a variety of algorithmic datasets, averaged over 3 seeds. Generalization happens at
higher percentages of data for intuitively more complicated and less symmetrical operations.
Figure 1 (center) shows median number of optimization steps until validation performance ﬁrst
reaches 99% for the product in abstract groupS5. In the vicinity of 25-30% of data, a decrease of 1%
of training data leads to an increase of 40-50% in median time to generalization. While the number
of steps until validation accuracy> 99% grows quickly as dataset size decreases, the number of steps
until the train accuracy ﬁrst reaches 99% generally trends down as dataset size decreases and stays in
the range of 103-104 optimization steps. We’ve observed a similar pattern of exponential increase in
optimization time until reaching generalization as dataset size decreases on all the algorithmic tasks
for which we could get the networks to generalize.
3.2 G ROKKING ON A VARIETY OF PROBLEMS
We’ve measured the mean accuracy across three runs for training datasets consisting of different
fractions of all available equations for a variety of binary operations listed in Appendix A.1.1. The
results are presented in Figure 2 (right).
Since the operands are presented to the neural network as unrelated abstract symbols, the operations
x+y (mod p−1) andx∗y (mod p) with a prime numberp and non-zerox,y are indistinguishable
from the neural network’s perspective (and similarlyx−y (mod p− 1) andx/y (mod p)). This
is because every nonzero residue modulo a prime can be represented as a power of a primitive root.
This representation shows the equivalence (up to renaming of symbols) of modular addition modulo
p− 1 and modular multiplication modulop. We see in Figure 2 (right) thatx−y andx/y indeed
take about the same amount of data for generalization to occur.
Some of the operations listed in Figure 2 (right) are symmetric with respect to the order of the
operands (x +y,x∗y,x2 +y2 andx2 +xy +y2). Such operations tend to require less data for
generalization than closely related non-symmetrical counterparts (x−y,x/y,x2 +xy +y2 +x).
We believe this effect might be partially architecture-dependent, since it’s easy for a transformer to
learn a symmetric function of the operands by ignoring positional embedding.
Some operations (for example x3 +xy2 +y (mod 97)) didn’t lead to generalization within the
allowed optimization budget at any percentage of data up to 95%. The converged models effectively
just memorized the training dataset without ﬁnding any real patterns in the data. To such a model, the
data is effectively random.
The operation [x/y (mod p) ify is odd, otherwisex−y (mod p)] requires the network to learn a
mix of several simple operations - in particular the role ofx has to be interpreted as a residue in the
additive group when it’s paired with an eveny, and as a residue in the multiplicative group when it’s
paired with an odd y. This shows that generalization can happen even for operations that are not
cleanly interpretable via group or ring operations.
3.3 A BLATIONS AND TRICKS
We’ve tried various forms of regularization to see what can induce networks to generalize better on
our datasets. Here we present the data efﬁciency curves on a particular dataset S5 for a variety of
interventions: full-batch gradient descent, stochastic gradient descent, large or small learning rates,
3
```

## Batch 1: 2201.02177, PDF page 4

```text
residual dropout Srivastava et al. (2014), weight decay Loshchilov & Hutter (2017) and gradient
noise Neelakantan et al. (2015). The results are shown in Figure 2 (left).
We ﬁnd that adding weight decay has a very large effect on data efﬁciency, more than halving the
amount of samples needed compared to most other interventions. We found that weight decay towards
the initialization of the network is also effective, but not quite as effective as weight decay towards
the origin. This makes us believe that the prior, that approximately zero weights are suitable for small
algorithmic tasks, explains part, but not all of the superior performance of weight decay. Adding some
noise to the optimization process (e.g. gradient noise from using minibatches, Gaussian noise applied
to weights before or after computing the gradients) is beneﬁcial for generalization, consistent with
the idea that such noise might induce the optimization to ﬁnd ﬂatter minima that generalize better.
We found that learning rate had to be tuned in a relatively narrow window for the generalization to
happen (within 1 order of magnitude).
3.4 Q UALITATIVE VISUALIZATION OF EMBEDDINGS
In order to gain some insight into networks that generalize, we visualized the matrix of the output
layer for the case of modular addition andS5. In Figure 3 we show t-SNE plots of the row vectors.
For some networks we ﬁnd clear reﬂections of the structure of the underlying mathematical objects
in the plots. For example the circular topology of modular addition is shown with a ‘number line’
formed by adding 8 to each element. The structure is more apparent in networks that were optimized
with weight decay.
4 D ISCUSSION
We have seen that in the datasets we studied, small algorithmic binary operation tables, effects such
as double descent or late generalization, and improvements to generalization from interventions like
weight decay can be striking. This suggests that these datasets could be a good place to investigate
aspects of generalization. For example, we plan to test whether various proposed measures of minima
ﬂatness correlate with generalization in our setting.
We have also seen that visualizing the embedding spaces of these neural networks can show natural
kinds of structure, for example in problems of modular arithmetic the topology of the embeddings
tends to be circles or cylinders. We also see that the network tends to idiosyncratically organize the
embeddings by various residues. Whilst the properties of these mathematical objects are familiar to
us, we speculate that such visualizations could one day be a useful way to gain intuitions about novel
mathematical objects.
Figure 3: Left. t-SNE projection of the output layer weights from a network trained onS5. We see
clusters of permutations, and each cluster is a coset of the subgroup⟨(0, 3)(1, 4), (1, 2)(3, 4)⟩ or one
of its conjugates. Right. t-SNE projection of the output layer weights from a network trained on
modular addition. The lines show the result of adding 8 to each element. The colors show the residue
of each element modulo 8.
4
```

## Batch 1: 2201.02177, PDF page 5

```text
In addition, we document an interesting phenomenon, where the number of optimization steps needed
to reach a given level of performance increases quickly as we reduce the size of the training dataset.
Since this represents a way trade compute for performance on smaller amounts of data, it would be
useful to investigate in future work whether the effect is also present for other datasets.

[REFERENCES SUPPRESSED]
```

## Batch 1: 2301.05217, PDF page 2

```text
Published as a conference paper at ICLR 2023
Figure 1: The algorithm implemented by the one-layer transformer for modular addition. Given two
numbers a and b, the model projects each point onto a corresponding rotation using its embedding
matrix. Using its attention and MLP layers, it then composes the rotations to get a representation of
a + b mod P . Finally, it “reads off” the logits for each c ∈ {0, 1, ..., P− 1}, by rotating by −c to
get cos(w(a + b − c)), which is maximized when a + b ≡ c mod P (since w is a multiple of 2πP ).
We reverse engineer the weights of these transformers and find that they perform this task by map-
ping the inputs onto a circle and performing addition on the circle. Specifically, we show that the
embedding matrix maps the inputs a, bto sines and cosines at a sparse set of key frequencies wk.
The attention and MLP layers then combine these using trigonometric identities to compute the sine
and cosine of wk(a + b), and the output matrices shift and combine these frequencies.
We confirm this understanding with four lines of evidence (Section 4): (1) the network weights
and activations exhibit a consistent periodic structure; (2) the neuron-logit map WL is well approx-
imated by a sum of sinusoidal functions of the key frequencies, and projecting the MLP activations
onto these sinusoidal functions lets us “read off” trigonometric identities from the neurons; (3) the
attention heads and MLP neuron are well approximated by degree- 2 polynomials of trigonometric
functions of a single frequency; and (4) ablating key frequencies used by the model reduces perfor-
mance to chance, while ablating the other 95% of frequencies slightly improves performance.
Using our understanding of the learned algorithm, we construct two progress measures for the mod-
ular addition task— restricted loss, where we ablate every non-key frequency, and excluded loss,
where we instead ablate all key frequencies. Both metrics improve continuously prior to when
grokking occurs. We use these metrics to understand the training dynamics underlying grokking
and find that training can be split into three phases: memorization of the training data; circuit for-
mation, where the network learns a mechanism that generalizes; and cleanup, where weight decay
removes the memorization components. Surprisingly, the sudden transition to perfect test accuracy
in grokking occurs during cleanup, after the generalizing mechanism is learned. These results show
that grokking, rather than being a sudden shift, arises from the gradual amplification of structured
mechanisms encoded in the weights, followed by the later removal of memorizing components.
2 R ELATED WORK
Phase Changes. Recent papers have observed that neural networks quickly develop novel quali-
tative behaviors as they are scaled up or trained longer (Ganguli et al., 2022; Wei et al., 2022a).
McGrath et al. (2021) find that AlphaZero quickly learns many human chess concepts between 10k
and 30k training steps and reinvents human opening theory between 25k and 60k training steps.
Grokking. Grokking was first reported in Power et al. (2022), which trained two-layer transformers
on several algorithmic tasks and found that test accuracy often increased sharply long after achieving
perfect train accuracy. Millidge (2022) suggests that this may be due to SGD being a random walk
on the optimal manifold. Our results echo Barak et al. (2022) in showing that the network instead
makes continuous progress toward the generalizing algorithm. Liu et al. (2022) construct small
examples of grokking, which they use to compute phase diagrams with four separate “phases” of
learning. Thilak et al. (2022) argue that grokking can arise without explicit regularization, from an
optimization anomaly they dub the slingshot mechanism, which may act as an implicit regularizer.
2
```

## Batch 1: 2301.05217, PDF page 3

```text
Published as a conference paper at ICLR 2023
Figure 2: The train and test accuracy (left) and train and test loss (right) of one-layer transformers on
the modular addition task described in Section 3, over 5 random seeds. These models consistently
exhibit grokking: they quickly overfit early on in training, but then later learn to generalize.
Circuits-style mechanistic interpretability. The style of post-hoc mechanistic interpretability in
Section 4 is heavily inspired by the Circuits approach of Cammarata et al. (2020), Elhage et al.
(2021), and Olsson et al. (2022).
Progress measures. Barak et al. (2022) introduce the notion of progress measures—metrics that
improve smoothly and that precede emergent behavior. They prove theoretically that training would
amplify a certain mechanism and heuristically define a progress measure. In contrast, we use mech-
anistic intepretability to discover progress measures empirically.
3 S ETUP AND BACKGROUND
We train transformers to perform addition mod P . The input to the model is of the form “ a b =”,
where a and b are encoded as P -dimensional one-hot vectors, and = is a special token above which
we read the output c. In our mainline experiment, we take P = 113 and use a one-layer ReLU
transformer, token embeddings with d = 128, learned positional embeddings, 4 attention heads of
dimension d/4 = 32, and n = 512hidden units in the MLP. In other experiments, we vary the depth
and dimension of the model. We did not use LayerNorm or tie our embed/unembed matrices.
Our mainline dataset consists of 30% of the entire set of possible inputs (that is, 30% of the 113 ·
113 pairs of numbers mod P ). We use full batch gradient descent using the AdamW optimizer
(Loshchilov & Hutter, 2017) with learning rate γ = 0.001 and weight decay parameter λ = 1. We
perform 40, 000 epochs of training. As there are only 113 · 113 possible pairs, we evaluate test loss
and accuracy on all pairs of inputs not used for training.
Networks trained on this task consistently exhibit grokking. As Figure 2 shows, our networks first
overfit the training set: train accuracy quickly converges to 100% and the train loss quickly declines,
while the test accuracy remains low and the test loss remains high. After around 10, 000 epochs,
the network generalizes and test accuracy increases to near 100%. In robustness experiments, we
confirm that grokking consistently occurs for other architectures and prime moduli (Appendix C.2).
In Section 5.3 we find that grokking does not occur without regularization.
To describe transformer components, we follow the conventions and notations laid out in Elhage
et al. (2021). We focus on thed×p embedding matrix WE, the d×n output matrix of the MLP layer
Wout, and the P × d unembedding matrix WU .2 Let Logits(a, b) denote the logit vector on inputs
a, b, and M LP(a, b) denote the MLP activations. Empirically, our networks do not significantly use
the skip connection around the MLP (Appendix A.1), so Logits (a, b) ≈ WU WoutMLP(a, b). We
therefore also study the P × n neuron-logit map WL = WU Wout.
3.1 T HE FOURIER MULTIPLICATION ALGORITHM
We claim that the learned networks use the following algorithm (Figure 1):
• Given two one-hot encoded tokens a, bmap these to sin(wka), cos(wka), sin(wkb), and
cos(wkb) using the embedding matrix, for various frequencies wk = 2kπP , k∈ N.
2We ignore the embedding and unembedding of the ‘=’ token for simplicity.
3
```

## Batch 1: 2301.05217, PDF page 4

```text
Published as a conference paper at ICLR 2023
• Compute cos (wk(a + b)) and sin (wk(a + b)) using the trigonometric identities:
cos (wk(a + b)) = cos (wka) cos (wka) − sin (wka) sin (wkb)
sin (wk(a + b)) = sin(wka) cos (wkb) + cos (wka) sin (wkb)
In our networks, this is computed in the attention and MLP layers.
• For each output logit c, compute cos (wk(a + b − c)) using the trigonometric identity:
cos (wk(a + b − c)) = cos (wk(a + b)) cos (wkc) + sin (wk(a + b)) sin (wkc) . (1)
This is a linear function of the already-computed values cos(wk(a + b)), sin(wk(a + b))
and is implemented in the product of the output and unembedding matrices WL.
• The unembedding matrix also adds together cos (wk(a + b − c)) for the various ks. This
causes the cosine waves to constructively interfere atc∗ = a + b mod p (giving c∗ a large
logit), and destructively interfere everywhere else (thus giving small logits to other cs).
We refer to this algorithm as Fourier multiplication, and will justify our claim in detail in Section 4.
4 R EVERSE ENGINEERING A ONE -LAYER TRANSFORMER
In this section, we describe four lines of evidence that our transformers are using the Fourier mul-
tiplication algorithm described in Section 3.1. Here we apply our analysis to the mainline model
from Section 3; the results are broadly consistent for other models, including across different num-
ber of layers, different fractions of the training data, and different prime moduli (see Appendix C.2,
especially Table 5).
Our first line of evidence involves examining the network weights and activations and observing
consistent periodic structure that is unlikely to occur by chance (Section 4.1). Moreover, when we
take Fourier transforms, many components are either sparse or nearly sparse in the Fourier domain,
supported on a handful of key frequencies.
We next look into the actualmechanisms implemented in the model weights (Section 4.2). We show
that the unembedding matrix WL is (approximately) rank 10, where each direction corresponds to
the cosine or sine of one of 5 key frequencies. Projecting the MLP activations onto the components
of WL approximately produces multiples of the functions cos (wk(a + b)) and sin (wk(a + b)),
showing that the MLP layer does compute these sums.
To better understand the mechanism, we zoom in to individual neurons (Section 4.3). We find that
the attention heads and most neurons are well-approximated by degree- 2 polynomials of sines and
cosines at a single frequency. Moreover, the corresponding direction in WL also contains only that
frequency. This suggests that the model’s computations are (1) localized across frequencies and (2)
mostly aligned with the neuron basis.
Finally, we use ablations to confirm that our interpretation is faithful (Section 4.4). We replace
various components of the model by the components of the Fourier multiplication algorithm and
find that doing so consistently does not harm and sometimes even improves model performance.
4.1 S UGGESTIVE EVIDENCE : SURPRISING PERIODICITY
The first line of evidence that the network is using the algorithm described in Section 3.1 is the
surprising periodicity in the activations of the transformer. That is, the output of every part of the
network is periodic as a function of the input tokens.
Periodicity in the embeddings. We start by examining the embeddings. We apply a Fourier trans-
form along the input dimension of the embedding matrix WE then compute the ℓ2-norm along the
other dimension; results are shown in Figure 3. We plot only the components for the first 56 frequen-
cies, as the norm of the components for frequencies k and P − k are symmetric. The embedding
matrix WE is sparse in the Fourier basis–it only has significant nonnegligible norm at 6 frequencies.
Of these frequencies, only 5 appear to be used significantly in later parts of the model (corresponding
to k ∈ {14, 35, 41, 42, 52}). We dub these the key frequencies of the model.
Periodicity in attention heads and MLP neuron activations. This periodic structure recurs
throughout the network. As an example, we plot the attention weight at position 0 for every combi-
nation of two inputs for head 0 in Figure 4. The attention exhibits a periodic structure with frequency
4
```

## Batch 1: 2303.06173, PDF page 2

```text
epochs
0.0
0.5
1.0Predictiveness
Double Descent Patterns
Type 1
Type 2
Type 3
epochs
0.0
0.5
1.0Accuracy
Double Descent
train
test
epochs
0.0
0.5
1.0Predictiveness
Grokking Patterns
epochs
0.0
0.5
1.0Accuracy
Grokking
Figure 2: A simple model of pattern learning. Left to right, (1) development of pattern predic-
tiveness during double descent, with well-performing Type 1 (heuristics) patterns and somewhat-
predictive Type 3 (slow & well generalizing) patterns ; (2) resulting train and test accuracy curves for
double descent; (3) pattern predictiveness during grokking, with poorly-performing Type 1 patterns
and perfectly-predictive Type 3 patterns; (4) resulting train and test curves for grokking. In both
cases, Type 2 (medium & poorly-generalizing) patterns quickly achieve perfect predictiveness.
Contributions. We provide a conceptual framework (Claim 1, Claim 2) which uniﬁes the learning
dynamics of grokking and double descent. We propose a simple model (Section 2.2) to support
Claim 1, and provide evidence for Claim 2 by showing that grokking can occur as a function of model
size (Section 3).
2 Pattern Learning
We propose an abstract model of neural network training as pattern learning. Our model aims to
capture the intuitive notion that a network uses distinct kinds of mechanisms to classify different
inputs; for example, it might memorize some examples while applying heuristics to classify others.
We build on this notion of pattern to formulate our Claims 1 and 2, and describe our model in more
detail in Section 2.2.
2.1 Core Claims
We ﬁrst claim that epoch-wise double descent and grokking share the same underlying dynamics, and
then claim that these dynamics also transfer to the model-wise setting.
Claim 1 (Pattern learning dynamics). Grokking, like epoch-wise double descent, occurs when slow
patterns generalize well and are ultimately favored by the training regime, but are preceded by faster
patterns which generalize poorly.
We formalize Claim 1 in Section 2.2, where we propose a simple model of pattern learning to explain
neural network training dynamics. As shown in Figure 2, our model can produce the dynamics from
grokking as well as double descent.
Claim 2 (Duality between model size and scaling time) . Patterns can be viewed as a function of
model size as well as a function of training time, and learning dynamics are similar between these
two cases.2
If Claim 2 is correct, then grokking, like double descent, should happen model-wise as well as
epoch-wise. We conﬁrm this hypothesis empirically in Section 3.1.
2.2 A Model of Learning Dynamics
In our model, a neural network consists of a set ofn patterns that develop over time during training.
For any training point, the probability that patterni classiﬁes it correctly at time-stept ispi(t).We
modelpi as a sigmoid
pi(t) = γi1 +e−αi(t−bi),
parameterized by a maximum predictiveness 0≤γi≤ 1, inﬂection pointbi≥ 0, and learning speed
αi≥ 0. The probability that the overall model classiﬁes the training point correctly is then given by
2It is reasonable to speak of pattern learning as a function of effective capacity (Arpit et al., 2017) or effective
model complexity (Nakkiran et al., 2021), though we avoid doing so in this work so as to stay agnostic about the
precise metric.
2
```

## Batch 1: 2303.06173, PDF page 3

```text
p1(t)
p2(t)
Pattern Accuracy
p1(t)
p2(t)
Train Accuracy
p1(t)
p2(t)
Test Accuracy
g2
g1
g1 + g2
2
p1(t)
p2(t)
Test Accuracy (p1 preferred)
g2
g1
Figure 3: Two pattern model. Full square represents the data set. Left to right, (1) blue shows
training samples correctly classiﬁed byp1(t), red shows training samples correctly classiﬁed byp2(t),
dashed green shows samples correctly classiﬁed by both; (2) accuracy is the union of patterns 1 and
2; (3) test accuracy is the sum of correct classiﬁcations weighted by generalization parameters, and
by their average generalization in the case both correctly classifying; (4) test accuracy given pattern 1
is preferred, causing all examples correctly classiﬁed by pattern 1 to generalize according tog1.
the probability that any of the patterns does so. Since each data-point is classiﬁed independently, the
probability of classifying a single training point correctly is equal to the overall training accuracy,
acctrain(t) = 1−
n∏
i=1
(1−pi(t)). (1)
To calculate test accuracy of our model we assign additional generalization parametersg1,...,g n∈
[0, 1] to represent the idea that some patterns generalize better than others.3 We assume that patterns
that are more frequently successful during training are more used at test time. For any subsetA of
{1,...,n }, we deﬁne the probabilityPA(t) = ∏i∈Api(t) ∏j/∈A(1−pj(t)) that only the patterns in
A are successful, as well as the average generalization abilityG(A) = 1/|A| ∑i∈Agi of the patternsinA. Overall test accuracy at timet is then given by the average generalization ability weighted the
probability of success at train time,
acctest(t) =
∑
A⊆{1,...,n}
PA(t)G(A). (2)
We additionally introduce the notion of a preferred pattern, which we use to model the effect of
inductive biases on pattern development. When patternk is preferred,gk is weighted more highly in
Equation 2 by settingG(A) = gk ifk∈A and otherwiseG(A) = 1/|A| ∑i∈Agi as usual.
2.3 Double Descent & Grokking with Pattern Types
We model learning in double descent and grokking as interactions between three patterns learned at
different speeds during training: a heuristic pattern that is fast and generalizes well; an overﬁtting
pattern that is fast, though slower than the heuristic, and generalizes poorly; and aslow-generalizing
pattern that is slow and generalizes well. This last pattern is ultimately preferred by the inductive
biases of the model.
As shown in Figure 2, this simple model can produce grokking as well as double descent; the two can
be interpolated between by solely modulating the maximum predictiveness (γ) of the heuristic and
the slow-generalizing patterns.4
3In this model whether the network classiﬁes a given input correctly depends on whether it is in the training
set or the test set, which does not make sense in the case of i.i.d. data: in the real world, whether a given example
(x, y) is classiﬁed correctly or not is purely a fact about the value of (x, y) and the parameters of the model,
and doesn’t depend on whether its in the training or test set. However, we include such a dependence to model
neural networks that overﬁt the training set and thus are better able to classify training examples. Intuitively,
every pattern corresponds to a ‘generalization set’ of inputs that are classiﬁed using that pattern even if they did
not occur during training. The generalization parameter can then be viewed as the fraction of the generalization
set that is classiﬁed correctly.
4Code replicating our results is available at github.com/xanderdavies/unifying-grok-dd, including
an interactive notebook to explore the pattern learning model and interpolate between grokking and double
descent.
3
```

## Batch 1: 2303.06173, PDF page 4

```text
20 50 80 110 140
Transformer embedding dimension
0
140
940
5890
36560
226430Training steps
T est Loss
20 50 80 110 140
Transformer embedding dimension
Training Loss
0
5
10
15
20
0
2
4
6
Figure 4: Model-Wise Grokking. Darker color indicates lower loss, dotted line represents 90%
training accuracy. Left: Test loss as function of training steps and model size. Right: Training loss.
Epoch-Wise Grokking: Moving vertically from zero training steps, test loss initially falls, then rises
dramatically (beginning near perfect ﬁtting of the training set), and then falls again. Model-Wise
Grokking: Moving horizontally along training step counts which will eventually lead to low loss, we
see the same pattern of initial test loss decrease, followed by rapid increase around training-set ﬁtting,
and then eventual decrease. See Figure 5 for a horizontal cross-section.
3 Experiments
3.1 Model-Wise Grokking
Following the original grokking setting of Power et al. (2022), we train decoder-only transformers
(Vaswani et al., 2017) with causal attention masking on the binary operation of division mod 97
(details in Appendix B). We explore the effects of regulating effective model complexity by varying
parameter-count.
Figure 4 shows train and test loss with respect to optimization steps and embedding dimension. For a
range of values, delayed generalization occurs both when moving vertically (epoch-wise grokking),
as well as when moving horizontally (model-wise grokking). Figure 6 shows the corresponding
accuracy heatmaps, with clear double descent behavior both epoch-wise and model-wise. Figure 5
shows model-wise grokking with models trained for 400k epochs.
3.2 A Type 1 Pattern in the Grokking Setting
In the modular division setting of Power et al. (2022) the test accuracy is non-monotonic (Figure 1).
Early in training, the model learns that for allb, 0/b = 0 mod n. This pattern generalizes well and is
learned quickly, corresponding to a Type 1 pattern in our model. As predicted by our model, this leads
to an initial spike above chance in test accuracy. Interestingly, the development of poorly-generalizing
Type 2 features then leads to worse-than-chance performance on the rest of the data, likely due to
anti-correlation between train and test set values for every dividend and divisor in modular division,
causing a descent in test performance. This small bump is noticeable in Power et al. (2022), but not
noted by the authors. We validate this hypothesis experimentally (Figure 7).
4 Related Work
Pattern Learning at Different Speeds. Heckel & Yilmaz (2020) ﬁnd different parts of networks
learning at different speeds can cause two bias-variance trade-off curves with different minima,
leading to double descent in test error; they show that adjusting step-sizes of different layers can
align the learning curves and eliminate double descent behavior. They argue that epoch-wise
double descent occurs due to this difference in learning speed, as opposed to due to regulating
model complexity. Pezeshki et al. (2021) use a linear teacher-student model to demonstrate that
epoch-wise double descent can be explained by different patterns being learned at different speeds.
Stephenson & Lee (2021) experimentally demonstrate double descent can be avoided by removing
or accelerating slow-to-learn features. In this work, we extend this pattern learning framework
to interpret grokking behavior as well as double descent behavior, and propose a mathematical
model uniting both phenomena. Our framework uses the concept of distinct patterns with individual
strengths (Heckel & Yilmaz, 2020; Pezeshki et al., 2021), but is distinct in allowing for speciﬁc
4
```

## Batch 1: 2303.06173, PDF page 5

```text
0 10 20 30 40 50 60 70 80
Transformer embedding dimension
0.0
0.2
0.4
0.6
0.8
1.0Accuracy
train
test
0 10 20 30 40 50 60 70 80
Transformer embedding dimension
0
5
10
15
20Loss
train
test
Figure 5: Model-wise grokking, with each point a transformer of the corresponding embedding
dimension trained for 400K optimization steps. Lines are smoothed data via a Gaussian ﬁlter. Left:
Accuracy, with delayed generalization. Right: Loss, with a rise in test loss followed by a fast descent.
per-pattern generalization parameters and separating maximum predictiveness from learning speed,
as well as introducing the notion of a “preferred” pattern.
Double Descent. The double descent phenomenon describes a phenomenon in which model test
performance initially improves, then worsens as the model overﬁts, and then eventually improves
again as we increase the capacity of our training procedure (Belkin et al., 2018). This capacity
measure was originally demonstrated with model size (model-wise); Nakkiran et al. (2021) generalize
the capacity notion in effective model complexity, and show double descent can occur when varying
the number of optimization steps (epoch-wise) and other forms of capacity modulation.
Grokking. Grokking was ﬁrst demonstrated by Power et al. (2022), who state that grokking is
distinct from double descent because generalization occurs far past the interpolation threshold. Liu
et al. (2022) demonstrate that grokking generalization speed can be accelerated in a simple embedding-
decoder model by using a larger learning rate for the embedding than for the decoder. This is in
line with ﬁndings by Heckel & Yilmaz (2020) on epoch-wise double descent, where decreasing
learning rates in later layers (which learn faster) aligns pattern learning speeds. We consider this
further evidence that both grokking and epoch-wise double descent occur as a result of similar
learning dynamics resulting from different speeds of pattern development. Nanda & Lieberum
(2022) investigate grokking through mechanistic interpretability, with ﬁndings in line with our results
(speciﬁcally observing the development of a Type 3 pattern).
Weight Decay Both Nakkiran et al. (2021) and Pezeshki et al. (2021) ﬁnd that weight decay acts
as a capacity constraint, resulting in both weight decay-wise double descent and preventing the
learning of slower features. In the grokking setting, however, weight decay plays a signiﬁcant role
in speeding up time to generalization (Power et al., 2022). We speculate that this occurs due to
weight decay hindering the memorization-based solutions, thus accelerating the development of the
better-generalizing solution.
5 Conclusion
In this work, we cover two phenomena in deep learning that were previously studied in isolation—
grokking and double descent—and argue that they are best understood as instances of the same
underlying learning dynamics.
The project of building a principled understanding of how and when networks generalize may be
especially important from the point of view of AGI safety, the problem of ensuring that advanced AI
systems are safe despite pursuing misaligned goals (Carlsmith, 2022; Bostrom, 2014) and incentives
to seek power or deceive human operators for instrumental reasons (Turner et al., 2021; Omohundro,
2008). A central problem is that we may need to be certain of the safety of a model before we scale
it to a capability level beyond which we cannot control it. Concerningly, it is well-known that the
out-of-distribution (OOD) generalization behavior of deep learning systems can be hard to control or
predict. A robust theory of generalization and learning in neural networks may be necessary to solve
this problem.
5
```

## Batch 2: 2210.01117, PDF page 2

```text
Published as a conference paper at ICLR 2023
w > wc
w wc
w < wc
large init
small init
fast
fast     slow
 (grokking)
generalizable 
   solutions
overfitting 
 solutions
weight space
(a)
wc
weight norm w
Loss
fast
slow (grokking)
test losstraining loss
large reg
small reg
no reg
large initsmall init
fast
Goldilocks zone (generalization) (b)
Figure 1: (a)w:L2 norm of model weights. Generalizing solutions (green stars) are concentrated
around a sphere in the weight space wherew≈wc (green). Overﬁtting solutions (orange) populate
thew & wc region. (b) The training loss (orange) and test loss (gray) have the shape of L and U,
respectively. Their mismatch in thew>w c region leads to fast-slow dynamics, resulting in grokking.
transfer to realistic datasets (MNIST, IMDb reviews and QM9), for which we also observe grokking,
although in a slightly non-standard setup where it is relatively weak. In Section 5, we discuss why
grokking is more dramatic for algorithmic datasets than on others (e.g., MNIST), by comparing their
loss landscapes. As a byproduct, we ﬁnd that training with constrained weight norm can almost
eliminate grokking. We review related work in Section 6 and summarize our conclusions in Section
7. Code is available at https://github.com/KindXiaoming/Omnigrok.
2 T HE LU MECHANISM FOR GROKKING
Weight norm and reduced loss Letting w denote the weights of a model, any functionf (w) (e.g,
train/test loss/accuracy) depends on both the weight norm w≡|| w||2 and the angular direction
ˆw≡ w/w. Similar to (Fort and Scherlis, 2019), we deﬁne a reduced function ˜f (w) by minimizing
training lossltrain(w) over angular directions, i.e.,
˜f (w)≡f (w∗(w)), where w∗(w)≡ argmin
||w||2=w
ltrain(w) (1)
In practice, we perform the constrained minimization by rescaling the model weights back to their
original norm after each unconstrained optimization step. We will see that this reduced 1D loss
landscape, which is easy to visualize, captures important features related to grokking. Throughout
the paper, our model is initialized by multiplying a factorα≡w/w0 to the standard initialization 1,
wherew0 andw are the weight norm of the network before and after multiplyingα.
LU mechanism Although the loss landscapes of neural networks are nonlinear, (Fort and Scherlis,
2019) reveal a simple landscape picture: There is a spherical shell in the weight space (the
"Goldilocks" zone), where generalization is better than outside this zone. We illustrate the Goldilocks
zone as the green area with average radius wc in Figure 1a; the green stars are the generalizing
solutions. The test loss is thus higher either both when w > wc andw < wc, forming a U-shape
againstw in Figure 1b (gray curve). By contrast, the training loss has an L-shape against weight
norm 2. There are many solutions which overﬁt training data for w >wc, but high training losses
are incurred forw<w c. This corresponds to the L-shaped curve seen in Figure 1b (orange curve,
no regularization). In summary, the (reduced) training loss and test loss are L-shaped and U-shaped
against weight norm, respectively, which we will refer to as the LU mechanism throughout the paper.
1The standard initialization means the default one in PyTorch.
2𝓁train(w) is non-increasing: One can always construct a larger network by adding useless non-zero weights
to a smaller network, without changing the functionality of the model.
2
```

## Batch 2: 2210.01117, PDF page 3

```text
Published as a conference paper at ICLR 2023
It is well known in statistics that generalization error has a "U" shape against model capacity, which
is usually attributed to the bias-variance trade-off. Although this common wisdom was challenged
by the observation of double descent (Nakkiran et al., 2021), the "U" curve can be recovered from a
double descent simply by changing the x-axis from the number of model parametersN to the 2-norm
of model parameters w≡|| w||2 (Ng and Ma, 2022). Although the LU mechanism may remind
readers of related phenomena (Schoenholz et al., 2016; Yang and Schoenholz, 2017; Nakkiran et al.,
2021), their setups are not exactly the same as ours. More importantly, our focus and contribution is
to understand grokking, a brand new generalization puzzle.
Grokking dynamics We identify the "LU mechanism" as the cause of grokking. If the weight norm is
initialized to be large (e.g., the black square in thew>w c region), the model ﬁrst quickly moves to a
nearby overﬁtting solution by minimizing the training loss. Without any regularization, the model will
stay where it is, because the gradient of the training loss is almost zero along the valley of overﬁtting
solutions, so generalization does not happen. Fortunately, there are usually explicit and/or implicit
regularizations that can drive the weight vector towards the Goldilocks zone w≈ wc. When the
regularization magnitude is non-zero but small, the radial motion can be (arbitrarily) slow. If weight
decay is the only source of regularization, and training loss is negligible after overﬁtting, then weight
decayγ causesw(t)≈ exp(−γt)w0, whenw0 >w c, so it takes timet≈ ln(w0/wc)/γ∝γ−1 to
generalize. A small γ results in a huge generalization delay (i.e., grokking). The dependence on
regularization magnitudes is illustrated in Figure 1b: no generalization at all happens for γ = 0 ,
smallγ leads to slow generalization (grokking), and large γ leads to faster generalization 3. The
above analysis only applies to large initializationsw>w c. Small initializationsw<w c can always
generalize fast 4, regardless of regularization.
Why isn’t grokking commonly observed? The standard initialization schemes typically initialize
w no larger thanwc. However, if we increase initialization scales (explicitly or implicitly), grokking
can appear. In Section 3 and 4, we ﬁnd that explicitly increasing initialization weight norm can induce
grokking. In Section 5, we argue for algorithmic datasets because (shown in Figure 6d)
wc(bad representation)>w c(good representation), (2)
i.e., a proper initialization for a bad representation is effectively too large for a good representation,
leading to grokking. Take the addition (basep) for example: with the good (linear) representation
or a bad (random) representation, the decoder needs to learn to classify O(p) orO(p2) examples,
respectively.
3 G ROKKING FOR A TEACHER -STUDENT SETUP
10 1
 100 101
relative weight norm = w/w0
10 5
10 4
10 3
10 2
10 1
100
101
Loss
train
test
(a)
0.0
0.2
0.4
0.6
0.8
1.0
= 2.0
 Accuracy
= 0
train
test
101 102 103 104 105
steps
0.0
0.2
0.4
0.6
0.8
1.0
= 0.5
 Accuracy
= 0.03
101 102 103 104 105
steps
= 1
101 102 103 104 105
steps (b)
10 1
 100
weight decay 
103
104
Steps to acc>0.95 (t)
 train
test
t 1
 (c)
Figure 2: Teacher-student setup. α: student initialization scale, γ: weight decay. (a) The reduced
training loss and test loss have the shape of "L" and "U", respectively. (b) Top row: large initialization
(α = 2.0) can demonstrate no generalization (no reg), grokking (small reg) and fast generalization
(large reg). Bottom: small initialization (α = 0.5) always generalizes fast, regardless of weight deacy.
(c)α = 2. The steps to overﬁtting is independent of weight decay, while the steps to generalization
scale inversely with the weight decay.
To illustrate how the LU mechanism results in grokking, we employ a toy teacher-student setup. The
teacher and the student share the same architecture (a 5-100-100-5 MLP with tanh activation), but
3γ should not be too large, otherwise it will bring the weights to a trivial solution w = 0.
4w should not be too small to harm optimization.
3
```

## Batch 2: 2210.01117, PDF page 4

```text
Published as a conference paper at ICLR 2023
are initialized with different seeds. The student network is initialized with the standard initialization
(the default one in PyTorch) but each weight is rescaled by the same factorα≡w/w0, wherew0
andw are the weight norm of the student network before and after rescaling. The teacher network is
initialized standardly, i.e.,αteacher = 1. Inputs and outputs have dimensionsdin = 5 anddout = 5,
respectively. We generateNtrain = 100 training andNtest = 100 test samples by ﬁrst drawing inputs
from the standard Gaussian distributionN (0, Idin×din ), and then feed the input data to the teacher
to generate output labels. The student network is trained with the Adam optimizer (learning rate
3× 10−4) for 105 steps.
LU landscapes Firstly, we compute the reduced losses by minimizing the training loss (excluding
weight decay) while constraining the weight norm of the student network to be constant. We treat
the converging point after training as the global minimum on the spherical surface, which explicitly
deﬁnes the reduced losses ˜ltrain(α) and ˜ltest(α). As shown in Figure 2a, ˜ltest(α) ﬁrst decreases and
then increases asα increases, displaying a U-shape with a minimum atα≈ 1. By contrast, ˜ltrain(α)
decreases whenα< 1 and remains ﬂat near zero whenα≥ 1, forming an L-shape. When weight
decayγ is present, the training landscape becomes ˜ltrain(α,γ ) = ˜ltrain(α) +γα2C 2 whereC is the
average parameter magnitude determined by the standard initialization.
Training dynamics Our problem is a regression task, but we can imitate the behavior of a classiﬁca-
tion task by manually setting a thresholdθ = 0.01 and deﬁning a sample to be correctly “classiﬁed"
if the prediction error is less thanθ. We study the dynamics of training and test accuracy. We run
experiments with two initializationsα = 0.5 (small) andα = 2.0 (large), and three weight decays
γ = 0 (no reg),γ = 0.03 (small reg) andγ = 1 (large reg). As shown in Figure 2b (bottom), small
initialization runs always generalize fast regardless of regularization. Large initialization runs (top)
depended on weight decay: no regularization fails to generalize, small regularization generalizes
slowly (grokking), while large regularization generalizes faster.
For the large initializationα = 2.0, we do a ﬁner sweep ofγ in [0.03, 1]. We compute the number of
steps and weight normw when training or test accuracy reaches 95%. As shown in Figure 2c, the
time (number of steps) to reach 95% training accuracy is independent of weight decayγ, while the
time to reach 95% test accuracy is inversely proportional to the weight decay, as we derived above
for the LU mechanism.
4 O MNIGROK : G ROKKING FOR MORE INTERESTING TASKS
We now analyze loss landscapes and search for grokking for several more interesting datasets, and
see that the insights obtained from our toy model can transfer to these datasets. We report the main
results here, with experiment details included in Appendix A.
Image classiﬁcation We visualize loss landscapes of MNIST (Deng, 2012) to verify the LU mech-
anism, and study the dependence on training data size. Similar to the teacher-student case, we
reduce losses and errors (one minus accuracy) to two variables (weight normw and data sizeN) by
minimizing over angular directions of weights, i.e.,
˜ltrain(w,N )≡ltrain(w∗,N ), ˜ltest(w,N )≡ltest(w∗,N ), w∗(w,N )≡ argmin
||w||2=w
ltrain(w,N ), (3)
shown in Figure 3 (a)(b). The reduced loss landscape reveals three things: (1) Larger initializations
lead to grokking. Point A in Figure 3 corresponds to the standard initialization(α = 1), which has low
training and test errors, hence no grokking. When increasing the weight norm from A to B, training
error is seen to remain low while test error rises. To generalize, implicit or explicit regularization
such as weight decay then brings the weight norm down, leading to delayed generalization (grokking)
if regularization is small. (2) Larger datasets lead to de-grokking. Comparing B and C in Figure 3,
C is seen to have larger training size than B and lower test error. Larger data size N makes the
Goldilocks zone broader, reducing or eliminating grokking even for large weight initializations. (3)
Critical data size can be deﬁned. As reported in (Power et al., 2022; Liu et al., 2022), we see that
there exists a critical training set size below which generalization is impossible. The effective theory
analysis in (Liu et al., 2022) only applies to algorithmic datasets, but not to other datasets with
unknown optimal representations. The loss landscape analysis presented is this work can apply to all
supervised-learning tasks. As shown in Figure 3 (b), the contours of constant test error are thumb-like,
and the tip of the thumb determines the minimum amount of data required for generalization.
4
```

## Batch 2: 2210.01117, PDF page 5

```text
Published as a conference paper at ICLR 2023
10 1
 100 101
relative weight norm = w/w0
101
102
103
104
6 × 104
training data size N A B
C
grokking
degrokking
training error
0.1
0.1
0.2
0.3
0.4
0.0
0.2
0.4
0.6
0.8
1.0
(a)
10 1
 100 101
relative weight norm = w/w0
101
102
103
104
6 × 104
training data size N A B
C
grokking
degrokking
test error
0.1
0.2
0.3
0.4
 0.0
0.2
0.4
0.6
0.8
1.0 (b)
0.1 1 10
0.0
0.2
0.4
0.6
0.8error
data size = 200
A
B
test
train
0.1 1 10
relative weight norm = w/w0
0.0
0.2
0.4
0.6
0.8error
data size = 8000
C
test
train (c)
102 103 104 105
Optimization Steps
0.25
0.50
0.75
1.00
Accuracy
MNIST Grokking With Varying , 1000 Train Points, =1e-4
train
test
 2
4
6
8
10
Initialization Scale 
(d)
0 5000 10000 15000 20000 25000 30000
Train Points
104
105
Steps to Test Accuracy > 60%
Steps until generalization for MNIST (weight decay 5e-3)
Mean
Runs that didn't reach 60% test acc in 10^5 steps
Runs that reached 60% test acc in 10^5 steps (e)
Figure 3: MNIST. (a) reduced training error, (b) reduced test error. Comparing A and B: larger weight
norm makes learning grok (delay generalization). Comparing B and C: a larger training data size
makes learning de-grok (speed up generalization). (c) "LU" holds truer for smaller data. (d) Accuracy
curves for MNIST in the setting where we observe grokking. (e) Time to generalize as a function of
training set sizeN.
0.1 1.0 10.0
relative weight norm = w/w0
102
103
104
5 × 104
data size N
training error
0.20
0.20
0.25
0.25
0.25
0.05
0.10
0.15
0.20
0.25
0.30
0.35
0.40
(a)
0.1 1.0 10.0
relative weight norm = w/w0
102
103
104
5 × 104
data size N
test error
0.20
0.25
0.20
0.25
0.30
0.35
0.40
0.45 (b)
0.1 1 10
0.0
0.1
0.2
0.3
0.4
0.5error
data size = 1k
test
train
0.1 1 10
relative weight norm = w/w0
0.0
0.1
0.2
0.3
0.4
0.5error
data size = 50k
test
train (c)
100 101 102 103 104 105
steps
0.4
0.6
0.8
1.0accuracy
= 6
100 101 102 103 104 105
steps
0.4
0.6
0.8
1.0accuracy
= 1
train
test (d)
Figure 4: We use an LSTM to predict IMDb reviews. (a) training error; (b) test error; (c) reduced
losses for data size 1k (top) and 50k (bottom); (d) With 1k data, a (weak) grokking signal is observed
for large initializations (α = 6), while no grokking is observed for standard initializations (α = 1).
Guided by the landscape analysis, we make two nonstandard decisions to induce grokking on MNIST:
(1) we reduce the size of the training set from 60k to 1k samples (by taking a random subset) and
(2) we increase the scale of the weight initialization distribution (by multiplying the initial weights,
sampled with Kaiming uniform initialization, by a constantα> 1). With these modiﬁcations to the
training set size and initialization scale, we train a depth-3 width-200 MLP with ReLU activations
with the AdamW optimizer using MSE loss with one-hot targets. We ﬁnd that the network quickly
ﬁts the training set, and test accuracy improves much later, as shown in Figure 3d, just as in the
stereotypical grokking learning ﬁrst observed in algorithmic datasets. Figure 3e shows the effect of
training set size on time to generalization for MNIST. We ﬁnd a result similar to what (Power et al.,
2022) observed, namely that generalization time increases rapidly once one approaches a certain
critical data set size. We also include the learning phase diagram in Appendix ??.
Sentiment analysis of text We look for grokking using LSTMs (Hochreiter and Schmidhuber, 1997)
for IMDb dataset (Maas et al., 2011). Similar to Eq. (3), we reduce training and test losses to depend
5
```

## Batch 2: 2210.01117, PDF page 6

```text
Published as a conference paper at ICLR 2023
0.1 1 10
relative weight norm = w/w0
101
102
103
104
data size N
training loss
0.05
0.10
0.0
0.1
0.2
0.3
0.4
0.5
(a)
0.1 1 10
relative weight norm = w/w0
101
102
103
104
data size N
test loss
0.1
0.2
0.2
0.0
0.1
0.2
0.3
0.4
0.5 (b)
0.1 1 10
10 3
10 2
10 1
100
101
102
103
MSE
data size = 100
test
train
0.1 1 10
relative weight norm = w/w0
10 3
10 2
10 1
100
101
102
103
MSE
data size = 3000
test
train (c)
100 101 102 103 104 105
steps
10 3
10 1
101
MSE
= 1
test
train
100 101 102 103 104 105
10 3
10 1
101
MSE
= 3
 (d)
Figure 5: We use a GCNN to predict isotropic polarizability of molecules in the QM9 dataset. (a)
training loss; (b) test loss; (c) reduced losses for data size 100 (top) and 3000 (bottom); (d) with 200
training samples, grokking is observed for large initialization (α = 3), while no grokking is observed
for standard initializations (α = 1).
on only the weight normw and data sizeN. We show the reduced training and test error in Figure 4
(a)(b). For large data size say the full dataset, training and test errors have similar "U" shapes5, so one
cannot create grokking via the "LU" mechanism. For small data size, say 1k, however, the mismatch
between training and test errors makes it possible to create grokking via large initializations. In
Figure 4 (c), we initialize weights larger (α = 6) with weight decay 1, overﬁtting is complete within
102 steps, but generalization does not start until around 103 steps. Note that the generalization "jump"
is not as sharp as on algorithmic datasets (Power et al., 2022) or MNIST, but at least generalization
is delayed here. By contrast, if we use the standard initialization ( α = 1 ) with no weight decay,
generalization happens early on during training, and does not improve much after overﬁtting.
Molecules We search for grokking using the graph convolutional neural network (GCNN) for QM9
dataset (Ramakrishnan et al., 2014). Similar to Eq. (3), we deﬁne the reduced training/test losses,
which are only dependent on weight normw and data sizeN. As shown in Figure 5(a)(b), when data
size is large, training and test losses have similar "U" shapes, hence grokking is impossible via the
"LU mechanism". When data size is small, training and test losses mismatch somewhere in the region
α =w/w0 > 1, making grokking possible. Indeed, shown in Figure 5(d), there is a sharp drop in test
loss around 104 steps if initialization is 3 times larger than standard, while standard initialization does
not lead to grokking. Note that zero weight decay is applied in both cases, implying the existence of
implicit regularizations.
5 R EPRESENTATION IS KEY TO GROKKING
In Section 4, we showed that increasing initialization scales can make grokking happen for standard
ML tasks. However, this seems a bit artiﬁcial and does not explain why standard initialization
leads to grokking on algorithmic datasets, but not on standard ML datasets, say MNIST. The key
difference is how much the task relies on representation learning. For the MNIST dataset, the
quality of representation determines whether the test accuracy is 95% or 100%; by constrast in
algorithmic datasets, the quality of representation determines whether test accuracy is random guess
(bad representation) or 100% (good representation). So overﬁtting (under a bad representation)
has a more dramatic effect on algorithmic datasets, i.e., the model weights increase quickly during
overﬁtting but test accuracy remains low. During overﬁtting, model weight norm is much larger than
at initialization, but then drops below the initialization norm when the model generalizes, shown
in Figure 7a, and also observed by (Nanda et al., 2023). As a byproduct, we are able to eliminate
grokking by constraining the model on a small weight norm sphere, shown in Figure 7b.
In the following, we will compare algorithmic datasets (Section 5.1) to MNIST (Section 5.2). We
show how their loss landscapes depend on representations differently, and how the difference leads to
different outcomes (grokking or not).
5In principle, reduced training losses should be non-increasing ("L"), but optimization issues may occur for
too large initializations (Schoenholz et al., 2016).
6
```

## Batch 2: 2309.02390, PDF page 2

```text
Explaining grokking through circuit efficiency
Train loss T est lossT est accuracy
0 5 10
Epochs 1e3
101
10 2
10 5
Loss
0
1
(a) Grokking. The original be-
haviour from Power et al. (2021).
We train on a dataset with𝐷≫
𝐷crit. As a result,𝐶genis strongly
preferred to𝐶memat convergence,
and we observe a transition to very
low test loss (100% test accuracy).
101 103 105
Epochs
101
10 2
10 5
0
1
(b) Ungrokking. If we take a net-
work that has already grokked and
train it on a new dataset with𝐷 <
𝐷crit, the network reverts to signif-
icant memorisation, leading to a
transition back to poor test loss.
(Note the log scale for the x-axis.)
0 2
Epochs 1e7
101
10 2
10 5
0
1
Accuracy
(c) Semi-grokking. When 𝐷 ∼
𝐷crit, the memorising algorithm
and generalising algorithm com-
pete with each other at conver-
gence, so we observe a transition
to improved but not perfect test
loss (test accuracy of 83%).
Figure 1| Novel grokking phenomena.When grokking occurs, we expect there are two algorithms
thatperformwellattraining: “memorisation”( 𝐶mem, withpoortestperformance)and“generalisation”
(𝐶gen, with strong test performance). Weight decay strengthens𝐶genover𝐶memas the training dataset
size increases. By analysing the point at which𝐶genand𝐶memare equally strong (the critical dataset
size 𝐷crit), we predict and confirm two novel behaviours:ungrokking and semi-grokking.
its efficiency should decrease as training dataset size increases. We validate these predictions by
quantifying efficiencies for various dataset sizes for both𝐶memand𝐶gen.
This suggests that there exists a crossover point at which𝐶genbecomes more efficient than𝐶mem,
which we call the critical dataset size𝐷crit. By analysing dynamics at𝐷crit, we predict and demonstrate
two new behaviours (Figure 1). Inungrokking, a model that has successfully grokked returns to poor
test accuracy when further trained on a dataset much smaller than𝐷crit. Insemi-grokking, we choose
a dataset size where𝐶genand𝐶memare similarly efficient, leading to a phase transition but only to
middling test accuracy.
We make the following contributions:
1. We demonstrate the sufficiency of three ingredients for grokking through a constructed simula-
tion (Section 3).
2. By analysing dynamics at the “critical dataset size” implied by our theory, wepredict two novel
behaviours: semi-grokking and ungrokking (Section 4).
3. Weconfirmourpredictionsthroughcarefulexperiments, includingdemonstratingsemi-grokking
and ungrokking in practice (Section 5).
2. Notation
We consider classification using deep neural networks under the cross-entropy loss. In particular, we
are given a set of inputs𝑋, a set of labels𝑌, and a training dataset,D ={(𝑥1,𝑦∗1),... (𝑥𝐷,𝑦∗𝐷)}.
For an arbitrary classifierℎ : 𝑋×𝑌→ ℝ, the softmax cross entropy loss is given by:
Lx-ent(ℎ) =− 1𝐷 ∑︁(𝑥,𝑦∗)∈D log exp(ℎ(𝑥,𝑦∗))˝𝑦′∈𝑌 exp(ℎ(𝑥,𝑦′)). (1)
The output of a classifier for a specific class is the classlogit, denoted by𝑜𝑦ℎ(𝑥) B ℎ(𝑥,𝑦). When the
2
```

## Batch 2: 2309.02390, PDF page 3

```text
Explaining grokking through circuit efficiency
input 𝑥 is clear from context, we will denote the logit as𝑜𝑦ℎ. We denote the vector of the logits for all
classes for a given input asﬁ𝑜ℎ(𝑥) orﬁ𝑜ℎ when 𝑥 is clear from context.
Parametric classifiers (such as neural networks) are parameterised with a vector𝜃 that induces
a classifierℎ𝜃. The parameter norm of the classifier is𝑃ℎ𝜃 B∥𝜃∥. It is common to addweight decay
regularisation, which is an additional loss termLwd(ℎ𝜃) = 12(𝑃ℎ𝜃)2. The overall loss is given by
L(ℎ𝜃) =Lx-ent(ℎ)+ 𝛼Lwd(ℎ𝜃), (2)
where𝛼 is a constant that trades off between softmax cross entropy and weight decay.
Circuits. Inspired by Olah et al. (2020), we use the termcircuit to refer to an internal mechanism by
which a neural network works. We only consider circuits that map inputs to logits, so that a circuit𝐶
induces a classifierℎ𝐶 for the overall task. We elide this distinction and simply write𝐶 to refer toℎ𝐶,
so that the logits are𝑜𝑦𝐶, the loss isL(𝐶), and the parameter norm is𝑃𝐶.
For any given algorithm, there exist multiple circuits that implement that algorithm. Abusing
notation, we use𝐶gen(𝐶mem) to refer either to thefamily of circuits that implements the generalising
(memorising) algorithm, or a single circuit from the appropriate family.
3. Three ingredients for grokking
Given a circuit with perfect training accuracy (as with a pure memorisation approach like𝐶memor a
perfectly generalising solution like𝐶gen), the cross entropy lossLx-ent incentivises gradient descent
to scale up the classifier’s logits, as that makes its answers more confident, leading to lower loss (see
Theorem D.1). For typical neural networks, this would be achieved by making the parameters larger.
Meanwhile, weight decayLwd pushes in the opposite direction, directly decreasing the parameters.
These two forces must be balanced at any local minimum of the overall loss.
When we havemultiple circuits that achieve strong training accuracy, this constraint applies to
each individually. But how will they relate to each other? Intuitively, the answer depends on the
efficiencyof each circuit, that is, the extent to which the circuit can convert relatively small parameters
into relatively large logits. For more efficient circuits, theLx-ent force towards larger parameters is
stronger, and theLwd force towards smaller parameters is weaker. So, we expect that more efficient
circuits will be stronger at any local minimum.
Given this notion of efficiency, we can explain grokking as follows. In the first phase,𝐶memis
learned quickly, leading to strong train performance and poor test performance. In the second phase,
𝐶genis now learned, and parameter norm is “reallocated” from𝐶memto𝐶gen, eventually leading to a
mixture of strong𝐶genand weak𝐶mem, causing an increase in test performance.
This overall explanation relies on the presence of three ingredients:
1. Generalising circuit:There are two families of circuits that achieve good training performance:
a memorising family𝐶memwith poor test performance, and a generalising family𝐶genwith good
test performance.
2. Efficiency:𝐶genis more “efficient” than𝐶mem, that is, it can produce equivalent cross-entropy
loss on the training set with a lower parameter norm.
3. Slow vs fast learning:𝐶genis learned more slowly than𝐶mem, such that during early phases of
training𝐶memis stronger than𝐶gen.
To illustrate the sufficiency of these ingredients, we construct a minimal example containing all
three ingredients, and demonstrate that it leads to grokking. We emphasise that this example is to be
3
```

## Batch 2: 2309.02390, PDF page 4

```text
Explaining grokking through circuit efficiency
treated as a validation of the three ingredients, rather than as a quantitative prediction of the dynamics
of existing examples of grokking. Many of the assumptions and design choices were made on the
basis of simplicity and analytical tractability, rather than a desire to reflect examples of grokking
in practice. The clearest difference is that𝐶genand 𝐶memare modelled as hardcoded input-output
lookup tables whose outputs can be strengthened through learned scalar weights, whereas in existing
examples of grokking𝐶genand𝐶memare learned internal mechanisms in a neural network that can be
strengthened by scaling up the parameters implementing those mechanisms.
Generalisation. To model generalisation, we introduce a training datasetD and a test datasetDtest.
𝐶genis a lookup table that produces logits that achieve perfect train and test accuracy.𝐶memis a lookup
table that achieves perfect train accuracy, but makes confident incorrect predictions on the test dataset.
We denote byDmem the predictions made by𝐶memon the test inputs, with the property that there is
no overlap betweenDtest andDmem. Then we have:
𝑜𝑦𝐺(𝑥) = 𝟙[(𝑥,𝑦)∈D or(𝑥,𝑦)∈D test]
𝑜𝑦𝑀(𝑥) = 𝟙[(𝑥,𝑦)∈D or(𝑥,𝑦)∈D mem]
Slow vs fast learning.To model learning, we introduceweights for each of the circuits, and use
gradient descent to update the weights. Thus, the overall logits are given by:
𝑜𝑦(𝑥) =𝑤𝐺𝑜𝑦𝐺(𝑥)+ 𝑤𝑀𝑜𝑦𝑀(𝑥)
Unfortunately, if we learn𝑤𝐺 and 𝑤𝑀 directly with gradient descent, we have no control over the
speedat which the weights are learned. Inspired by Jermyn and Shlegeris (2022), we instead compute
weights as multiples of two “subweights”, and then learn the subweights with gradient descent.
More precisely, we let𝑤𝐺 = 𝑤𝐺1𝑤𝐺2 and 𝑤𝑀 = 𝑤𝑀1𝑤𝑀2, and update each subweight according to
𝑤𝑖←𝑤𝑖−𝜆·𝜕L/𝜕𝑤𝑖. The speed at which the weights are strengthened by gradient descent can then
be controlled by the initial values of the weights. Intuitively, the gradient towards the first subweight
𝜕L/𝜕𝑤1 depends on the strength of the second subweight𝑤2 and vice-versa, and so low initial values
lead to slow learning. At initialisation, we set𝑤𝐺1 = 𝑤𝑀1 = 0 to ensure the logits are initially zero,
and then set𝑤𝐺2 << 𝑤𝑀2 to ensure𝐶genis learned more slowly than𝐶mem.
Efficiency.Above, we operationalised circuit efficiency as the extent to which the circuit can convert
relatively small parameters into relatively large logits. When the weights are all one, each circuit
produces a one-hot vector as its logits, so their logit scales are the same, and efficiency is determined
solely by parameter norm. We define𝑃𝐺 and 𝑃𝑀 to be the parameter norms when weights are all one.
Since we want𝐶gento be more efficient than𝐶mem, we set𝑃𝐺 < 𝑃𝑀.
This still leaves the question of how to model parameter norm when the weights are not all one.
Intuitively, increasing the weights corresponds to increasing the parameters in a neural network to
scale up the resulting outputs. In a𝜅-layer MLP with Relu activations and without biases, scaling
all parameters by a constant𝑐 scales the outputs by𝑐𝜅. Inspired by this observation, we model the
parameter norm of𝑤𝐺𝐶𝐺 as𝑤1/𝜅𝐺 𝑃𝑖 for some𝜅 >0, and similarly for𝑤𝑀𝐶𝑀.
Theoretical analysis.We first analyse the optimal solutions to the setup above. We can ignore the
subweights, as they only affect the speed of learning:Lx-ent andLwd depend only on the weights, not
subweights. Intuitively, to get minimal loss, we must assign higher weights to more efficient circuits –
but it is unclear whether we should assignno weight to less efficient circuits, or merely smaller but
still non-zero weights. Theorem D.4 shows that in our example, both of these cases can arise: which
one we get depends on the value of𝜅.
4
```

## Batch 2: 2309.02390, PDF page 5

```text
Explaining grokking through circuit efficiency
Train loss T est loss Gen logit Mem logit Parameter norm
0 5 10
Steps 1e3
101
100
10 1
10 2
Loss
0
5
10
(a) All three ingredients.
When 𝐶genis more efficient than
𝐶membut learned slower, we
observe grokking.𝐶genonly starts
to grow significantly by step 2500,
and then substitutes for 𝐶mem.
Total parameter norm falls due to
𝐶gen’s higher efficiency.
0 5 10
Steps 1e3
101
100
10 1
10 2
Loss
0
5
10
(b) 𝐶genless efficient than𝐶mem.
We set𝑃𝐺 > 𝑃𝑀. Since𝐶genis now
less efficient and learned slower,
it never grows, and test loss stays
high due to𝐶memthroughout train-
ing.
0 5 10
Steps 1e3
101
100
10 1
10 2
Loss
0
5
10
(c) 𝐶genand 𝐶memlearned at
equal speeds.We set𝑤𝐺1 = 𝑤𝑀1
so they are learned equally quickly.
𝐶genis prioritised at least as much
as𝐶memthroughout training, due
to its higher efficiency. Thus,
test loss is very similar to train
loss throughout training, and no
grokking is observed.
Figure 2| 𝐶genmust be learned slowly for grokking to arise.We learn weights𝑤𝑀 and𝑤𝐺 through
gradient descent on the loss in Equation D.1. To model the fact that𝐶genis more efficient than𝐶mem,
we set𝑃𝑀 > 𝑃𝐺. We see that we only get grokking when𝐶genis learned more slowly than𝐶mem.
Experimental analysis.We run our example for various hyperparameters, and plot training and
test loss in Figure 2. We see that when all three ingredients are present (Figure 2a), we observe
the standard grokking curves, with a delayed decrease in test loss. By contrast, when we make the
generalising circuit less efficient (Figure 2b), the test loss never falls, and when we remove the slow
vs fast learning ingredient (Figure 2c), we see that test loss decreases immediately. See Appendix C
for details.
4. Why generalising circuits are more efficient
Section 3 demonstrated that grokking can arise when𝐶genis more efficient than𝐶mem, but left open
the question ofwhy 𝐶genis more efficient. In this section, we develop a theory based on training
dataset size𝐷, and use it to predict two new behaviours:ungrokking and semi-grokking.
4.1. Relationship of efficiency with dataset size
Consider a classifierℎD obtained by training on a datasetD of size𝐷 with weight decay, and a
classifierℎD′ obtained by training on the same dataset with one additional point:D′ =D∪{( 𝑥,𝑦∗)}.
Intuitively,ℎD′ cannot bemore efficient thanℎD: if it was, thenℎD′ would outperformℎD even on
justD, since it would get similarLx-ent while doing better by weight decay. So we should expect that,
on average, classifier efficiency is monotonically non-increasing in dataset size.
How does generalisation affect this picture? Let us suppose thatℎD successfully generalises to
predict 𝑦∗ for the new input𝑥. Then, as we move fromD toD′,Lx-ent(ℎD) likely does not worsen
with this new data point. Thus, we could expect to see the same classifier arise, with the same average
logit value, parameter norm, and efficiency.
Now supposeℎD instead fails to predict the new data point(𝑥,𝑦∗). Then the classifier learned for
5
```

## Batch 2: 2310.06110, PDF page 2

```text
Published as a conference paper at ICLR 2024
(a)
100 101 102 103 104 105
Epochs
0.0
0.1
0.2
0.3
0.4
0.5
0.6
0.7
Loss
Network Train Loss
Network T est Loss
Lazy Network T est Loss
NTK Regression T est Loss (b)
100 101 102 103 104 105
Epochs
0.012
0.014
0.016
0.018
0.020
NTK Alignment
NTK Alignment
Parameter weight norm
300
400
500
600
700
800
900
1000
Parameter weight norm (c)
Figure 1: (a) Claimed parameter dynamics during grokking in a parameter space of R3 for
illustrative purposes. S(X, w0) is an affine subspace of parameter space reachable by models
linearized around w0. (b) Grokking on a polynomial regression task introduced in Section 5 with an
MLP, vanilla GD, and zero regularization. Green and blue loss curves in (b) correspond to sketched
green and blue parameter dynamics in (a). Horizontal line (black) in (b) is the mean-squared error
of best kernel regression estimate with the NTK at initialization. (c) The fact that parameter weight
norm increases (dashed orange) cannot be explained by any existing theories of grokking. Features
get aligned (grey) in a way we make precise in Section 5.
data without adapting its internal representations (Chizat et al., 2019). In this regime, the network
behaves as a linearized model with features evaluated at initialization (Jacot et al., 2018; Chizat
et al., 2019; Lee et al., 2019) 1. We show that grokking can arise when a network begins fitting
and “memorizing” its training set (albeit imperfectly) in the linearized regime, then later adapts its
features to the data, leading to improved generalization at late time.
We illustrate this idea schematically in Figure 1(a). Suppose we randomly initialize a network with
the parameters w0. When linearized around w0, under gradient descent, a neural network’s weights
are restricted to an affine subspace spanned by initial gradients w0 + span{∇wf (w, xµ)|w0 }Pµ=1,
and gradient descent finds a training minimizer on this subspace,wlazy. For MSE loss this minimizer
is the kernel regression solution with the network’s initial Neural Tangent Kernel (NTK) (Jacot et al.,
2018; Lee et al., 2019). Alternatively, if the network leaves the linearized regime, the weights can
leave the subspace of the linear model and converge to another solution wfeature. We hypothesize
that grokking can occur when a network transitions from initially tracking the linearized network
dynamics in the subspace to more complicated dynamics that approach wfeature off of the subspace
which achieves better generalization because it learns features.
Given a fixed dataset where grokking is possible, our proposal naturally suggests two key factors
that control grokking: (1) how much feature learning is necessary for good performance, and (2)
how fast these features are learned. We introduce two parameters corresponding to these notions
and demonstrate they can control grokking.
The key contributions in this paper are the following:
• We give simple examples of a two-layer MLP without any weight decay that exhibits grokking
in ways inconsistent with existing theories of grokking.
• We demonstrate with both theory and experiments that grokking in this setting is associated with
the transition from lazy training to a rich, feature learning regime, and can be tuned by parameters
that control this transition. These parameters are:
– A scale parameter, α, that controls the magnitude of the output of the network, and thus the
rate of feature learning throughout training (ie. laziness).
– The task-model kernel alignment between the neural tangent kernel (NTK) of the network at
initialization and the test labels, a measure of how much feature learning is necessary for good
performance on the task (Cortes et al., 2012).
1We use the terms “lazy,” “kernel regime” and “linearized model” interchangeably to refer to the same
phenomenon where the network learns without changing its internal features. Concretely, this is a regime
where the network output f can move a large amount while ∇wf stays approximately constant.
2
```

## Batch 2: 2310.06110, PDF page 3

```text
Published as a conference paper at ICLR 2024
– A “goldilocks” train set size so that generalization is possible but not immediate (for instance,
grokking is impossible in the infinite data limit where train loss perfectly tracks test loss).
• We provide multiple lines of evidence that the feature learning dynamics that give grokking in
this simple setup are also those at play during grokking in more complicated settings studied in
past work: on MNIST, with one-layer transformers, and with student-teacher networks. Given a
set of training inputs, we give a method to construct labels that can generate grokking.
2 R ELATED WORK
Grokking. Nanda et al. (2023) mechanistically interpret the algorithm learned during grokking for
modular addition tasks. We show in Section 6 that merely tuning the network output scaling/laziness
parameter α is alone sufficient to make grokking continuously vanish on the one-layer Transformer
used in that work. Thilak et al. (2022) argue that grokking is caused by an optimization anomaly of
adaptive optimizers. We find grokking with vanilla gradient descent, so this cannot be the cause of
grokking in the general case. While we show in experiments in 6 that parameters from our theory
control grokking with adaptive optimizers, we note in Appendix Section 14 that learning dynamics
in such settings are less well understood. Davies et al. (2023) point out that grokking and double
descent share similarities in dynamics, and are fundamentally about the speed at which patterns of
varying complexity are learned. This agrees with our argument that the network first learns patterns
in the data that a linearized model can do well on, then changes its features to learn the patterns that
generalize. Liu et al. (2022a) empirically find that parameter weight norm at initialization can con-
trol grokking, while Varma et al. (2023) propose a heuristic for cross-entropy training with weight
decay, suggesting that grokking arises from a “generalizing circuit” being favored over a “memoriz-
ing circuit.” Both papers rely on weight decay and weight norm decrease to explain grokking. How-
ever, we show examples of grokking with zero weight decay and an increase in parameter weight
norm during training. We comment more on relations to existing theories in Appendix Section 9.
Kernel dynamics and feature learning in a polynomial setting. The limiting behavior of neural
networks in the large width limit (under commonly used parameterizations) is a linear model with
the NTK as the kernel (Jacot et al., 2018). This has motivated investigations into the inductive biases
of kernel methods (Bordelon et al., 2020; Canatar et al., 2021), which have revealed that kernels are
strongly biased to explain training data using the top components of their eigenspectrum. While this
spectral bias can enable good generalization on some learning problems, target functions that are not
in the top eigenspaces of the kernel require a potentially much larger amount of data. Many papers
have proposed examples where neural networks can outperform kernels statistically by amplifying
task-relevant dimensions compared to task-irrelevant dimensions in the input space (Mei et al., 2018;
Paccolat et al., 2021; Refinetti et al., 2021). One example of such a problem that has attracted recent
attention is single or multi-index models where the target function is a polynomial that depends on
a small subset of the high dimensional inputs (Ba et al., 2022; Arnaboldi et al., 2023; Nichani et al.,
2022; Atanasov et al., 2022; Berthier et al., 2023; Bietti et al., 2022). The fact that feature-learning
neural networks can outperform kernels on these tasks suggests that they could be useful toy models
of grokking, especially if early training is close to linearized dynamics.
3 W EIGHT NORM AND WEIGHT DECAY CANNOT EXPLAIN GROKKING
Previous explanations of grokking rely on weight norm decreases at late time (Liu et al., 2022a;
Varma et al., 2023). In Figure 2, we show a simple example of a modular arithmetic task, which is a
common task under study in grokking (Power et al., 2022; Nanda et al., 2023; Gromov, 2023), with
a two-layer MLP trained without any weight decay (details in Appendix Section 8.3). Weight norm
of parameters increases during training (Figure 2(a)), so grokking cannot in general be explained by
theories of weight decay.
We will focus on the dynamics of grokking in the loss (Figure 2(b)), because loss, not accuracy,
guides training dynamics. Further, we show in Section 19 of the Appendix that accuracy curves
for regression tasks are misleading because they can be gamed by choice of metric. We use mean-
squared error (MSE) loss on this classification task to adhere to the convention for how grokking
was seen in modular arithmetic in Liu et al. (2022a); Gromov (2023). We show in Section 6 that our
results remain consistent across architectures, optimizers, and datasets out of the box.
3
```

## Batch 2: 2310.06110, PDF page 4

```text
Published as a conference paper at ICLR 2024
0 10000 20000 30000 40000 50000
Epochs
0
20
40
60
80
100Accuracy
Train accuracy
T est accuracy
Weight Norm
150
200
250
300
350
Weight Norm
(a) Accuracy Curves
0 10000 20000 30000 40000 50000
Epochs
0.00
0.01
0.02
0.03
0.04MSE
Train loss
T est loss (b) Loss Curves
0 20000 40000 60000 80000 100000
Epochs
0
20
40
60
80
100Accuracy
Train, = 0.5
Test, = 0.5
Train, = 1
Test, = 1
Train, = 1.5
Test, = 1.5
Train, = 2
Test, = 2
 (c) Sweep over α
Figure 2: (a) and (b) demonstrate accuracy and loss curves for grokking on a modular arithmetic task
that shows an increase in parameter weight norm during training. (c) is a sweep over the laziness
parameter α that we will introduce and provide a theory for, showcasing how it can continuously
control grokking.
While we gave the modular arithmetic task as a counterexample first because it is a common task
under study in grokking, we will focus on a polynomial regression task in the rest of the paper,
which we can analyze the dynamics of mathematically. We introduce that task in Section 5. Pa-
rameter weight norm in that example also increases as it groks, as visible in Figure 1 (c). These
inconsistencies motivate our study which results in two key parameters – network laziness and NTK
alignment – that we introduce. The effects of varying the first, α, are shown in Figure 2(c) and we
see it can make grokking more dramatic, or vanish entirely.
4 G ROKKING AS TRANSITION FROM LAZY TO RICH LEARNING
Grokking is often conceptualized as a network that first finds a memorizing solution which fits the
training set but not the test set, later converging to a generalizing solution. We hypothesize that the
“memorizing” solutions that have been documented in prior works on grokking are equivalent to
early-time lazy training dynamics . At late time, the linearized approximation breaks down as the
network extracts useful features and begins to “grok.”
We next briefly review and define the idea of lazy training regime of neural networks, and introduce
some key theoretical concepts that will play an important role in our discussion.
4.1 P RIMER ON LAZY LEARNING : L INEAR VS NONLINEAR TRAINING REGIMES
In the lazy training regime, a networkf (w, x) of inputs x and parameters w obey the approximation
f (w, x) ≈ f (w0, x) + ∇wf (w, x)|w0 · (w − w0). (1)
While this approximation is still capable of learning nonlinear functions of the input x, it is a linear
model in the trainable parameters w. It can thus be recast as a kernel method with the neural tangent
kernel K
K(x, x′) = ∇wf (w, x)|w0 · ∇wf (w, x′)|w0 (2)
evaluated at initialization. This holds for any linearized model trained with GD on any loss, though
some loss functions (e.g. cross-entropy) cause non-linear models to eventually deviate from their
linearization (Lee et al., 2019). Deep neural networks can approach this linearization in many ways:
• Large width: in commonly used parameterization and initialization schemes of neural networks,
increasing the network width improves the quality of this approximation Jacot et al. (2018); Lee
et al. (2019).
• Large initial weights: increasing the size of the initial weights also causes the network to behave
closer to linearized dynamics (Chizat et al., 2019). We argue that this explains why Liu et al.
(2022a) and Varma et al. (2023) observed an association between grokking and large initial
weight norm.
4
```

## Batch 2: 2310.06110, PDF page 5

```text
Published as a conference paper at ICLR 2024
• Label rescaling: scaling y by factor α−1 can induce lazy training (Geiger et al., 2020).
• Output rescaling: multiplying the network output logits by a large scale factor α can also induce
lazy training (Chizat et al., 2019).
In this work, we primarily use the last option, where the α → ∞limit is one where equation 1
becomes exact and the network behaves at inference-time like a linear model (in the case of MSE,
this linear model is kernel regression with the initial NTK). In Figure 7, we show that these methods
of inducing laziness are equivalent in inducing grokking.
Inductive bias of kernels and deficiency of kernels on misaligned tasks:Though linearized mod-
els around the initial weights can perform well on some learning tasks, they do not generalize well
when trained on target functions y(x) which are misaligned to the NTK, in a sense we make precise
when we define centered-kernel alignment (CKA) in the next section. By contrast, neural networks
in the feature learning regime can adapt their internal representations to improve the sample com-
plexity of learning for functions that would be difficult for the NTK (Ghorbani et al., 2019; Arnaboldi
et al., 2023; Ba et al., 2022; Damian et al., 2023).
5 P OLYNOMIAL REGRESSION IN A TWO LAYER PERCEPTRON
To illustrate our main ideas, we study the simplest possible toy example of grokking: high dimen-
sional polynomial regression. This choice is motivated by known separation results between neural
networks and kernel methods. First, theoretical studies of kernel regression have demonstrated that
learning degree k polynomials in dimension D with the NTK requires P ∼ Dk samples (Borde-
lon et al., 2020; Canatar et al., 2021; Xiao et al., 2022). On the other hand, in the feature learning
regime, two-layer networks trained in the online setting can learn high-degree polynomials with
P ∼ D samples (Saad and Solla, 1995; Engel, 2001; Goldt et al., 2019; Arnaboldi et al., 2023;
Berthier et al., 2023; Sarao Mannelli et al., 2020). This indicates that neural networks can poten-
tially generalize for D ≪ P ≪ Dk, but only if they learn features (Atanasov et al., 2022). We
therefore predict the possibility of grokking in this intermediate range of sample sizes, especially if
feature learning occurs late in training, as in a lazy network. We indeed find we can induce grokking
this way on a two-layer network. In fact, grokking persists even with readout weights of the 2 layer
MLP fixed to 1, so in seeking a minimal setting reproducing grokking, this is what we study 2. This
type of two-layer NN is referred to as a committee machine (Saad and Solla, 1995).
The model f (w, x) and target function y(x) are defined in terms of input x ∈ RD as
f (w, x) = αN
NX
i=1
ϕ(wi · x) , ϕ (h) = h + ϵ2 h2 , y (x) = 12 (β⋆ · x)2 (3)
The value of α controls the scale of the output, and consequently the speed of feature learning.
The value of ϵ alters how difficult the task is for the initial NTK. We consider training on a fixed
dataset {(xµ, yµ)}Pµ=1 of P samples. The inputs x are drawn from an isotropic Gaussian distribution
x ∼ N(0, 1D I). It will be convenient to introduce the following two summary statistics
¯w = 1N
NX
i=1
wi ∈ RD , M = 1N
NX
i=1
wiw⊤i ∈ RD×D (4)
Using these two moments of the weights, the neural network function can be written as f (x) =
α ¯wx + αϵ2 x⊤M x. Further, the NTK can also be expressed as
K(x, x′) = x · x′ + ϵ(x · x′) ¯w · (x + x′) + ϵ2(x · x′) x⊤M x′ (5)
At initialization in a wide network, ¯w = 0 and M = I. Diagonalizing this initial NTK with respect
to the Gaussian data distribution reveals that linear functions all have eigenvalue λlin = D−1 while
2The mechanism behind grokking in this setting is the same for training a full 2 layer MLP with readouts,
but the kernel is not only a function of ¯w, M. We discuss this in Appendix Section 11, but this is a technicality:
the same arguments and plots hold in ordinary two-layer MLPs in the way one would expect.
5
```

## Batch 2: 1711.05101, PDF page 2

```text
Published as a conference paper at ICLR 2019
on many popular image classiﬁcation datasets), Adam leads to worse results than SGD with
momentum (for which L2 regularization behaves as expected).
Weight decay is equally effective in both SGD and Adam. For SGD, it is equivalent to L 2
regularization, while for Adam it is not.
Optimal weight decay depends on the total number of batch passes/weight updates. Our
empirical analysis of SGD and Adam suggests that the larger the runtime/number of batch
passes to be performed, the smaller the optimal weight decay.
Adam can substantially beneﬁt from a scheduled learning rate multiplier. The fact that Adam
is an adaptive gradient algorithm and as such adapts the learning rate for each parameter
does not rule out the possibility to substantially improve its performance by using a global
learning rate multiplier, scheduled, e.g., by cosine annealing.
The main contribution of this paper is to improve regularization in Adam by decoupling the weight
decay from the gradient-based update. In a comprehensive analysis, we show that Adam generalizes
substantially better with decoupled weight decay than with L2 regularization, achieving 15% relative
improvement in test error (see Figures 2 and 3); this holds true for various image recognition datasets
(CIFAR-10 and ImageNet32x32), training budgets (ranging from 100 to 1800 epochs), and learning
rate schedules (ﬁxed, drop-step, and cosine annealing; see Figure 1). We also demonstrate that our
decoupled weight decay renders the optimal settings of the learning rate and the weight decay factor
much more independent, thereby easing hyperparameter optimization (see Figure 2).
The main motivation of this paper is to improve Adam to make it competitive w.r.t. SGD with
momentum even for those problems where it did not use to be competitive. We hope that as a result,
practitioners do not need to switch between Adam and SGD anymore, which in turn should reduce
the common issue of selecting dataset/task-speciﬁc training algorithms and their hyperparameters.
2 D ECOUPLING THE WEIGHT DECAY FROM THE GRADIENT -BASED UPDATE
In the weight decay described by Hanson & Pratt (1988), the weightsθ decay exponentially as
θt+1 = (1−λ)θt−α∇ft(θt), (1)
whereλ deﬁnes the rate of the weight decay per step and ∇ft(θt) is the t-th batch gradient to be
multiplied by a learning rateα. For standard SGD, it is equivalent to standard L2 regularization:
Proposition 1 (Weight decay = L2 reg for standard SGD). Standard SGD with base learning rateα
executes the same steps on batch loss functions ft(θ) with weight decay λ (deﬁned in Equation 1)
as it executes without weight decay onf regt (θ) = ft(θ) + λ′2‖θ‖22, withλ′ = λα.
The proofs of this well-known fact, as well as our other propositions, are given in Appendix A.
Due to this equivalence, L 2 regularization is very frequently referred to as weight decay, including
in popular deep learning libraries. However, as we will demonstrate later in this section, this equiva-
lence does not hold for adaptive gradient methods. One fact that is often overlooked already for the
simple case of SGD is that in order for the equivalence to hold, the L2 regularizerλ′ has to be set toλ
α, i.e., if there is an overall best weight decay value λ, the best value of λ′ is tightly coupled withthe learning rate α. In order to decouple the effects of these two hyperparameters, we advocate to
decouple the weight decay step as proposed by Hanson & Pratt (1988) (Equation 1).
Looking ﬁrst at the case of SGD, we propose to decay the weights simultaneously with the update
ofθt based on gradient information in Line 9 of Algorithm 1. This yields our proposed variant of
SGD with momentum using decoupled weight decay (SGDW). This simple modiﬁcation explicitly
decouplesλ andα (although some problem-dependent implicit coupling may of course remain as
for any two hyperparameters). In order to account for a possible scheduling of both α andλ, we
introduce a scaling factorηt delivered by a user-deﬁned procedureSetScheduleMultiplier (t).
Now, let’s turn to adaptive gradient algorithms like the popular optimizer Adam Kingma & Ba
(2014), which scale gradients by their historic magnitudes. Intuitively, when Adam is run on a loss
functionf plus L2 regularization, weights that tend to have large gradients inf do not get regularized
as much as they would with decoupled weight decay, since the gradient of the regularizer gets scaled
2
```

## Batch 2: 1711.05101, PDF page 3

```text
Published as a conference paper at ICLR 2019
Algorithm 1 SGD with L2 regularization and SGD with decoupled weight decay (SGDW) , both
with momentum
1: given initial learning rateα∈ I R, momentum factorβ1∈ I R, weight decay/L2 regularization factorλ∈ I R
2: initialize time step t ← 0, parameter vector θt=0 ∈ I Rn, ﬁrst moment vector mt=0 ← 0, schedule
multiplierηt=0∈ I R
3: repeat
4: t←t + 1
5: ∇ft(θt−1)← SelectBatch(θt−1) ⊿ select batch and return the corresponding gradient
6: gt←∇ft(θt−1) +λθt−1
7: ηt← SetScheduleMultiplier(t) ⊿ can be ﬁxed, decay, be used for warm restarts
8: mt←β1mt−1 +ηtαgt
9: θt← θt−1− mt −ηtλθt−1
10: until stopping criterion is met
11: return optimized parameters θt
Algorithm 2 Adam with L2 regularization and Adam with decoupled weight decay (AdamW)
1: givenα = 0.001,β 1 = 0.9,β 2 = 0.999,ϵ = 10 −8,λ∈ I R
2: initialize time stept← 0, parameter vector θt=0∈ I Rn, ﬁrst moment vector mt=0← 0, second moment
vector vt=0← 0, schedule multiplierηt=0∈ I R
3: repeat
4: t←t + 1
5: ∇ft(θt−1)← SelectBatch(θt−1) ⊿ select batch and return the corresponding gradient
6: gt←∇ft(θt−1) +λθt−1
7: mt←β1mt−1 + (1−β1)gt ⊿ here and below all operations are element-wise
8: vt←β2vt−1 + (1−β2)g2t
9: ˆmt← mt/(1−βt1) ⊿ β1 is taken to the power oft
10: ˆvt← vt/(1−βt2) ⊿ β2 is taken to the power oft
11: ηt← SetScheduleMultiplier(t) ⊿ can be ﬁxed, decay, or also be used for warm restarts
12: θt← θt−1−ηt
(
α ˆmt/(√ˆvt +ϵ) +λθt−1 )
13: until stopping criterion is met
14: return optimized parameters θt
along with the gradient of f. This leads to an inequivalence of L 2 and decoupled weight decay
regularization for adaptive gradient algorithms:
Proposition 2 (Weight decay⁄= L2 reg for adaptive gradients). LetO denote an optimizer that has
iteratesθt+1← θt−αMt∇ft(θt) when run on batch loss function ft(θ) without weight decay,
andθt+1← (1−λ)θt−αMt∇ft(θt) when run on ft(θ) with weight decay, respectively, with
Mt⁄=kI (wherek∈ R). Then, forO there exists no L2 coefﬁcientλ′ such that runningO on batch
lossf regt (θ) = ft(θ)+ λ′2‖θ‖22 without weight decay is equivalent to runningO onft(θ) with decay
λ∈ R+.
We decouple weight decay and loss-based gradient updates in Adam as shown in line 12 of Algo-
rithm 2; this gives rise to our variant of Adam with decoupled weight decay (AdamW).
Having shown that L 2 regularization and weight decay regularization differ for adaptive gradient
algorithms raises the question of how they differ and how to interpret their effects. Their equivalence
for standard SGD remains very helpful for intuition: both mechanisms push weights closer to zero,
at the same rate. However, for adaptive gradient algorithms they differ: with L 2 regularization, the
sums of the gradient of the loss function and the gradient of the regularizer (i.e., the L2 norm of the
weights) are adapted, whereas with decoupled weight decay, only the gradients of the loss function
are adapted (with the weight decay step separated from the adaptive gradient mechanism). With
L2 regularization both types of gradients are normalized by their typical (summed) magnitudes, and
therefore weights x with large typical gradient magnitude s are regularized by a smaller relative
amount than other weights. In contrast, decoupled weight decay regularizes all weights with the
same rate λ, effectively regularizing weights x with large s more than standard L 2 regularization
3
```

## Batch 3: 2201.02177, PDF page 8

```text
Figure 5: One of the binary operation tables presented to the networks that the network can perfectly
ﬁll in. Each symbol is represented as a letter in English, Hebrew, or Greek alphabet for reader’s
convenience. We invite the reader to guess which operation is represented here.
Algorithmically generated reasoning datasets like bAbI Weston et al. (2015) encourage work on
studying generalization in data-limited regime. Most results on such datasets however focus on a
point estimate of performance of a particular architecture or training technique, whereas our main
interest is in pointing out the change in generalization past the point where a particular architecture
can memorize the training data completely.
Neelakantan et al. (2015) has a “grok-like” learning curve on an algorithmic task, but it is related to
optimization difﬁculty, whereas our phenomenon is speciﬁcally about generalization.
In Saxton et al. (2019) they study generalization on procedurally generated math problems such as
arithmetic and differentiation, but for the most part these tasks are more involved than the simple
binary op problems we have studied and as such do not lend themselves to observing the kinds of
phenomena we describe in this paper, since they would require an extremely large number of samples
to master.
In Jiang et al. (2019) they studied a large number of generalization or complexity measures on
convolutional neural networks to see which, if any, are predictive of generalization performance.
They ﬁnd that ﬂatness based measures that aim to quantify the sensitivity of the trained neural network
to parameter perturbations are the most predictive. We conjectured that the grokking phenomena
8
```

## Batch 3: 2201.02177, PDF page 9

```text
we report in this work may be due to the noise from SGD driving the optimization to ﬂatter/simpler
solutions that generalize better and hope to investigate in future work whether any of these measures
are predictive of grokking.
Zhang et al. (2016) ﬁnds that neural networks of sizes typically used in deep learning can interpolate
arbitrary training data, and yet generalize when trained with semantically meaningful labels using
appropriate optimization procedures. Our work shows a related phenomenon where neural networks
can interpolate a small algorithmic training dataset without generalizing, but start generalizing when
trained with SGD for longer.
Nakkiran et al. (2019); Belkin et al. (2018) focus on the phenomenon of double descent in loss as
a function of model and optimization procedure capacity. They ﬁnd that the classical U-shaped
validation loss curve is followed in some settings (including neural network training) by a second
descent of loss that starts around the minimal capacity that is needed to interpolate any training data.
We observe a second descent in validation loss (though not accuracy) as a function of the amount of
training in some of our experiments, and it happens past the point of interpolating the training data.
We believe that the phenomenon we describe might be distinct from the double descent phenomena
described in Nakkiran et al. (2019); Belkin et al. (2018) because we observe the second descent
in loss far past the ﬁrst time the training loss becomes very small (tens of thousands of epochs in
some of our experiments), and we don’t observe a non-monotonic behavior of accuracy. The setting
of small algorithmic datasets that we study also provides a smaller, more tractable playground for
studying subtle generalization phenomena than natural datasets studied in Nakkiran et al. (2019).
A.4 G ENERALIZATION WITH MEMORIZING SEVERAL OUTLIERS
Figure 6: Effect on data efﬁciency of introducingk∈ [0, 10, 100, 1000, 2000, 3000] outliers (exam-
ples with random labels) into the training data. Small number of outliers doesn’t noticeably impact
generalization performance, but a large number hinders it signiﬁcantly.
In this section we show data efﬁciency curves for a modiﬁed version of a binary op by introducing
k outliers to the training dataset. More precisely, at the beginning of the experiment we randomly
samplek equations from the training set and replace their answers with answers to otherk equations
randomly sampled from the training data. The rest of the equations in the training data and all the
equations in the validation data are kept as before.
In this situation one could imagine one of the following scenarios unfolding. If the model class of
neural networks optimized and regularized as before was not large enough to interpolate such “noisy”
dataset, one could imagine the procedure converging to a solution that generalizes well, but denoises
the training data (i.e. predicts c =a◦b as an answer even for the outlier equationsa,b→c′ with
c′⁄= c). On the other extreme it could be that the optimization procedure can ﬁnd networks that
interpolate the data, but the resulting models don’t generalize, because they are forced to represent a
considerably more complicated function than before (a simple function +k exceptions encoded in
the training data).
In our experiments we ﬁnd that the ﬁrst option doesn’t happen - all experiments reach 100% training
accuracy at some point, and this point is not considerably affected by changing the number of outliers
k. The second phenomenon happens in a range of training data percentages and number of outliers k
- increasingk decreases the range of training data percentages for which the optimization procedure
converges to models that generalize. However the effect of introducing a small number of outliers
(up to 1000) is not very pronounced - see Figure 6. We interpret this as additional evidence that
the capacity of the network and optimization procedure is well beyond the capacity needed for
9
```

## Batch 3: 2303.06173, PDF page 8

```text
A An alternative intuition for preferred patterns
Rather than thinking about patterns as random functions from the entire input distributionD to the
model’s outputO, we can instead think of patterns as functions from a subset of the input distribution
Di⊂D . On this view, a pattern can successfully classify an input from the training set if and only if
that input is in the patterns domain. On the test set, a data-point is allocated uniformly at random
to patterns whose domain includes that data-point. If allocated to pattern j, the test data-point is
classiﬁed successfully with probabilitygj.
We can then say that a preferred pattern enforces that its domainDi is disjoint from all other pattern
domains on the test set; that isDi is preferred if∀j∈{ 0,··· ,n},i⁄=j =⇒ Di∩Dj =∅.
B Experiment Details
In all of our experiments, we train decoder-only transformer with causal attention masking. Each
residue is encoded as a symbol, and loss and accuracy are only evaluated on the answer part of the
equation. Unless otherwise stated, we use a 2-layer network of width 128, with a single attention
head. We typically train for 400 thousand optimization steps via AdamW (β1 = 0.9,β2 = 0.98),
with learning rate of 1e-3 and weight decay of 1e-5.
C Discussion: how relevant is the science of deep learning for AI safety?
A key factor that inﬂuences whether we will be able to build safe AI systems is the degree to which our
systems are transparent and well-understood. A system is transparent if we are able to ascertain what
process lead it to produce a speciﬁc output or action; we might try to train a system to produce visible
thoughts, truthfully report its knowledge, or probe it with interpretability tools (Christiano et al.,
2021; Soares, 2021; Lanham, 2022; Lin et al., 2021; Olah et al., 2018). A system is well-understood
to the extent that we have a broader theory about why it works and how it scales with respect to
training time, model size, or dataset size. To name a few examples: we might try to quantitatively
understand why models follow certain scaling laws, how they behave in the inﬁnite-width limit, or
what training curves look like on different input types (Sharma & Kaplan, 2022; Bahri et al., 2021;
Maloney et al., 2022; Yang & Hu, 2021; Siddiqui et al., 2022).
We use the term science of deep learning to refer to the latter kind of inquiry, which can be directly
useful for safety: for example, it might help us predict when and how a neural network acquires a
certain capability or behavior. This is helpful if we want to build a system that can perform a speciﬁc
feat of engineering, while making sure that it does not have the capability to model humans; or if we
tried to build a system that optimizes for the short-term approval of its operator, and would like to
know in advance if it will generalize in a way that leads to it deceiving its operator in order to gain a
higher measured approval score once it gains the ability to do so. In addition, a better science of deep
learning may help us build better interpretability tools.
A science of deep learning may also be harmful if theoretical or empirical breakthroughs result in
faster advancement of potentially dangerous capabilities. This is a major drawback of this line of
research. A tentative argument in favor of scientiﬁc / conceptual work is that it seems possible to
build human-level AI systems without a radically improved understanding of deep learning; however,
building safe human-level AI is a harder problem that will likely require a more robust theory. Thus
advancing the science of deep learning seems somewhat more critical for solving problems of safety
than of capabilities. This argument is speculative, and may turn out to be wrong.
D Additional Figures
8
```

## Batch 3: 2303.06173, PDF page 9

```text
20 50 80 110 140
Transformer embedding dimension
0
140
940
5890
36560
226430Training steps
T est Accuracy
20 50 80 110 140
Transformer embedding dimension
Training Accuracy
10 3
10 2
10 1
100
Figure 6: Left: Test accuracy as function of training steps and model size. A faint double descent
in test accuracy is visible, and delayed generalization is clear both epoch-wise (vertically) and
model-wise (horizontally). Right: Training accuracy as a function of training steps and model size.
100 101 102 103
Epochs
0.0
0.2
0.4
0.6
0.8
1.0Accuracy
Modular Division (training on 50% of data)
0 25 50 75 100 125 150
0
20
40
60
80
96
Test Examples Correct (4656 total)
no. test correct
no. '0 / b = 0' correct
no. '0 / b = 0' examples
train
test
Figure 7: Early in training, the model learns 0/b = 0 mod n, as the no. 0/b = 0 mod n correct
(green) matches all such examples (dashed gray). This leads to a brief peak of 96 correct examples,
corresponding to perfect performance on the 0/b = 0 and chance performance (1/97) on other data.
Test accuracy on all other examples then falls below chance due to memorization.
9
```

## Batch 3: 2309.02390, PDF page 7

```text
Explaining grokking through circuit efficiency
In the second case, gradient descent would produce a mixture of both𝐶memand 𝐶gen. Since
neither𝐶memnor𝐶genwould dominate the prediction on the test set, we would expect middling test
performance.
𝐶memwould still be learned faster, and so this would look similar to grokking: an initial phase with
good train performance and bad test performance, followed by a transition to significantly improved
test performance. Since we only get to middling generalisation unlike in typical grokking, we call this
behavioursemi-grokking.
Our theory does not say which of the two cases will arise in practice, but in Section 5.3 we find
that semi-grokking does happen in our setting.
5. Experimental evidence
Our explanation of grokking has some support from from prior work:
1. Generalising circuit:Nanda et al. (2023, Figure 1) identify and characterise the generalising
circuit learned at the end of grokking in the case of modular addition.
2. Slow vs fast learning:Nanda et al. (2023, Figure 7) demonstrate “progress measures” showing
that the generalising circuit develops and strengthens long after the network achieves perfect
training accuracy in modular addition.
To further validate our explanation, we empirically test our predictions from Section 4:
(P1) Efficiency: We confirm our prediction that𝐶genefficiency is independent of dataset size, while
𝐶memefficiency decreases as training dataset size increases.
(P2) Ungrokking (phase transition):We confirm our prediction that ungrokking shows a phase
transition around𝐷crit.
(P3) Ungrokking (weight decay):We confirm our prediction that the final test accuracy after
ungrokking is independent of the strength of weight decay.
(P4) Semi-grokking: We demonstrate that semi-grokking occurs in practice.
Training details.We train 1-layer Transformer models with the AdamW optimiser (Loshchilov and
Hutter, 2019) on cross-entropy loss (see Appendix A for more details). All results in this section are
on the modular addition task (𝑎+𝑏 mod 𝑃 for𝑎,𝑏∈( 0,...,𝑃 − 1) and 𝑃 = 113) unless otherwise
stated; results on 9 additional tasks can be found in Appendix A.
5.1. Relationship of efficiency with dataset size
We first test our prediction about memorisation and generalisation efficiency:
(P1) Efficiency.We predict (Section 4.1) that memorisation efficiency decreases with increasing train
dataset size, while generalisation efficiency stays constant.
To test (P1), we look at training runs where only one circuit is present, and see how the logits𝑜𝑦𝑖
vary with the parameter norm𝑃𝑖 (by varying the weight decay) and the dataset size𝐷.
Experiment setup.We produce𝐶mem-only networks by using completely random labels for the
training data (Zhang et al., 2021), and assume that the entire parameter norm at convergence is
allocated to memorisation. We produce𝐶gen-only networks by training on large dataset sizes and
checking that> 95% of the logit norm comes from just the trigonometric subspace (see Appendix B
for details).
7
```

## Batch 3: 2309.02390, PDF page 8

```text
Explaining grokking through circuit efficiency
25 30 40 60 90
Parameter norm
30
60
90Correct logit
fixed logit values
0.5 1.0 2.0 4.0 8.0
Dataset size 1e3
25
30
40
60
90Parameter norm0.5
1.0
2.0
4.0
8.0
Dataset size
1e3
50
60
70
Correct logit
(a) 𝐶memscatter plot. At a fixed logit value (dot-
ted horizontal lines), parameter norm increases with
dataset size.
25 30 40 60 90
Parameter norm
30
60
90Correct logit
fixed logit values
0.5 1.0 2.0 4.0 8.0
Dataset size 1e3
25
30
40
60
90Parameter norm0.5
1.0
2.0
4.0
8.0
Dataset size
1e3
50
60
70
Correct logit
(b) 𝐶memisologit curves. Curves go up and right,
showing that parameter norm increases with dataset
size when holding logits fixed.
27 30 33
Parameter norm
30
60
90
120Correct logit
fixed logit values
4 6 8
Dataset size 1e3
27
30
33Parameter norm
4
6
8
Dataset size
1e3
50
70
90
Correct logit
(c)𝐶genscatter plot. There is no obvious structure
to the colours, suggesting that the logit to parameter
norm relationship is independent of dataset size.
(d)𝐶genisologit curves.The curves are flat, showing
that for fixed logit values the parameter norm does
not depend on dataset size.
Figure 3| Efficiency of the𝐶memand𝐶genalgorithms. We collect and visualise a dataset of triples 
𝑜𝑦,𝑃 𝑚,𝐷  (correct logit, parameter norm, and dataset size), each corresponding to a training run
with varying random seed, weight decay, and dataset size, for both𝐶memand𝐶gen. Besides a standard
scatter plot, we geometrically bucket logit values into six buckets, and plot “isologit curves” showing
the dependence of parameter norm on dataset size for each bucket. The results validate our theory
that (1)𝐶memrequires larger parameter norm to produce the same logits as dataset size increases,
and (2)𝐶genuses the same parameter norm to produce fixed logits, irrespective of dataset size. In
addition,𝐶memhas a much wider range of parameter norms than𝐶gen, and at the extremes can be
more efficient than𝐶gen.
Results. Figures 3a and 3b confirm our theoretical prediction for memorisation efficiency. Specifically,
to produce a fixed logit value, a higher parameter norm is required when dataset size is increased,
implying decreased efficiency. In addition, for a fixed dataset size, scaling up logits requires scaling up
parameter norm, as expected. Figures 3c and 3d confirm our theoretical prediction for generalisation
efficiency. To produce a fixed logit value, the same parameter norm is required irrespective of the
dataset size.
Note that the figures show significant variance across random seeds. We speculate that there are
many different circuits implementing the same overall algorithm, but they have different efficiencies,
and the random initialisation determines which one gradient descent finds. For example, in the case
of modular addition, the generalising algorithm depends on a set of “key frequencies” (Nanda et al.,
2023); different choices of key frequencies could lead to different efficiencies.
It may appear from Figure 3c that increasing parameter norm does not increase logit value,
contradicting our theory. However, this is a statistical artefact caused by the variance from the random
seed. Wedo see “stripes” of particular colours going up and right: these correspond to runs with the
same seed and dataset size, but different weight decay, and they show that when the noise from the
random seed is removed, increased parameter norm clearly leads to increased logits.
8
```

## Batch 3: 2309.02390, PDF page 9

```text
Explaining grokking through circuit efficiency
103 104
Reduced dataset size
0.0
0.5
1.0T est accuracy
x + y mod P
0.1
0.5
1.0
1.5
2.0
Weight decay
Average accuracy Per seed accuracy
Figure 4| Ungrokking. We train on the full
dataset (achieving 100% test accuracy), and
then continue training on a smaller subset of
the full dataset. We plot test accuracy against
reduced dataset size for a range of weight de-
cays. We see a sharp transition from strong test
accuracy to near-zero test accuracy, that is in-
dependent of weight decay (different coloured
lines almost perfectly overlap). See Figure 8 for
more tasks.
0 1 2 3
Epochs 1e7
0.0
0.5
1.0T est accuracy
0.25
0.50
0.75
1.00
Final accuracy
Figure 5| Semi-grokking. We plot test accu-
racy against training epochs for a large sweep of
training runs with varying dataset sizes. Lines
are coloured by the final test accuracy at the
end of training. Out of 200 runs, at least 6 show
clearsemi-grokkingattheendoftraining. Many
other runs show transient semi-grokking, hover-
ing around middling test accuracy for millions
of epochs, or having multiple plateaus, before
fully generalising.
5.2. Ungrokking: overfitting after generalisation
We now turn to testing our predictions about ungrokking. Figure 1b demonstrates that ungrokking
happens in practice. In this section we focus on testing that it has the properties we expect.
(P2) Phase transition.We predict (Section 4.2) that if we plot test accuracy at convergence against
the size of the reduced training dataset𝐷′, there will be a phase transition around𝐷crit.
(P3) Weight decay.We predict (Section 4.2) that test accuracy at convergence is independent of the
strength of weight decay.
Experiment setup.We train a network to convergence on the full dataset to enable perfect gener-
alisation, then continue training the model on a small subset of the full dataset, and measure the
test accuracy at convergence. We vary both the size of the small subset, as well as the strength of the
weight decay.
Results. Figure 4 shows the results, and clearly confirms both (P2) and (P3). Appendix A has
additional results, and in particular Figure 8 replicates the results for many additional tasks.
5.3. Semi-grokking: evenly matched circuits
Unlike the previous predictions, semi-grokking is not strictly implied by our theory. However, as we
will see, it turns out that it does occur in practice.
(P4) Semi-grokking.When training at around𝐷≈ 𝐷crit, where𝐶memand𝐶genhave roughly equal
efficiencies, the final network at convergence should either be entirely composed of the most efficient
circuit, or of roughly equal proportions of𝐶memand𝐶gen. If the latter, we should observe a transition
to middling test accuracy well after near-perfect train accuracy.
There are a number of difficulties in demonstrating an example of semi-grokking in practice.
First, the time to grok increases super-exponentially as the dataset size𝐷 decreases (Power et al.,
2021, Figure 1), and𝐷crit is significantly smaller than the smallest dataset size at which grokking
9
```

## Batch 3: 2310.06110, PDF page 12

```text
Published as a conference paper at ICLR 2024
Simon Kornblith, Mohammad Norouzi, Honglak Lee, and Geoffrey Hinton. Similarity of neural
network representations revisited. In International conference on machine learning, pages 3519–
3529. PMLR, 2019.
Sanjeev Arora, Simon Du, Wei Hu, Zhiyuan Li, and Ruosong Wang. Fine-grained analysis of op-
timization and generalization for overparameterized two-layer neural networks. In International
Conference on Machine Learning, pages 322–332. PMLR, 2019.
Aitor Lewkowycz and Guy Gur-Ari. On the training dynamics of deep networks with l 2 regular-
ization. Advances in Neural Information Processing Systems, 33:4790–4799, 2020.
Boaz Barak, Benjamin Edelman, Surbhi Goel, Sham Kakade, Eran Malach, and Cyril Zhang. Hid-
den progress in deep learning: Sgd learns parities near the computational limit. Advances in
Neural Information Processing Systems, 35:21750–21764, 2022.
Theodor Misiakiewicz. Spectrum of inner-product kernel matrices in the polynomial regime and
multiple descent phenomenon in kernel ridge regression.arXiv preprint arXiv:2204.10425, 2022.
Jeremy M Cohen, Simran Kaur, Yuanzhi Li, J Zico Kolter, and Ameet Talwalkar. Gradient descent
on neural networks typically occurs at the edge of stability. arXiv preprint arXiv:2103.00065 ,
2021.
Rylan Schaeffer, Brando Miranda, and Sanmi Koyejo. Are emergent abilities of large language
models a mirage? arXiv preprint arXiv:2304.15004, 2023.
12
```

## Batch 3: 2310.06110, PDF page 13

```text
Published as a conference paper at ICLR 2024
8 A PPENDIX
ADDITIONAL EXPERIMENTS
8.1 A N OTE ON IMPLEMENTING LARGE α
As was discussed in the original paper on inducing lazy training by Chizat et al. (2019), it is im-
portant to subtract off the initial predictor from the neural network function. Concretely, one should
take as their predictor, the modified function
˜f (x, θ) = α[f (x, θ) − f (x, θ0)] (7)
In our experiments, we place ˜f in the optimizer when we compute gradients. This allows us to train
with very large values of α without experiencing instability at initialization. Further, to maintain
consistent timescales of training, it is important to rescale learning rate as η = η0/α2. This rescal-
ing keeps the initial derivative ddt f |t=0 independent of α and thus the early training dynamics areconsistent across α. Otherwise, large α networks will have too large a learning rate and small α
networks take too long to train.
8.2 W EIGHT NORM AND INITIALIZATION SCALE HAVE THE SAME EFFECT
100 101 102 103 104
t
0.0
0.2
0.4
0.6
0.8
1.0Loss
= 2 5
= 2 2
= 2 1
= 20
= 21
= 22
= 23
= 24
(a) Varying α
100 101 102 103 104
t
0.0
0.2
0.4
0.6
0.8
1.0
1.2Loss
= 2 3
= 2 2
= 2 1
= 20
= 21
 (b) Varying Init. Scale σ
100 101 102 103 104
t
0.0
0.2
0.4
0.6
0.8
1.0
1.2Loss
= 2 2 | = 24
= 2 1 | = 22
= 20 | = 2 0
= 21 | = 2 2
 (c) Vary σ with σ2α fixed
10 1
 100 101
2
100
101
| 0|/| 0|
vary , = 1
vary , = 1
( 2) 12
(d) Parameter Movement
10 1
 100 101
2
10 3
10 2
10 1
100
Final T est Loss
vary , = 1
vary , = 1
 (e) Final MSE vs σ2α
100 101
| 0|/| 0|
10 3
10 2
10 1
100
Final T est Loss
vary , = 1
vary , = 1
 (f) Final MSE vs Param. Move-
ment
Figure 7: Weight scale alters grokking dynamics and final test loss primarily by manipulating the
richness of the dynamics, specifically how far the dynamics deviates from the linear/kernel regime.
(a) The loss curves for a two layer network trained on the quadratic polynomial with varying laziness
parameter α. Note that small α networks do not grok as dramatically as large α and also achieve
good test loss. (b) A similar sweep over weight initialization scale σ yields the same trend. (c) For
a two layer network, approximate preservation of the feature learning can be achieved by choosing
α ∼ σ−2. (d)-(f) The relative parameter change |w − w0|/|w0| and final test loss is controlled
through the quantity σ2α.
8.3 M ODULAR ARITHMETIC IN A 2 LAYER PERCEPTRON
Here are the architecture details for grokking with weight norm increase on a modular arithmetic
task on a two-layer perceptron with vanilla GD. First, we consider the classic modular arithmetic
task a + b ≡ c mod p used previously to explore grokking in Power et al. (2022); Nanda et al.
(2023). We find grokking in a one-hidden layer network with input dimension D = 2p, where the
13
```
