src=open("code/btlib.py").read()
old=src[src.index("    def __post_init__(self):"):src.index("    @property\n    def m(self):")]
new='''    def __post_init__(self):
        self._hidx = None

    def design(self):
        """Dense design matrix (only used in tests)."""
        m = len(self.players)
        d = m + (1 if self.use_home else 0)
        T = len(self.a)
        X = np.zeros((T, d))
        X[np.arange(T), self.a] += 1.0
        X[np.arange(T), self.b] -= 1.0
        if self.use_home:
            X[:, m] = self.h
        return X

'''
src=src.replace(old,new)
src=src.replace("    use_home: bool = False\n    X: np.ndarray = field(default=None, repr=False)\n","    use_home: bool = False\n")
open("code/btlib.py","w").write(src)
t=open("code/tests/test_btlib.py").read()
t=t.replace("g = tt.X.T @","g = tt.design().T @").replace("X, y, n = tt.X, tt.y, tt.n","X, y, n = tt.design(), tt.y, tt.n")
open("code/tests/test_btlib.py","w").write(t)
