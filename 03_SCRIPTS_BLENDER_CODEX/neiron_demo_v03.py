"""Escena educativa animada; geometria y lecturas ilustrativas, no telemetria real."""
from pathlib import Path
BASE=Path(__file__).resolve().parent
exec(compile((BASE/'prototipo_01_neiron_v02.py').read_text(encoding='utf-8').split('\ncabinet(0,True)')[0],str(BASE/'prototipo_01_neiron_v02.py'),'exec'))
s.name='neiron | Lavadora - demostracion'
s.frame_start=1;s.frame_end=240;s.render.fps=24
cyan=material('Datos / cian',(.02,.65,.85),.1,.28)
amber=material('Movimiento / naranja',(.95,.32,.05))
housing=material('Lavadora gris claro',(.42,.49,.51),.3,.4)
dark=material('Pantallas',(.008,.025,.038))
wallmat=material('Entorno neutro',(.095,.125,.15))
lightmat=material('Detalles claros',(.67,.75,.78))

def empty(name,loc=(0,0,0)):
    o=bpy.data.objects.new(name,None);C.objects.link(o);o.location=Vector(loc)*MM;return o
def sphere(name,loc,r,mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=r*MM,location=Vector(loc)*MM)
    return assign(bpy.context.object,name,mat)
def arrow(name,pts,mat,r=3):
    o=line(name,pts,r,mat)
    p=Vector(pts[-1]);v=(p-Vector(pts[-2])).normalized()
    bpy.ops.mesh.primitive_cone_add(vertices=24,radius1=r*3,radius2=0,depth=r*9*MM,location=(p-v*r*4.5)*MM)
    tip=bpy.context.object;tip.scale=(MM,MM,1);tip.rotation_euler=v.to_track_quat('Z','Y').to_euler();assign(tip,name+' flecha',mat)
    return o
def ring(name,center,r,mat,axis='Z',thick=3):
    pts=[]
    for i in range(97):
        a=i*math.tau/96
        pts.append((center[0]+r*math.cos(a),center[1]+(r*math.sin(a) if axis=='Z' else 0),center[2]+(r*math.sin(a) if axis=='Y' else 0)))
    return line(name,pts,thick,mat)
