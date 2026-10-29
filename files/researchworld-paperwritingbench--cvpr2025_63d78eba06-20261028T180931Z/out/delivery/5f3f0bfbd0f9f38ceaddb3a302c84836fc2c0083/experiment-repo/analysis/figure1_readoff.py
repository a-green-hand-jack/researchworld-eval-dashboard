import numpy as np, PIL.Image as I
im=np.array(I.open('/initial-state/inputs/2/figure_1.png').convert('RGB')).astype(int)
cols={'Retrained':(98,132,190),'Unl+':(222,148,100),'Unl-':(200,95,100)}
xr={'Retrained':[54,143,233,323,502,592,682,772],'Unl+':[76,166,256,345,525,615,704,794],'Unl-':[98,188,278,368,547,637,727,817]}
panels=[('CIFAR-10',0,0),('CIFAR-100',1,0),('StanfordDogs',0,1),('Caltech256',1,1)]
y0={0:237.5,1:522.5}; ppu={0:(237.5-10)/80,1:(522.5-296)/80}
groups=['Test','Remain','Forget','MIA']
for n,(pn,px,py) in enumerate(panels):
    print(pn)
    for m,c in cols.items():
        vals=[]
        for g in range(4):
            x=xr[m][g+4*px]+10
            col=np.abs(im[:,x]-np.array(c)).sum(1)<60
            lo,hi=(0,260) if py==0 else (280,540)
            yb=int(y0[py])-2
            top=yb
            while col[top-1]: top-=1
            vals.append(round((y0[py]-top+0.5)/ppu[py],1))
        print(' ',m,dict(zip(groups,vals)))
