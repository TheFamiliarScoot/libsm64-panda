import os
import sys
import ctypes as ct
from panda3d.core import *
from direct.task import Task
from from_blender import *

# Panda3D Python bindings for libsm64
# by TheFamiliarScoot

# TODO(patchmixolydic): needs a better name
SM64_BOUNDS = 0x7FFF

class UnsupportedOSError(Exception):
    pass

class SM64State:
    def __init__(self, dll_directory: str, dll_name_stub: str, rom_path: str):
        dll_full_name = None
        if sys.platform.startswith("darwin"):
            # TODO(patchmixolydic): is this right? i don't macOS
            dll_full_name = f"lib{dll_name_stub}.dylib"
        elif sys.platform == "win32" or sys.platform == "cygwin":
            dll_full_name = f"{dll_name_stub}.dll"
        elif sys.platform == "linux" or sys.platform.startswith("freebsd"):
            # TODO(patchmixolydic): this might also hold for AIX
            dll_full_name = f"lib{dll_name_stub}.so"
        else:
            raise UnsupportedOSError(f"libsm64-panda currently doesn't support your platform ({sys.platform})")

        texture_buff = init_sm64(self, os.path.join(dll_directory, dll_full_name), rom_path)

        # converts loaded texture from ROM
        img = PNMImage(SM64_TEXTURE_WIDTH, SM64_TEXTURE_HEIGHT)
        img.addAlpha()

        make_image(img, texture_buff)

        self.texture = Texture('MarioTex')
        self.texture.load(img)

        samp = SamplerState()
        samp.setMinfilter(SamplerState.FT_nearest)
        samp.setMagfilter(SamplerState.FT_nearest)

        self.texture.default_sampler = samp
        self.texture.setAnisotropicDegree(0)
        
        print("State created!")
    
    def __del__(self):
        self.sm64.sm64_global_terminate()

    # Creates a flat plane surface with a specified size
    def make_flat_plane_surface_array(self, size):
        tempsurf = (SM64Surface * 2)()
        tri1 = SM64Surface()
        tri1.surftype = COLLISION_TYPES['SURFACE_DEFAULT']
        tri1.terrain = COLLISION_TYPES['TERRAIN_GRASS']
        tri1.v0x = size
        tri1.v0y = 0
        tri1.v0z = -size
        tri1.v1x = -size
        tri1.v1y = 0
        tri1.v1z = -size
        tri1.v2x = -size
        tri1.v2y = 0
        tri1.v2z = size
        tempsurf[0] = tri1
        tri2 = SM64Surface()
        tri2.surftype = COLLISION_TYPES['SURFACE_DEFAULT']
        tri2.terrain = COLLISION_TYPES['TERRAIN_GRASS']
        tri2.v0x = size
        tri2.v0y = 0
        tri2.v0z = size
        tri2.v1x = size
        tri2.v1y = 0
        tri2.v1z = -size
        tri2.v2x = -size
        tri2.v2y = 0
        tri2.v2z = size
        tempsurf[1] = tri2

        self.sm64.sm64_static_surfaces_load(tempsurf, 2)

    # clamp to bounds
    # "inspired" by libsm64-blender
    def rebound(item):
        item = int(item)
        if item > SM64_BOUNDS:
            return SM64_BOUNDS
        if item < -SM64_BOUNDS:
            return -SM64_BOUNDS
        return item

    # Adds a specified amount of nodes to the static surfaces list
    # TODO(thefamiliarscoot) CURRENTLY BROKEN FIX IT
    def add_surface_triangles(self, *arg):
        tempdata = []

        # this sucks
        for model in arg:
            geomNodeCollection = model.findAllMatches('**/+GeomNode')

            modelpos = model.getPos()
            modelscale = model.getScale()
            for nodePath in geomNodeCollection:
                geomNode = nodePath.node()
                for i in range(geomNode.getNumGeoms()):
                    geom = geomNode.getGeom(i)

                    vdata = geom.getVertexData()

                    for j in range(geom.getNumPrimitives()):
                        prim = geom.getPrimitive(j).decompose()
                        vertex = GeomVertexReader(vdata, 'vertex')
                        for k in range(prim.getNumPrimitives()):
                            sf = SM64Surface()
                            s = prim.getPrimitiveStart(k)
                            e = prim.getPrimitiveEnd(k)
                            vertdata = []
                            for l in range(s, e):
                                vi = prim.getVertex(l)
                                vertex.setRow(vi)
                                v = vertex.getData3()
                                vertdata.append(v)
                            sf.surftype = COLLISION_TYPES['SURFACE_DEFAULT']
                            sf.terrain = COLLISION_TYPES['TERRAIN_GRASS']
                            # rip floats
                            sf.v0x = rebound((vertdata[0].getX() * modelscale.getX()) + modelpos.getX())
                            sf.v0y = rebound((vertdata[0].getY() * modelscale.getY()) + modelpos.getY())
                            sf.v0z = rebound((vertdata[0].getZ() * modelscale.getZ()) + modelpos.getZ())
                            sf.v1x = rebound((vertdata[1].getX() * modelscale.getX()) + modelpos.getX())
                            sf.v1y = rebound((vertdata[1].getY() * modelscale.getY()) + modelpos.getY())
                            sf.v1z = rebound((vertdata[1].getZ() * modelscale.getZ()) + modelpos.getZ())
                            sf.v2x = rebound((vertdata[2].getX() * modelscale.getX()) + modelpos.getX())
                            sf.v2y = rebound((vertdata[2].getY() * modelscale.getY()) + modelpos.getY())
                            sf.v2z = rebound((vertdata[2].getZ() * modelscale.getZ()) + modelpos.getZ())
                            tempdata.append(sf)
        
        surf = (SM64Surface * len(tempdata))()
        for i in range(len(tempdata)):
            surf[i] = tempdata[i]

        self.sm64.sm64_static_surfaces_load(surf, len(surf))

