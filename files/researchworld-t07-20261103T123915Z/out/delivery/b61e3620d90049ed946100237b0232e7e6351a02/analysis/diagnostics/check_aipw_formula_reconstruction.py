"""Disposable direct-estimator check of the retrospective same-alpha identity."""
import numpy as np
from benchsmall.estimators import aipw_estimator,mean_estimator
rng=np.random.default_rng(671)
for n in [137,300]:
 source=rng.binomial(1,.4,(43,n)).astype(float);target=rng.binomial(1,.6,(11,n)).astype(float)
 for k in [10,30,100]:
  items=rng.permutation(n)[:k];z=target[:,items]
  code=aipw_estimator(source,items,10.,'code').predict(z)
  direct=aipw_estimator(source,items,10.,'paper').predict(z)
  reconstructed=(k/n)*mean_estimator(source,items).predict(z)+(1-k/n)*code
  np.testing.assert_allclose(reconstructed,direct,rtol=0,atol=1e-12)
print('Same-alpha formula reconstruction agrees with direct paper estimator to1e-12 on disposable binary matrices.')
