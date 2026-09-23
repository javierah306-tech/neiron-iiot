"""P01: maqueta visual paramétrica. Ejecutar en proceso Blender independiente.
No es modelo validado para fabricación. Hardware y accesorios aproximados.
"""
import bpy, bmesh, math, json
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '04_PROTOTIPOS_3D'
MM = .001
W,H,D,T = 120,90,55,3
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene
s.name='neiron | P01 abierto'
s.unit_settings.system='METRIC'
s.unit_settings.length_unit='MILLIMETERS'
s.unit_settings.scale_length=1

def material(name,color,metal=0,rough=.4):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=rough
    return m
graphite=material('Polimero | grafito',(.065,.085,.105))
lidmat=material('Tapa | gris mineral',(.20,.25,.29))
orange=material('Acento | naranja',(.95,.23,.035))
black=material('Junta y cables',(.013,.020,.028),0,.6)
steel=material('Acero',(.56,.65,.70),.8,.24)
pcb=material('PCB ESP32',(.015,.075,.065))
blue=material('PCB MPU6050',(.02,.16,.48))
green=material('Bornes',(.06,.36,.24))
gold=material('Contactos',(.72,.46,.12),.65,.3)
white=material('Rotulos',(.79,.87,.89))

def coll(name):
    c=bpy.data.collections.new(name); s.collection.children.link(c); return c
C=coll('01 | Gabinetes - geometria provisional')
def assign(o,name,mat):
    o.name=name
    for c in list(o.users_collection):c.objects.unlink(o)
    C.objects.link(o)
    if mat:o.data.materials.append(mat)
    o['estado']='Referencia visual; cotas e interfaces por verificar'
    return o
def bevel(o,r=.7):
    m=o.modifiers.new('Suavizado de aristas','BEVEL'); m.width=r*MM;m.segments=3
    o.modifiers.new('Normales','WEIGHTED_NORMAL')
def box(name,loc,size,mat,r=.5):
    bpy.ops.mesh.primitive_cube_add(size=1,location=Vector(loc)*MM);o=bpy.context.object
    o.dimensions=Vector(size)*MM;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    assign(o,name,mat)
    if r:bevel(o,r)
    return o
def profile(w,h,c):
    return [(-w/2+c,-h/2),(w/2-c,-h/2),(w/2,-h/2+c),(w/2,h/2-c),(w/2-c,h/2),(-w/2+c,h/2),(-w/2,h/2-c),(-w/2,-h/2+c)]
def prism(name,x,y,z,w,h,depth,mat,c=6):
    p=profile(w,h,c);v=[((a+x)*MM,(y+b)*MM,(k+z)*MM) for b in [-depth/2,depth/2] for a,k in p]
    f=[tuple(reversed(range(8))),tuple(range(8,16))]+[(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)]
    me=bpy.data.meshes.new(name);me.from_pydata(v,[],f);me.update()
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    o=bpy.data.objects.new(name,me);C.objects.link(o)
    if mat:o.data.materials.append(mat)
    return o
def subtract(o,c):
    bpy.context.view_layer.objects.active=o
    m=o.modifiers.new('Cavidad o perforacion','BOOLEAN');m.operation='DIFFERENCE';m.object=c
    bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(c,do_unlink=True)
def cyl(name,loc,r,depth,mat,axis='Y',vertices=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r*MM,depth=depth*MM,location=Vector(loc)*MM)
    o=bpy.context.object
    if axis=='Y':o.rotation_euler[0]=math.pi/2
    assign(o,name,mat);bevel(o,.25);return o
def line(name,points,r,mat,cyclic=False):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=r*MM;cu.bevel_resolution=3
    sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
    for p,co in zip(sp.points,points):p.co=(*[v*MM for v in co],1)
    sp.use_cyclic_u=cyclic;o=bpy.data.objects.new(name,cu);C.objects.link(o);cu.materials.append(mat);return o
def text(name,body,loc,size,mat=white):
    cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.size=size*MM;cu.extrude=.015*MM
    o=bpy.data.objects.new(name,cu);C.objects.link(o);o.location=Vector(loc)*MM;o.rotation_euler=(math.pi/2,0,0);cu.materials.append(mat)
    return o

