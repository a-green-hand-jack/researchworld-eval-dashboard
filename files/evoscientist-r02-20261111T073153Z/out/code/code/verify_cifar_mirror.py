"""Check that the Hugging Face mirror arrays (data/cifar10_uint8.npz, made by prepare_cifar.py) are identical to the
official CIFAR-10 python tarball (data/cifar-10-python.tar.gz, md5 c58f30108f718f92721af3b95e74349a)."""
import tarfile, pickle, hashlib, numpy as np
raw = open("data/cifar-10-python.tar.gz", "rb").read()
print("tar md5", hashlib.md5(raw).hexdigest())
tf = tarfile.open("data/cifar-10-python.tar.gz")
def rd(name):
    d = pickle.load(tf.extractfile(name), encoding="bytes")
    return d[b"data"].reshape(-1, 3, 32, 32).transpose(0, 2, 3, 1), np.array(d[b"labels"])
tr = [rd(f"cifar-10-batches-py/data_batch_{i}") for i in range(1, 6)]
Xtr = np.concatenate([a for a, _ in tr]); ytr = np.concatenate([b for _, b in tr])
Xte, yte = rd("cifar-10-batches-py/test_batch")
m = np.load("data/cifar10_uint8.npz")
print("test images identical:", np.array_equal(Xte, m["Xte"]), "test labels identical:", np.array_equal(yte, m["yte"]))
# the train order of the mirror may differ from the official batch order: compare as multisets of images
hs = lambda X: sorted(hashlib.md5(x.tobytes()).hexdigest() for x in X)
print("train images identical as a multiset:", hs(Xtr) == hs(m["Xtr"]), "| same order:", np.array_equal(Xtr, m["Xtr"]))