class SM64Mario(NodePath):
    # Vertex Formats
    vf_array = GeomVertexArrayFormat()
    vf_array.addColumn("vertex", 3, Geom.NTFloat32, Geom.CPoint)
    vf_array.addColumn("normal", 3, Geom.NTFloat32, Geom.CNormal)
    vf_array.addColumn("color", 3, Geom.NTFloat32, Geom.CColor)
    vf_array.addColumn("texcoord", 2, Geom.NTFloat32, Geom.CTexcoord)

    vformat = GeomVertexFormat()
    vformat.addArray(vf_array)
    vformat = GeomVertexFormat.registerFormat(vformat)
    
    # Shaders
    shader = Shader.load(Shader.SL_GLSL,
                     vertex="shaders/mario.vsh",
                     fragment="shaders/mario.fsh")

    def __init__(self, showbase, state, pos):
        self.mario_node = GeomNode('MarioNode')

        # nodepath things
        NodePath.__init__(self, self.mario_node)
        NodePath.setPos(self, pos.getX(), pos.getY(), pos.getZ())
        NodePath.setHpr(self, 0, 90, 0)

        self.mario_id = -1
        self.tick_count = 0

        if showbase == None:
            print("Showbase does not exist!")
            del self
            return
        if state == None:
            print("State does not exist!")
            del self
            return
        
        # buffers
        self.mario_inputs = SM64MarioInputs()
        self.mario_state = SM64MarioState()
        self.mario_geo = SM64MarioGeometryBuffers()

        # state-related things
        self.sm64_state = state
        self.mario_id = self.sm64_state.sm64.sm64_mario_create(int(pos.getX()), int(pos.getY()), int(pos.getZ()))
        if self.mario_id == -1:
            print("Couldn't create this Mario! Is there solid ground at that position?")
            del self
            return
        self.mario_task_name = 'MarioTick' + str(self.mario_id)
        self.setName('MarioNode' + str(self.mario_id))

        # vertex data
        self.mario_vdata = None

        # textures
        NodePath.setTexture(self, self.sm64_state.texture)
        NodePath.setShader(self, SM64Mario.shader)

        # task
        showbase.taskMgr.add(self.mario_tick, self.mario_task_name)

        # let the user know
        print("Mario (id " + str(self.mario_id) + ") created and spawned at " + str(pos))
    
    # Builds the VertexData for Mario's geometry
    def make_mario_vdata(self, fmt, geo):
        vdata = GeomVertexData('mario-vertex', fmt, Geom.UHDynamic)
        vdata.setNumRows(SM64_GEO_MAX_TRIANGLES * 3)

        position = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        color = GeomVertexWriter(vdata, 'color')
        uv = GeomVertexWriter(vdata, 'texcoord')

        for i in range(SM64_GEO_MAX_TRIANGLES * 3):
            x = (geo.position_data[3*i] - self.mario_state.posX) / SM64_SCALE_FACTOR
            y = (geo.position_data[3*i+1] - self.mario_state.posY) / SM64_SCALE_FACTOR
            z = (geo.position_data[3*i+2] - self.mario_state.posZ) / SM64_SCALE_FACTOR
            position.addData3(x, y, z)

            nx = geo.normal_data[3*i]
            ny = geo.normal_data[3*i+1]
            nz = geo.normal_data[3*i+2]
            normal.addData3(nx, ny, nz)

            r = geo.color_data[3*i]
            g = geo.color_data[3*i+1]
            b = geo.color_data[3*i+2]
            color.addData3(r, g, b)

            u = geo.uv_data[2*i]
            v = -geo.uv_data[2*i+1]
            uv.addData2(u, v)
        
        return vdata

    # Intended to be run as a task
    def mario_tick(self, task):
        # quick 30fps hack
        if self.tick_count % 2 == 0:
            # for this mario, we should:

            # tick him natively first
            try:
                self.sm64_state.sm64.sm64_mario_tick(self.mario_id, ct.byref(self.mario_inputs), ct.byref(self.mario_state), ct.byref(self.mario_geo))
            except:
                print("Mario (id " + str(self.mario_id) + ") crashed or is untickable")
                return Task.done

            # update the node
            ms = self.mario_state
            NodePath.setPos(self, ms.posX / SM64_SCALE_FACTOR, -ms.posZ / SM64_SCALE_FACTOR, ms.posY / SM64_SCALE_FACTOR)

            # update his visual geometry

            # generates vertex data from a geo
            self.mario_vdata = self.make_mario_vdata(SM64Mario.vformat, self.mario_geo)

            if self.tick_count == 0:
                # primitive data should remain the same, since triangles will not be modified - only vertices
                prim = GeomTriangles(Geom.UHDynamic)
                for i in range(self.mario_geo.numTrianglesUsed): prim.addNextVertices(3)
                prim.closePrimitive()

                self.mario_geom = Geom(self.mario_vdata)
                self.mario_geom.addPrimitive(prim)

                self.mario_node.addGeom(self.mario_geom)
            else:
                self.mario_geom.setVertexData(self.mario_vdata)

        #   print("Ticked Mario position: " + str(self.getPos()))
                
        self.tick_count += 1
        return Task.cont

    def __del__(self):
        if hasattr(self, 'mario_task_name'):
            self.showbase.taskMgr.remove(self.mario_task_name)
        if self.mario_id != -1:
            self.sm64_state.sm64_mario_delete(self.mario_id)
    
    def setPos(self, x, y, z):
        if self.mario_id != -1:
            self.mario_state.posX = x
            self.mario_state.posY = y
            self.mario_state.posZ = z

    def setVel(self, x, y, z):
        self.mario_state.velX = x
        self.mario_state.velY = y
        self.mario_state.velZ = z
    
    def get_input_buttons(self, a: bool, b: bool, z: bool):
        self.mario_inputs.buttonA = int(a)
        self.mario_inputs.buttonB = int(b)
        self.mario_inputs.buttonZ = int(z)

    def get_input_stick(self, x: float, y: float):
        self.mario_inputs.stickX = x
        self.mario_inputs.stickY = y

    def get_input_camera(self, x: float, y: float):
        self.mario_inputs.camLookX = x
        self.mario_inputs.camLookY = y