def cabinet(x,opened=False):
    global C
    C=coll(('03 | Abierto' if opened else '02 | Cerrado')+' - piezas gabinete')
    shell=prism('Cuerpo hueco 120 x 90 x 51',x,2,0,W,H,51,graphite)
    cutter=prism('Corte interior',x,-2,0,W-2*T,H-2*T,53,None,4)
    subtract(shell,cutter)
    for a in [-38,0,38]:
        cut=cyl('Paso provisional', (x+a,1,-44),5,12,None,'Z');subtract(shell,cut)
    bevel(shell,.7)
    bracket=box('Soporte mural desmontable',(x,32,0),(78,6,78),black,2)
    for z in [-34,34]:
        cut=cyl('Taladro anclaje',(x,32,z),2.5,12,None);subtract(bracket,cut)
    for a in [-48,48]:
        for z in [-33,33]:
            cyl('Pilar cierre',(x+a,0,z),4,44,graphite)
            cyl('Inserto M3 referencia',(x+a,-22,z),2.3,4,gold)
    # Junta representada separadamente; canal y compresion aun no dimensionados.
    line('Junta perimetral provisional',[(x+a,-24,k) for a,k in profile(113,83,5)],.9,black,True)
    for i,a in enumerate([-38,0,38]):
        cyl(['Entrada 5V USB - concepto','Prensaestopas vibracion','Prensaestopas temperatura'][i],(x+a,1,-50),7,13,black,'Z',8)
        cyl('Tuerca entrada',(x+a,1,-44),8,4,graphite,'Z',6)
        cyl('Salida cable',(x+a,1,-58),4.6,6,black,'Z')
    C=coll(('05 | Interior abierto' if opened else '04 | Interior cerrado')+' - hardware comercial')
    box('Bandeja desmontable',(x,20,0),(99,2,69),lidmat)
    # Placa de referencia 55 alto x 28 ancho; conectores representados aparte.
    box('ESP32 PCB OEM 30 pines',(x-22,13,1),(28,1.6,55),pcb)
    box('Blindaje ESP32',(x-22,9,7),(17,5,18),steel)
    box('Zona antena',(x-22,11,23),(18,1,10),black)
    for k in range(4):box('Pista antena',(x-27+k*3,10,23),(1,1,8),gold,.1)
    box('Micro USB',(x-22,9,-24),(8,5,6),steel)
    box('Boca USB',(x-22,6,-26),(6,1,2),black,.1)
    for a in [-12,12]:
        box('Zocalo',(x-22+a,15,0),(3,4,39),black)
        for j in range(15):box('Pin',(x-22+a,10,-18+j*2.54),(.65,7,.65),gold,.1)
    box('Placa de interconexion',(x+24,13,-3),(28,1.6,46),pcb)
    for z,n in [(9,4),(-11,3)]:
        for j in range(n):
            a=x+13+j*6
            box('Borne desmontable',(a,7,z),(5.7,9,10),green)
            cyl('Tornillo borne',(a,2,z),1.6,1,steel)
    box('Resistencia 4k7',(x+25,9,24),(8,3,3),gold)
    line('Arnes interior',[(x-10,8,-10),(x+1,7,-15),(x+4,8,9),(x+12,5,9)],.65,orange)
    line('Cable Micro USB interior',[(x-22,8,-27),(x-22,8,-34),(x-38,5,-36),(x-38,1,-44)],1.7,black)
    line('Cable sensor interior',[(x+12,4,9),(x+5,3,-31),(x,1,-44)],1.8,black)
    line('Cable temperatura interior',[(x+25,4,-11),(x+38,3,-30),(x+38,1,-44)],1.5,black)
    C=coll(('07 | Tapa desplazada' if opened else '06 | Tapa montada')+' - piezas gabinete')
    dz=108 if opened else 0
    lid=prism('Tapa frontal',x,-25.5,dz,W,H,4,lidmat);bevel(lid,.65)
    box('Franja identidad monocromatica',(x-48,-28,dz),(5,1,61),graphite,1)
    text('Marca impresa neiron','neiron', (x-35,-27.56,dz+20),6)
    cyl('Indicador sellado concepto',(x+36,-28,dz+21),2,1,orange)
    for a in [-48,48]:
        for z in [-33,33]:
            cyl('Tornillo cautivo referencia',(x+a,-28,dz+z),2.8,1.8,steel)
            box('Ranura tornillo',(x+a,-29,dz+z),(3,.3,.65),black,.1)
    if opened:
        for a in [-48,48]:line('Guia despiece',[(x+a,-24,40),(x+a,-24,70)],.15,steel)

cabinet(0,True)
C=coll('09 | Presentacion')
floor=material('Fondo',(.035,.048,.065),0,.8)
box('Fondo estudio',(0,90,15),(1200,5,1000),floor,0)
world=bpy.data.worlds.new('Estudio');s.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.17,.21,.27,1);world.node_tree.nodes['Background'].inputs[1].default_value=.4
def aim(o,p):o.rotation_euler=(Vector(p)*MM-o.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size in [('Principal',(-200,-260,400),2,.35),('Relleno',(350,-150,180),1.2,.3),('Borde',(0,45,320),1.5,.2)]:
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);C.objects.link(o);o.location=Vector(loc)*MM;aim(o,(0,0,10))
d=bpy.data.cameras.new('Camara revision');o=bpy.data.objects.new('Camara revision',d);C.objects.link(o);o.location=Vector((180,-650,220))*MM;aim(o,(0,0,44));d.type='ORTHO';d.ortho_scale=.275;s.camera=o
s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True
s.render.resolution_x=1300;s.render.resolution_y=1600;s.render.resolution_percentage=100
s.world.color=(.15,.15,.15);s.view_settings.view_transform='AgX'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.shading.type='MATERIAL'
            area.spaces.active.clip_end=100
info=bpy.data.texts.new('LEEME - P01')
info.write('Maqueta visual P01. Unidades reales en metros, interfaz milimetros.\nGabinete 120 x 90 x 55 mm. Hardware aproximado.\nUn solo gabinete abierto con tapa retirada y desplazada para inspeccion. Marca neiron impresa, no relieve de fabricacion.\nFuente USB-A externa 5 V 2 A; no incluida dentro.\nEntradas y junta conceptuales; sin validacion IP ni tolerancias de fabricacion.\nCable mostrado para composicion: no es patron de corte de 20 cm.\n')
(OUT/'blend_files').mkdir(parents=True,exist_ok=True);(OUT/'renders').mkdir(parents=True,exist_ok=True)
s.render.filepath=str(OUT/'renders'/'P01_neiron_abierto_v02.png')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'blend_files'/'P01_neiron_abierto_v02.blend'))
bpy.ops.render.render(write_still=True)
print('P01_COMPLETADO')
