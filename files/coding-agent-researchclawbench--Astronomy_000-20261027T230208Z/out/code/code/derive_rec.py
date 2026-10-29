import sympy as sp
r,u=sp.symbols('r u')
a,w,mu,m,A,rp,rm=sp.symbols('a omega mu m A r_p r_m')
sig,chi,q=sp.symbols('sigma chi q')
I=sp.I
# R = (r-rp)^(-i sig) (r-rm)^(i sig+chi-1) exp(q r) S(u)
Delta=(r-rp)*(r-rm)
K=(r**2+a**2)*w-a*m
lam=A+a**2*w**2-2*a*m*w
f=sp.Function('S')
x=sp.symbols('x')  # placeholder
pref=(r-rp)**(-I*sig)*(r-rm)**(I*sig+chi-1)*sp.exp(q*r)
# unknown S(r) as function of r through u(r)
S=sp.Function('S')(r)
R=pref*S
ode=Delta*sp.diff(Delta*sp.diff(R,r),r)+(K**2-Delta*(mu**2*r**2+lam))*R
ode=sp.simplify(ode/pref)
ode=sp.expand(ode)
S0,S1,S2=sp.symbols('S0 S1 S2')
ode=ode.subs(sp.Derivative(S,(r,2)),S2).subs(sp.Derivative(S,r),S1).subs(S,S0)
c2=sp.simplify(ode.coeff(S2)); c1=sp.simplify(ode.coeff(S1)); c0=sp.simplify(ode.coeff(S0))
print('c2',sp.factor(c2))
# convert to u: d/dr = u'(r) d/du ; u=(r-rp)/(r-rm); u' = (rp-rm)/(r-rm)^2... 
up=(rp-rm)/(r-rm)**2
upp=sp.diff(up,r)
# S1 = up*Su ; S2 = up^2*Suu + upp*Su
Su,Suu=sp.symbols('Su Suu')
expr=c2*(up**2*Suu+upp*Su)+c1*up*Su+c0*S0
expr=sp.together(expr)
# replace r in terms of u
rr=(rp-rm*u)/(1-u)
expr=sp.simplify(expr.subs(r,rr))
num,den=sp.fraction(sp.together(expr))
num=sp.expand(num)
import pickle
pc=[sp.factor(num.coeff(s)) for s in (Suu,Su,S0)]
for p in pc: print(sp.collect(sp.expand(p),u)); print()
pickle.dump(pc,open('/work/outputs/rec_poly.pkl','wb'))
