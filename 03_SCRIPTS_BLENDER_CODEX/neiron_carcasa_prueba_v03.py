"""Cuerpo y tapa vacíos para impresión de PRUEBA: escala mm y mallas comprobadas."""
from pathlib import Path
BASE=Path(__file__).resolve().parent
exec(compile((BASE/'prototipo_01_neiron_v02.py').read_text(encoding='utf-8').split('\ncabinet(0,True)')[0],str(BASE/'prototipo_01_neiron_v02.py'),'exec'))
from mathutils import Matrix
import struct
s.name='neiron | Cuerpo y tapa - prueba FDM'
C=coll('SOLO PIEZAS IMPRIMIBLES')
def boolean(obj,tool,operation):
    bpy.context.view_layer.objects.active=obj
    m=obj.modifiers.new(operation,'BOOLEAN');m.operation=operation;m.solver='EXACT';m.object=tool
    bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(tool,do_unlink=True)
body=prism('neiron cuerpo - 120x90x51',0,2,0,120,90,51,graphite)
cut=prism('Cavidad',0,-2,0,114,84,53,None,4);boolean(body,cut,'DIFFERENCE')
for x in [-48,48]:
    for z in [-33,33]:
        post=cyl('Pilar',(x,1,z),5,49,None)
        # Boolean sobre malla simple sin modificadores decorativos.
        post.modifiers.clear();boolean(body,post,'UNION')
        pilot=cyl('Piloto M3 a repasar',(x,-22,z),1.25,20,None);pilot.modifiers.clear();boolean(body,pilot,'DIFFERENCE')
# Sin aperturas no dimensionadas: tres marcas exteriores para futura entrada comercial.
for x in [-38,0,38]:
    mark=cyl('Centro futura entrada',(x,1,-45),.6,1,None,'Z');mark.modifiers.clear();boolean(body,mark,'DIFFERENCE')
lid=prism('neiron tapa - 120x90x4',0,-25.5,0,120,90,4,lidmat)
for x in [-48,48]:
    for z in [-33,33]:
        hole=cyl('Paso M3',(x,-25.5,z),1.7,10,None);hole.modifiers.clear();boolean(lid,hole,'DIFFERENCE')
# Orientacion FDM: fondo cuerpo a cama, apertura hacia arriba; tapa cara externa a cama.
body.data.transform(Matrix.Rotation(-math.pi/2,4,'X'));body.data.transform(Matrix.Translation((0,0,27.5*MM)))
lid.data.transform(Matrix.Rotation(math.pi/2,4,'X'));lid.data.transform(Matrix.Translation((140*MM,0,27.5*MM)))

results={}
def validate_export(o,path):
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bad=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume(signed=True)
    assert bad==0,(o.name,bad)
    assert volume>0,(o.name,volume)
    # Una sola componente conectada por pieza.
    unseen=set(bm.verts);components=0
    while unseen:
        components+=1;stack=[unseen.pop()]
        while stack:
            for edge in stack.pop().link_edges:
                for v in edge.verts:
                    if v in unseen:unseen.remove(v);stack.append(v)
    assert components==1,(o.name,components)
    bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(o.data)
    verts=[v.co for v in bm.verts]
    dims=[(max(v[i] for v in verts)-min(v[i] for v in verts))*1000 for i in range(3)]
    assert all(abs(a-b)<.01 for a,b in zip(dims,[120,90,51 if o==body else 4])),dims
    assert min(v.z for v in verts)>-1e-7
    # STL numerico en mm, por pieza centrada en XY. Sin dependencia del exportador/version.
    mn=[min(v[i] for v in verts) for i in range(3)]
    faces=list(bm.faces)
    with path.open('wb') as f:
        f.write(b'neiron P01 PRUEBA FDM - unidades mm'.ljust(80,b' '));f.write(struct.pack('<I',len(faces)))
        for face in faces:
            xyz=[(v.co[i]-mn[i])*1000 for v in face.verts for i in range(3)]
            f.write(struct.pack('<12fH',*face.normal,*xyz,0))
    results[o.name]={'dimensiones_mm':dims,'aristas_no_manifold':bad,'componentes':components,'volumen_mm3':volume*1e9,'triangulos':len(faces),'stl':str(path)}
    bm.free()
out=OUT/'impresion_prueba';out.mkdir(parents=True,exist_ok=True)
validate_export(body,out/'neiron_cuerpo_120x90x51_PRUEBA.stl')
validate_export(lid,out/'neiron_tapa_120x90x4_PRUEBA.stl')
(out/'validacion_geometria.json').write_text(json.dumps(results,indent=2),encoding='utf-8')

info=bpy.data.texts.new('LEEME - Antes de imprimir')
info.write('SOLO CUERPO Y TAPA. Primera prueba de ajuste, no recinto IP54 validado.\nCuerpo 120x90x51 mm; tapa 120x90x4. Paredes y fondo 3 mm.\n4 pilotos diametro 2.5 mm para repasar/roscar M3; tapa 4 pasos 3.4 mm.\nLongitud tornillo depende mecanizado final; tornilleria no incluida.\nEntradas sin abrir: 3 marcas guia. Elegir prensaestopas y perforar a su cota.\nSin ranura de junta ni soporte mural funcional; pendientes antes de uso final.\nSTL separados en mm, cada pieza cabe en 120x90; imprimir por separado.\nNo perfil ni G-code: impresora aun no seleccionada.\n')
for o in bpy.context.selected_objects:o.select_set(False)
body.select_set(True);lid.select_set(True);bpy.context.view_layer.objects.active=body
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            sp=area.spaces.active;sp.shading.type='SOLID';sp.shading.color_type='MATERIAL';sp.region_3d.view_distance=.37;sp.region_3d.view_location=Vector((.07,0,.02));sp.region_3d.view_rotation=Vector((1,-1,1.8)).to_track_quat('Z','Y');sp.clip_end=100
(OUT/'blend_files').mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'blend_files'/'neiron_carcasa_y_tapa_PRUEBA_v03.blend'))
print(json.dumps(results))
# Render de control aparte: las camaras y luces NO se guardan en el archivo de dos piezas.
C=coll('Temporal render')
d=bpy.data.cameras.new('Camara');o=bpy.data.objects.new('Camara',d);C.objects.link(o);o.location=(.25,-.3,.35);o.rotation_euler=(Vector((.07,0,.015))-o.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=.32;s.camera=o
world=bpy.data.worlds.new('Fondo control');s.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.20,.25,1);world.node_tree.nodes['Background'].inputs[1].default_value=.6
for pos,power in [((-.1,-.2,.4),3),((.3,.2,.3),2)]:
    d=bpy.data.lights.new('Luz','AREA');d.energy=power;d.size=.3;o=bpy.data.objects.new('Luz',d);C.objects.link(o);o.location=pos;o.rotation_euler=(Vector((.07,0,0))-o.location).to_track_quat('-Z','Y').to_euler()
s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=True;s.render.resolution_x=1400;s.render.resolution_y=900;s.render.resolution_percentage=100
s.render.filepath=str(OUT/'renders'/'neiron_piezas_impresion_v03.png');bpy.ops.render.render(write_still=True)
