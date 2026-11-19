import sys, time; sys.path.insert(0,'src')
import numpy as np, data, models, explain
for dn in ['pima','german']:
    D=data.load(dn)
    rs=np.random.RandomState(0); bg=D['Xtr'][rs.choice(len(D['Xtr']),50,replace=False)]
    x=D['Xte'][0]
    for k in ['lr','rf','xgb','mlp']:
        t=time.time(); m=models.train(k,D); tt=time.time()-t
        print(dn,k,m.score(D['Xte'],D['yte']),'train %.1fs'%tt)
        d=len(x)
        t=time.time(); p=explain.kernel_phi(m.predict,x,bg,1024,0); t1=time.time()-t
        t=time.time(); q=explain.perm_phi(m.predict,x,bg,1024,0); t2=time.time()-t
        t=time.time(); r,kind=explain.reference_phi(m,x,bg); t3=time.time()-t
        fx=m.predict(x)[0]; base=m.predict(bg).mean()
        print('  eff: sum kernel %.4f perm %.4f ref %.4f target %.4f'%(p.sum(),q.sum(),r.sum(),fx-base),
              '| relL2 kernel %.3f perm %.3f'%(np.linalg.norm(p-r)/np.linalg.norm(r),np.linalg.norm(q-r)/np.linalg.norm(r)),
              '| t %.2f %.2f %.2f'%(t1,t2,t3),kind)
        if k=='rf' and d<=12:
            e=explain.exact_kernel(m.predict,x,bg); print('  treeshap vs enumeration maxabs diff',np.abs(e-r).max())
