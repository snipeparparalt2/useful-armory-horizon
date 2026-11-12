import gzip,struct,sys,glob,os,hashlib
from PIL import Image,ImageDraw
def rd(b,i,t):
    if t==1: return struct.unpack_from('>b',b,i)[0],i+1
    if t==2: return struct.unpack_from('>h',b,i)[0],i+2
    if t==3: return struct.unpack_from('>i',b,i)[0],i+4
    if t==8:
        n=struct.unpack_from('>H',b,i)[0]; return b[i+2:i+2+n].decode(),i+2+n
    if t==9:
        et,n=struct.unpack_from('>bi',b,i); i+=5; out=[]
        for _ in range(n):
            v,i=rd(b,i,et); out.append(v)
        return out,i
    if t==10:
        d={}
        while True:
            tt=b[i]; i+=1
            if tt==0: return d,i
            n=struct.unpack_from('>H',b,i)[0]; k=b[i+2:i+2+n].decode(); i+=2+n
            d[k],i=rd(b,i,tt)
    raise ValueError(t)
COL={'air':None,'stone_bricks':(125,125,125),'cracked_stone_bricks':(105,105,110),'mossy_stone_bricks':(105,125,95),'cobblestone':(120,118,116),'mossy_cobblestone':(100,120,95),'oak_planks':(170,135,80),'spruce_planks':(110,82,48),'oak_log':(105,82,50),'spruce_log':(60,40,22),'chest':(200,140,40),'barrel':(150,105,60),'spawner':(40,60,90),'ladder':(160,120,70),'white_wool':(235,235,235),'red_wool':(170,40,35),'campfire':(240,130,30),'prismarine_bricks':(100,170,160),'dark_prismarine':(50,95,80),'prismarine':(95,160,150),'sea_lantern':(210,235,230),'aquiteore':(60,220,190),'colosfiteblock':(240,140,25),'colosifiteore':(200,130,60),'nether_bricks':(60,25,30),'cracked_nether_bricks':(50,20,25),'chiseled_nether_bricks':(70,30,35),'gold_block':(250,215,60),'magma_block':(150,60,20),'deepslate_bricks':(72,72,76),'cracked_deepslate_bricks':(62,62,66),'deepslate_tiles':(52,52,56),'polished_deepslate':(82,82,86),'shadowblock':(40,30,80),'deepslate_shadow_ore':(110,90,220),'soul_lantern':(90,220,230),'lantern':(250,200,90),'stone':(130,130,130),'andesite':(140,140,138),'gravel':(135,128,125),'rail':(160,150,130),'cobweb':(230,230,230),'bookshelf':(150,110,70),'chiseled_stone_bricks':(140,140,140),'glass':(190,225,235),'jigsaw':(150,60,170),'coarse_dirt':(120,85,58),'dirt_path':(150,120,70),'hay_block':(200,170,40),'spruce_slab':(110,82,48)}
def col(name):
    n=name.split(':')[1]
    if n in COL: return COL[n]
    h=hashlib.md5(n.encode()).digest(); return (90+h[0]%120,90+h[1]%120,90+h[2]%120)
def render(path,cut=False):
    root,_=rd(gzip.open(path).read(),3,10)
    W,H,D=root['size']; pal=root['palette']
    cells={tuple(b['pos']):pal[b['state']]['Name'] for b in root['blocks']}
    s=12
    img=Image.new('RGBA',((W+D)*s+20,(W+D)*s//2+H*s+30),(245,245,245,255)); d=ImageDraw.Draw(img)
    ox=D*s+10; oy=H*s+10
    for y in range(H):
        for z in range(D):
            for x in range(W):
                if cut and z>D//2: continue
                c=col(cells.get((x,y,z),'minecraft:air'))
                if not c: continue
                px=ox+(x-z)*s; py=oy+(x+z)*s//2-y*s
                top=[(px,py),(px+s,py+s//2),(px,py+s),(px-s,py+s//2)]
                left=[(px-s,py+s//2),(px,py+s),(px,py+2*s),(px-s,py+s*3//2)]
                right=[(px+s,py+s//2),(px,py+s),(px,py+2*s),(px+s,py+s*3//2)]
                d.polygon(top,fill=c,outline=(0,0,0,60)); d.polygon(left,fill=tuple(int(v*0.75) for v in c),outline=(0,0,0,60)); d.polygon(right,fill=tuple(int(v*0.55) for v in c),outline=(0,0,0,60))
    return img,root
paths=sorted(glob.glob('content/data/useful_armory/structure/**/*.nbt',recursive=True))
ims=[]
for p in paths:
    a,root=render(p); b,_=render(p,True); ims+= [a,b]
    be=[(pal['Name']) for pal in root['palette']]
    print(os.path.basename(p),root['size'],len(root['blocks']),'DataVersion',root['DataVersion'],'nbt blocks:',[ (b['pos'],b['nbt'].get('id'),b['nbt'].get('LootTable') or b['nbt'].get('SpawnData',{}).get('entity',{}).get('id') or b['nbt'].get('name')) for b in root['blocks'] if 'nbt' in b])
W=sum(i.width for i in ims[:6]); 
rows=[ims[i:i+6] for i in range(0,len(ims),6)]
sheet=Image.new('RGBA',(max(sum(i.width for i in r) for r in rows),sum(max(i.height for i in r) for r in rows)),(245,245,245,255))
y=0
for r in rows:
    x=0
    for i in r: sheet.paste(i,(x,y)); x+=i.width
    y+=max(i.height for i in r)
sheet.save(sys.argv[1])
