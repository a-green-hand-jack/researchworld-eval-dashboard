import numpy as np
def coeffs_fun(a,w,mu,m,A):
    b=np.sqrt(1-a*a); rp=1+b; rm=1-b; D=rp-rm
    q=np.sqrt(mu**2-w**2+0j)   # Re q>0 decaying
    if q.real>0: q=-q
    sig=(2*w*rp-a*m)/D
    chi=(mu**2-2*w**2)/q
    I=1j
    def f(u):
        r=(rp-rm*u)/(1-u); rrp=D*u/(1-u); rrm=D/(1-u)
        Delta=rrp*rrm; dDelta=2*r-2
        K=(r**2+a**2)*w-a*m; lam=A+a*a*w*w-2*a*m*w
        V=K**2-Delta*(mu**2*r**2+lam)
        L=-I*sig/rrp+(I*sig+chi-1)/rrm+q
        # dL/du
        dLdu=I*sig*D/(rrp**2*(1-u)**2)*1.0  # placeholder replaced below
        # exact: d(1/rrp)/du = d((1-u)/(D u))/du = -1/(D u^2); d(1/rrm)/du = -1/D
        dLdu=-I*sig*(-1/(D*u**2))+(I*sig+chi-1)*(-1/D)
        dLdr=dLdu*(1-u)**2/D
        up=(1-u)**2/D; upp=-2*(1-u)*up/D
        cuu=Delta**2*up**2
        cu=Delta**2*(upp+2*L*up)+Delta*dDelta*up
        c0=Delta**2*(dLdr+L**2)+Delta*dDelta*L+V
        return cuu,cu,c0
    return f
if __name__=='__main__':
    f=coeffs_fun(0.9,0.3+1e-3j,0.31,1,2.0)
    us=np.linspace(0.1,0.9,12)
    for k,name in enumerate(['cuu','cu','c0']):
        for p in (0,1,2,3,4):
            y=np.array([f(u)[k]*(1-u)**p for u in us])
            c=np.polyfit(us,y,8); res=np.abs(np.polyval(c,us)-y).max()
            deg=np.max(np.nonzero(np.abs(c)>1e-9*np.abs(c).max())[0]) if True else 0
            print(name,p,'highest nonzero power', 8-np.min(np.nonzero(np.abs(c)>1e-8*np.abs(c).max())[0]),'res',res)
