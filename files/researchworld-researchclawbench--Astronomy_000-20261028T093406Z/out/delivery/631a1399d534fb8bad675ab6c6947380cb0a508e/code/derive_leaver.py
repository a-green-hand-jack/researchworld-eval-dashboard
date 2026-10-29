"""Symbolic derivation of the Leaver recurrence (numerator polynomial in x over (1-x)^10; after
substituting the Leaver exponents it factorises as (1-x)^8 * quadratic(x)). The numerator
coefficients (code/leaver_coef.pkl) are produced with `pickle.dump((Pl.all_coeffs()[::-1], den), ...)`.
Run once; leaver.py loads the pickle of the coefficient list."""
import sympy as sp
x,n,d=sp.symbols('x n delta')
rp,rm,w,mu,m,a,lam,q,A,B=sp.symbols('rp rm w mu m a lam q A B')
u=d/(1-x); rr=rm+u; rpp=rp+0
# r - r+ = x*u ; r - r- = u ; r = rm + u
Dl=x*u*u
r_=rm+u
H=A*u+B*x*u+q*Dl                    # Delta*h with h=A/(r-r+)+B/(r-r-)+q  -> A(r-r-)+B(r-r+)+q*Delta
Dp=2*r_-(rp+rm)                      # Delta'
K=(r_**2+a**2)*w-a*m
P=H**2+Dp*H-A*u**2-B*(x*u)**2+K**2-Dl*(mu**2*r_**2+lam)
tot=Dl**2*((1-x)**4*n*(n-1)/(d**2*x**2)-2*(1-x)**3*n/(d**2*x))+Dl*(2*H+Dp)*(1-x)**2*n/(d*x)+P
tot=sp.together(sp.expand(tot))
num,den=sp.fraction(tot)
print(sp.factor(den))
num=sp.expand(num.subs(d,rp-rm))
Pl=sp.Poly(num,x)
print(Pl.degree())
import pickle; pickle.dump((Pl.all_coeffs()[::-1],den),open(__import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)),'leaver_coef_full.pkl'),'wb'))