def camera(name,loc,target,scale):
    d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);C.objects.link(o);o.location=Vector(loc)*MM
    o.rotation_euler=(Vector(target)*MM-o.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=scale;return o
def packets(name,pts,mat,start=1):
    for j in range(3):
        o=sphere(name+str(j),pts[0],6,mat)
        for cycle in range(-1,5):
            for i,p in enumerate(pts):
                f=start+j*16+cycle*64+i*48/(len(pts)-1)
                o.location=Vector(p)*MM;o.keyframe_insert(data_path='location',frame=f)

C=coll('10 | Entorno esencial - referencia fotografica')
box('Suelo limpio',(100,120,-18),(2450,950,25),wallmat,8)
box('Pared posterior simplificada',(-550,425,470),(1050,15,980),wallmat,4)
for x in [-950,-700,-450,-200]:box('Junta panel pared',(x,414,470),(2,1,950),graphite,.1)
# Solo una toma de agua de referencia. No se reproduce calefon ni objetos del entorno.
line('Tuberia agua referencia',[(-190,399,0),(-190,399,650),(-235,399,650)],8,steel)
box('Llave referencia',(-218,383,668),(45,8,7),amber,2)

C=coll('11 | Lavadora - corte didactico NO replica mecanica')
box('Panel izquierdo',(-895,90,430),(16,530,780),housing,8)
box('Panel trasero',(-650,353,430),(500,12,780),housing,8)
box('Zocalo',(-650,90,45),(500,530,65),housing,15)
box('Marco frontal izquierdo',(-860,-170,420),(58,16,700),housing,8)
box('Marco frontal derecho',(-440,-170,420),(58,16,700),housing,8)
box('Panel inferior',(-650,-171,125),(390,15,90),housing,8)
box('Tapa superior',(-650,90,838),(530,550,35),housing,18)
box('Ventana tapa',(-650,130,859),(360,320,9),dark,20)
box('Panel mandos',(-650,-116,862),(400,105,13),lidmat,10)
for x in [-760,-710,-660]:cyl('Boton lavadora',(x,-125,873),12,5,lightmat,'Z')
box('Display lavadora',(-570,-125,873),(90,38,4),dark,3)
text('Nombre lavadora','LAVADORA / CARGA SUPERIOR',(-867,-184,802),15)
drum=cyl('Tambor - esquema',(-650,100,500),185,430,steel,'Z')
for z in [290,710]:ring('Aro tambor',(-650,100,z),188,lidmat,'Z',7)
for i in range(20):
    a=i*math.tau/20
    rib=line('Nervio tambor',[(-650+187*math.cos(a),100+187*math.sin(a),315),(-650+187*math.cos(a),100+187*math.sin(a),690)],2,graphite)
    rib.parent=drum;rib.matrix_parent_inverse=drum.matrix_world.inverted()
rotor=cyl('Motor ilustrativo',(-650,85,220),76,95,graphite,'Z')
cyl('Eje esquema',(-650,85,281),12,60,steel,'Z')
for i in range(8):
    a=i*math.tau/8;o=box('Aleta motor',(-650+65*math.cos(a),85+65*math.sin(a),220),(13,13,80),lidmat,2)
arrow('Movimiento motor',[(-765,-30,235),(-770,-70,275),(-745,-85,295)],amber,4)
text('Motor aclaracion','MOTOR / ESQUEMA',(-817,-196,235),17,amber)
text('Corte aclaracion','Corte didactico: mecanismo interno no verificado',(-900,-203,6),10)
for f,a in [(1,0),(240,math.tau*10)]:
    drum.rotation_euler.z=a;drum.keyframe_insert('rotation_euler',frame=f)

# Gabinete fisico detras, cercano al sensor. Una copia ampliada explica su interior.
before=set(bpy.data.objects);cabinet(0,False)
C=coll('12 | Instalacion posterior - nodo a escala')
node=empty('neiron instalado',(-320,386,690))
for o in set(bpy.data.objects)-before:
    if o!=node:o.parent=node
C=coll('13 | Sensores y alimentacion fisica')
prism('Cabezal MPU6050 sobre carcasa',-435,340,643,42,30,18,graphite,4)
box('Contacto rigido sensor',(-435,351,643),(38,4,25),steel)
cyl('Sonda DS18B20 - superficie',(-442,340,607),4,30,steel,'Z')
sensorpath=[(-435,331,643),(-408,320,643),(-395,321,600),(-320,322,600),(-320,387,632)]
line('Cable sensor recorrido ilustrativo',sensorpath,2.2,black)
line('Cable sonda',[(-442,340,592),(-425,320,585),(-282,321,585),(-282,387,632)],1.8,black)
box('Adaptador externo USB 5V 2A',(-190,383,824),(40,38,60),graphite,4)
line('Alimentacion USB',[(-190,362,796),(-210,320,760),(-358,320,748),(-380,320,600),(-358,387,632)],2,black)

# Detalle ampliado x3 con tapa desplazada lateralmente durante demostracion.
before=set(bpy.data.objects);cabinet(0,False)
C=coll('14 | Detalle ampliado neiron x3')
detail=empty('DETALLE x3', (180,-180,560));detail.scale=(3,3,3)
lidparts=[]
for o in set(bpy.data.objects)-before:
    if o!=detail:
        o.parent=detail
        if any(c.name.startswith('06 | Tapa') for c in o.users_collection):lidparts.append(o)
lidpivot=empty('Abrir tapa - animacion');lidpivot.parent=detail
for o in lidparts:o.parent=lidpivot
for f,pos in [(1,(0,0,0)),(40,(0,0,0)),(80,(0,-15,105)),(190,(0,-15,105)),(240,(0,0,0))]:
    lidpivot.location=Vector(pos)*MM;lidpivot.keyframe_insert('location',frame=f)

C=coll('15 | Router y PC - flujo de datos')
box('Router WiFi',(625,30,720),(170,65,40),graphite,10)
for x in [568,678]:cyl('Antena router',(x,48,787),5,110,black,'Z')
for x in [578,594,610]:sphere('LED router',(x,-5,720),3,cyan)
box('Monitor PC',(1000,50,575),(390,30,255),graphite,12)
box('Pantalla PC',(1000,33,575),(357,2,223),dark,3)
box('Pie monitor',(1000,55,390),(30,40,140),steel,4)
box('Base monitor',(1000,25,326),(190,140,12),graphite,6)
box('Teclado',(1000,-95,322),(275,100,10),lidmat,5)
text('Dashboard marca','neiron / seguimiento', (840,29,650),17)
text('Dashboard demo','DATOS SIMULADOS', (840,29,623),10,amber)
text('Dashboard vib','Vibracion relativa', (840,29,597),11)
pts=[(841+i*5,28,560+15*math.sin(i*.7)*(0.3+0.7*math.sin(i*.05)**2)) for i in range(62)]
line('Grafico vibracion ilustrativo',pts,1.3,cyan)
text('Dashboard temp','Superficie: 27.4 C  /  ejemplo',(840,29,511),11)
text('Dashboard estado','Historial + comparacion de ciclos',(840,29,482),10)

C=coll('16 | Flujo animado - no cables reales')
arrow('Ampliacion visual',[(-313,315,699),(-235,140,730),(-140,90,650)],lightmat,2)
wifi1=[(340,-80,600),(435,-80,670),(520,-80,720)]
wifi2=[(708,-60,720),(785,-60,720),(825,-60,665)]
arrow('WiFi neiron a router',wifi1,cyan,3);arrow('Red a PC',wifi2,cyan,3)
packets('Paquete WiFi ',wifi1,cyan);packets('Paquete PC ',wifi2,cyan,20)
for r in [25,42,59]:
    pts=[(425+r*math.cos(a),-83,795+r*math.sin(a)) for a in [math.pi/6+i*math.pi/30 for i in range(21)]]
    line('Ondas WiFi',pts,2,cyan)
arrow('Vibracion transmitida a carcasa',[(-585,-195,260),(-445,-195,360),(-410,300,625)],amber,2)

C=coll('17 | Explicaciones')
text('Titulo','neiron',(-930,-500,1390),64)
text('Bajada','DE LA LAVADORA A LOS DATOS',(-930,-500,1332),23)
text('Lectura','Demostracion animada / instalacion posterior / entorno simplificado',(-930,-500,1290),15)
text('Paso1','01  MEDIR',(-905,-500,1180),23,amber)
text('Paso1b','Vibracion y temperatura de carcasa',(-905,-500,1149),12)
text('Paso2','02  ADQUIRIR',(-20,-500,1180),23,cyan)
text('Paso2b','ESP32: indicadores cada segundo',(-20,-500,1149),12)
text('Paso3','03  TRANSMITIR',(505,-500,1180),23,cyan)
text('Paso3b','Wi-Fi / router',(505,-500,1149),12)
text('Paso4','04  INTERPRETAR',(915,-500,1180),23,cyan)
text('Paso4b','PC: guardar y comparar',(915,-500,1149),12)
text('Ubicacion','NODO DETRAS',(-350,280,808),14)
text('Sensor aclaracion','Sensores sobre carcasa',(-478,240,555),11)
text('Detalle label','DETALLE AMPLIADO x3',(-30,-180,353),17)
text('Detalle label2','Tapa animada / hardware aproximado',(-30,-180,326),11)
text('PC resultado','Observar lavado y centrifugado',(830,-150,253),15)
text('Limite','No diagnostica por si solo rodamientos ni vida util.',(830,-150,227),10)
text('Footer','ESPACIO: reproducir  |  Arrastra la linea de tiempo  |  Rueda: acercar  |  Boton central: orbitar',(-930,-650,60),16)
text('Disclaimer','Esquema educativo. Temperatura superficial, no temperatura interna del motor. Datos simulados.',(-930,-650,25),12)

C=coll('18 | Camaras y luces')
main=camera('01 Vista general',(650,-3500,1550),(100,0,600),2.8)
rear=camera('02 Instalacion posterior',(-20,-100,1150),(-400,335,690),.65)
camera('03 Interior neiron',(470,-1100,940),(120,0,600),.9)
s.camera=main
world=bpy.data.worlds.new('Estudio demo');s.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.11,.16,.22,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45
for name,loc,power,size in [('Principal',(-1000,-1500,2400),70,2),('Relleno',(1800,-900,1600),50,1.5),('Contraluz',(0,1000,2000),60,1.2)]:
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.size=size;o=bpy.data.objects.new(name,d);C.objects.link(o);o.location=Vector(loc)*MM;o.rotation_euler=(Vector((0,0,500))*MM-o.location).to_track_quat('-Z','Y').to_euler()
for f,n in [(1,'Inicio / movimiento'),(40,'Abrir neiron'),(80,'Interior y adquisicion'),(140,'WiFi y PC'),(190,'Cerrar tapa')]:s.timeline_markers.new(n,frame=f)
s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True
s.render.resolution_x=2200;s.render.resolution_y=1400;s.render.resolution_percentage=100;s.view_settings.view_transform='AgX'
s.frame_set(120)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            sp=area.spaces.active;sp.region_3d.view_perspective='CAMERA';sp.shading.type='MATERIAL';sp.clip_end=100;sp.overlay.show_overlays=False
info=bpy.data.texts.new('LEEME - Demostracion neiron')
info.write('ESPACIO sobre linea de tiempo: reproducir/pausar. Fotogramas 1-240.\nTapa animada y paquetes ilustrativos. Se puede orbitar y seleccionar objetos.\nCamaras adicionales en coleccion 18: posterior y detalle.\nLa copia x3 explica el gabinete instalado; NO es un segundo dispositivo.\nMotor y tambor esquematicos, dimensiones lavadora no verificadas.\nSensores en carcasa: vibracion general y temperatura superficial. No se infiere temperatura interna ni diagnostico de rodamientos.\nLecturas PC SIMULADAS; no conexion a hardware. Cable de 20 cm objetivo sujeto a recorrido real.\n')
(OUT/'blend_files').mkdir(parents=True,exist_ok=True);(OUT/'renders').mkdir(parents=True,exist_ok=True)
s.render.filepath=str(OUT/'renders'/'neiron_lavadora_demo_v03.png')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'blend_files'/'neiron_lavadora_demo_v03.blend'))
bpy.ops.render.render(write_still=True)
print('DEMO_COMPLETADA')
