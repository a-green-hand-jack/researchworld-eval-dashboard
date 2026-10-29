s=open("code/datasets.py").read()
s=s.replace('return dict(a=df.a.values, b=df.b.values, y=df.y.values.astype(float), h=h,',
 'return dict(a=np.asarray(df.a.values, dtype=object), b=np.asarray(df.b.values, dtype=object),\n                y=np.asarray(df.y.values, dtype=float), h=np.asarray(h, dtype=float),')
open("code/datasets.py","w").write(s)
