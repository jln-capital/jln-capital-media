W=520;H=200
def building(col,sw=1.5,ext=140):
    L=lambda x1,y1,x2,y2,w=1:f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="{round(sw*w,2)}" stroke-linecap="round"></line>'
    Rr=lambda x,y,w,h,k=1:f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{col}" stroke-width="{round(sw*k,2)}" stroke-linejoin="round"></rect>'
    P=lambda d,k=1:f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{round(sw*k,2)}" stroke-linecap="round" stroke-linejoin="round"></path>'
    n=9;bay=46;x0=24;x1=x0+n*bay            # arcade from x0 to x1
    s=L(-ext,H,W+ext,H)                      # water line
    s+=L(x0-6,150,x1+6,150)+L(x0-6,145,x1+6,145)   # floor slab
    s+=L(x0-6,88,x1+6,88)+L(x0-8,82,x1+8,82)       # entablature / cornice
    s+=L(x0-4,72,x1+4,72,0.8)                       # top balustrade rail
    for i in range(n+1):
        x=x0+i*bay
        s+=Rr(x-4,150,8,50,0.9)                     # pier into the water
        s+=L(x-2,145,x-2,112,0.8)+L(x+2,145,x+2,112,0.8)+L(x-4,112,x+4,112,0.8)   # column + capital
        s+=Rr(x-3.5,72,7,10,0.7)                    # pedestal on the balustrade
        s+=f'<circle cx="{x}" cy="{67.5}" r="2.6" fill="none" stroke="{col}" stroke-width="{round(sw*0.7,2)}"></circle>'+L(x,70,x,72,0.7)   # urn
        if i<n:
            r=(bay-8)/2
            s+=P(f'M{x+4} 112 A{r} {r} 0 0 1 {x+bay-4} 112')        # arch
            s+=L(x+4,131,x+bay-4,131,0.7)                           # railing
            for k in range(1,7): s+=L(x+4+k*(bay-8)/7,131,x+4+k*(bay-8)/7,145,0.45)
            for k in range(1,5): s+=L(x+3.5+k*(bay-7)/5,72,x+3.5+k*(bay-7)/5,82,0.4)   # top balusters
    # end pavilion on the right
    a=x1+6;b=a+44
    s+=Rr(a,60,44,140)+L(a-3,60,b+3,60)+L(a-3,54,b+3,54)+L(a,150,b,150,0.8)+L(a,88,b,88,0.8)
    s+=P(f'M{a+11} 145 V112 A11 11 0 0 1 {b-11} 112 V145',0.9)       # tall arched opening
    s+=P(f'M{a+15} 82 V72 A7 7 0 0 1 {b-15} 72 V82 Z',0.7)           # upper arched window
    s+=P(f'M{a+6} 54 L{a+22} 38 L{b-6} 54',0.9)                      # pediment
    s+=f'<circle cx="{a+22}" cy="33.5" r="2.8" fill="none" stroke="{col}" stroke-width="{round(sw*0.7,2)}"></circle>'+L(a+22,36,a+22,38,0.7)
    for xx in (a,b): s+=Rr(xx-3,44,6,10,0.7)+f'<circle cx="{xx}" cy="40" r="2.4" fill="none" stroke="{col}" stroke-width="{round(sw*0.7,2)}"></circle>'
    # reflection hints in the water
    for i in range(n+2):
        x=x0+i*bay if i<=n else b-22
        s+=L(x-3,206,x+3,206,0.5)+L(x-2,211,x+2,211,0.4)
    return s
