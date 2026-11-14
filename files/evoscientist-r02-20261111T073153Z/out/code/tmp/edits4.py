p = "paper/appendix.tex"
s = open(p).read()
a = r"we used the \texttt{uoft-cs/cifar10} parquet mirror on Hugging Face (the official files from the dataset page downloaded too slowly in our environment) and verified its test-set order against CIFAR-10H (argmax of human proportions equals the mirror's test label for $99.2\%$ of images; a mismatched order would give about $10\%$)."
b = r"we used the \texttt{uoft-cs/cifar10} parquet mirror on Hugging Face (downloaded first because the official server was slow), then downloaded the official tarball (md5 \texttt{c58f30108f718f92721af3b95e74349a}, as listed on the task page) and verified that the mirror's test images and labels are identical, in the same order, and that its training images are identical as a set (\texttt{code/verify\_cifar\_mirror.py}); the test order also matches CIFAR-10H (argmax of human proportions equals the test label for $99.2\%$ of images; a mismatched order would give about $10\%$)."
print(a in s)
s = s.replace(a, b)
open(p, "w").write(s)
