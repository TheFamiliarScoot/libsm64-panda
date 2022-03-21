import os
import ctypes as ct
from panda3d.core import *
from direct.task import Task

# Panda3D Python bindings for libsm64
# by TheFamiliarScoot

SM64_TEXTURE_WIDTH = 64 * 11
SM64_TEXTURE_HEIGHT = 64
SM64_GEO_MAX_TRIANGLES = 1024
SM64_SCALE_FACTOR = 1

class SM64Surface(ct.Structure):
    _fields_ = [
        ('surftype', ct.c_int16),
        ('force', ct.c_int16),
        ('terrain', ct.c_uint16),
        ('v0x', ct.c_int16), ('v0y', ct.c_int16), ('v0z', ct.c_int16),
        ('v1x', ct.c_int16), ('v1y', ct.c_int16), ('v1z', ct.c_int16),
        ('v2x', ct.c_int16), ('v2y', ct.c_int16), ('v2z', ct.c_int16)
    ]

class SM64MarioInputs(ct.Structure):
    _fields_ = [
        ('camLookX', ct.c_float), ('camLookZ', ct.c_float),
        ('stickX', ct.c_float), ('stickY', ct.c_float),
        ('buttonA', ct.c_ubyte), ('buttonB', ct.c_ubyte), ('buttonZ', ct.c_ubyte),
    ]

class SM64MarioState(ct.Structure):
    _fields_ = [
        ('posX', ct.c_float), ('posY', ct.c_float), ('posZ', ct.c_float),
        ('velX', ct.c_float), ('velY', ct.c_float), ('velZ', ct.c_float),
        ('faceAngle', ct.c_float),
        ('health', ct.c_int16),
    ]

class SM64MarioGeometryBuffers(ct.Structure):
    _fields_ = [
        ('position', ct.POINTER(ct.c_float)),
        ('normal', ct.POINTER(ct.c_float)),
        ('color', ct.POINTER(ct.c_float)),
        ('uv', ct.POINTER(ct.c_float)),
        ('numTrianglesUsed', ct.c_uint16)
    ]

    def __init__(self):
        self.position_data = (ct.c_float * (SM64_GEO_MAX_TRIANGLES * 3 * 3))()
        self.position = ct.cast(self.position_data , ct.POINTER(ct.c_float))
        self.normal_data = (ct.c_float * (SM64_GEO_MAX_TRIANGLES * 3 * 3))()
        self.normal = ct.cast(self.normal_data , ct.POINTER(ct.c_float))
        self.color_data = (ct.c_float * (SM64_GEO_MAX_TRIANGLES * 3 * 3))()
        self.color = ct.cast(self.color_data , ct.POINTER(ct.c_float))
        self.uv_data = (ct.c_float * (SM64_GEO_MAX_TRIANGLES * 3 * 2))()
        self.uv = ct.cast(self.uv_data , ct.POINTER(ct.c_float))
        self.numTrianglesUsed = 0

    def __del__(self):
        pass

class SM64State:
    def __init__(self, dll_path: str, rom_path: str):
        self.sm64 = ct.cdll.LoadLibrary(dll_path)

        self.sm64.sm64_global_init.argtypes = [ ct.c_char_p, ct.POINTER(ct.c_ubyte), ct.c_char_p ]
        self.sm64.sm64_static_surfaces_load.argtypes = [ ct.POINTER(SM64Surface), ct.c_uint32 ]
        self.sm64.sm64_mario_create.argtypes = [ ct.c_int16, ct.c_int16, ct.c_int16 ]
        self.sm64.sm64_mario_create.restype = ct.c_int32
        self.sm64.sm64_mario_tick.argtypes = [ ct.c_uint32, ct.POINTER(SM64MarioInputs), ct.POINTER(SM64MarioState), ct.POINTER(SM64MarioGeometryBuffers) ]

        with open(os.path.expanduser(rom_path), 'rb') as file:
            rom_bytes = bytearray(file.read())
            rom_chars = ct.c_char * len(rom_bytes)
            texture_buff = (ct.c_ubyte * (4 * SM64_TEXTURE_WIDTH * SM64_TEXTURE_HEIGHT))()
            self.sm64.sm64_global_init(rom_chars.from_buffer(rom_bytes), texture_buff, None)
        
        print(self.sm64)
        print("State created!")
    
    def __del__(self):
        self.sm64.sm64_global_terminate()

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

        print(tempsurf)
        print(tri1)
        print(tri2)
        self.sm64.sm64_static_surfaces_load(tempsurf, 2)
    
    # Adds a specified amount of nodes to the static surfaces list
    def add_surface_triangles(self, *arg):
        tempdata = []

        def rebound(item):
            item = int(item)
            bounds = 0x7FFF
            if item > bounds:
                return bounds
            if item < -bounds:
                return -bounds
            return item

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
    vf_array.addColumn("position", 3, Geom.NTFloat32, Geom.CPoint)
    vf_array.addColumn("normal", 3, Geom.NTFloat32, Geom.CNormal)
    vf_array.addColumn("color", 3, Geom.NTFloat32, Geom.CColor)
    vf_array.addColumn("uv", 2, Geom.NTFloat32, Geom.CTexcoord)

    vformat = GeomVertexFormat()
    vformat.addArray(vf_array)
    vformat = GeomVertexFormat.registerFormat(vformat)

    def __init__(self, showbase, state, pos):
        self.mario_node = GeomNode('MarioNode')
        NodePath.__init__(self, self.mario_node)
        NodePath.setPos(self, pos.getX(), pos.getY(), pos.getZ())

        self.mario_id = -1
        self.tick_count = 0
        self.mario_scale = 1

        if showbase == None:
            print("Showbase does not exist!")
            del self
            return
        if state == None:
            print("State does not exist!")
            del self
            return
        
        self.mario_inputs = SM64MarioInputs()
        self.mario_state = SM64MarioState()
        self.mario_geo = SM64MarioGeometryBuffers()
        self.sm64_state = state
        self.mario_id = self.sm64_state.sm64.sm64_mario_create(int(pos.getX()), int(pos.getY()), int(pos.getZ()))
        if self.mario_id == -1:
            print("Couldn't create this Mario! Is there solid ground at that position?")
            del self
            return
        self.mario_task_name = 'MarioTick' + str(self.mario_id)
        self.setName('MarioNode' + str(self.mario_id))

        self.mario_vdata = None

        showbase.taskMgr.add(self.mario_tick, self.mario_task_name)
        print("Mario (id " + str(self.mario_id) + ") created and spawned at " + str(pos))
    
    # Builds the VertexData for Mario's geometry
    def make_mario_vdata(self, fmt, geo):
        vdata = GeomVertexData('mario-vertex', fmt, Geom.UHDynamic)
        vdata.setNumRows(geo.numTrianglesUsed * 3)

        position = GeomVertexWriter(vdata, 'position')
        normal = GeomVertexWriter(vdata, 'normal')
        color = GeomVertexWriter(vdata, 'color')
        uv = GeomVertexWriter(vdata, 'uv')

        for i in range(geo.numTrianglesUsed):
            x = geo.position_data[3*i] / SM64_SCALE_FACTOR
            y = geo.position_data[3*i+1] / SM64_SCALE_FACTOR
            z = geo.position_data[3*i+2] / SM64_SCALE_FACTOR
            position.addData3(x, y, z)

            nx = geo.normal_data[3*i]
            ny = geo.normal_data[3*i+1]
            nz = geo.normal_data[3*i+2]
            normal.addData3(nx, ny, nz)

            r = geo.color_data[3*i]
            g = geo.color_data[3*i+1]
            b = geo.color_data[3*i+2]
            color.addData4(r, g, b, 0xFF)

            u = geo.uv_data[2*i]
            v = geo.uv_data[2*i+1]
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
            NodePath.setPos(self, ms.posX, ms.posY, ms.posZ)

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
            showbase.taskMgr.remove(self.mario_task_name)
        if self.mario_id != -1:
            self.sm64_state.sm64_mario_delete(self.mario_id)
    
    def setPos(self, x, y, z):
        NodePath.setPos(self, x, y, z)

        if self.mario_id != -1:
            # we should let the simulated mario know we updated his position, too
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

COLLISION_TYPES = {
    "SURFACE_DEFAULT": 0x0000,
    "SURFACE_BURNING": 0x0001,
    "SURFACE_0004": 0x0004,
    "SURFACE_HANGABLE": 0x0005,
    "SURFACE_SLOW": 0x0009,
    "SURFACE_DEATH_PLANE": 0x000A,
    "SURFACE_CLOSE_CAMERA": 0x000B,
    "SURFACE_WATER": 0x000D,
    "SURFACE_FLOWING_WATER": 0x000E,
    "SURFACE_INTANGIBLE": 0x0012,
    "SURFACE_VERY_SLIPPERY": 0x0013,
    "SURFACE_SLIPPERY": 0x0014,
    "SURFACE_NOT_SLIPPERY": 0x0015,
    "SURFACE_TTM_VINES": 0x0016,
    "SURFACE_MGR_MUSIC": 0x001A,
    "SURFACE_INSTANT_WARP_1B": 0x001B,
    "SURFACE_INSTANT_WARP_1C": 0x001C,
    "SURFACE_INSTANT_WARP_1D": 0x001D,
    "SURFACE_INSTANT_WARP_1E": 0x001E,
    "SURFACE_SHALLOW_QUICKSAND": 0x0021,
    "SURFACE_DEEP_QUICKSAND": 0x0022,
    "SURFACE_INSTANT_QUICKSAND": 0x0023,
    "SURFACE_DEEP_MOVING_QUICKSAND": 0x0024,
    "SURFACE_SHALLOW_MOVING_QUICKSAND": 0x0025,
    "SURFACE_QUICKSAND": 0x0026,
    "SURFACE_MOVING_QUICKSAND": 0x0027,
    "SURFACE_WALL_MISC": 0x0028,
    "SURFACE_NOISE_DEFAULT": 0x0029,
    "SURFACE_NOISE_SLIPPERY": 0x002A,
    "SURFACE_HORIZONTAL_WIND": 0x002C,
    "SURFACE_INSTANT_MOVING_QUICKSAND": 0x002D,
    "SURFACE_ICE": 0x002E,
    "SURFACE_LOOK_UP_WARP": 0x002F,
    "SURFACE_HARD": 0x0030,
    "SURFACE_WARP": 0x0032,
    "SURFACE_TIMER_START": 0x0033,
    "SURFACE_TIMER_END": 0x0034,
    "SURFACE_HARD_SLIPPERY": 0x0035,
    "SURFACE_HARD_VERY_SLIPPERY": 0x0036,
    "SURFACE_HARD_NOT_SLIPPERY": 0x0037,
    "SURFACE_VERTICAL_WIND": 0x0038,
    "SURFACE_BOSS_FIGHT_CAMERA": 0x0065,
    "SURFACE_CAMERA_FREE_ROAM": 0x0066,
    "SURFACE_THI3_WALLKICK": 0x0068,
    "SURFACE_CAMERA_PLATFORM": 0x0069,
    "SURFACE_CAMERA_MIDDLE": 0x006E,
    "SURFACE_CAMERA_ROTATE_RIGHT": 0x006F,
    "SURFACE_CAMERA_ROTATE_LEFT": 0x0070,
    "SURFACE_CAMERA_BOUNDARY": 0x0072,
    "SURFACE_NOISE_VERY_SLIPPERY_73": 0x0073,
    "SURFACE_NOISE_VERY_SLIPPERY_74": 0x0074,
    "SURFACE_NOISE_VERY_SLIPPERY": 0x0075,
    "SURFACE_NO_CAM_COLLISION": 0x0076,
    "SURFACE_NO_CAM_COLLISION_77": 0x0077,
    "SURFACE_NO_CAM_COL_VERY_SLIPPERY": 0x0078,
    "SURFACE_NO_CAM_COL_SLIPPERY": 0x0079,
    "SURFACE_SWITCH": 0x007A,
    "SURFACE_VANISH_CAP_WALLS": 0x007B,
    "SURFACE_PAINTING_WOBBLE_A6": 0x00A6,
    "SURFACE_PAINTING_WOBBLE_A7": 0x00A7,
    "SURFACE_PAINTING_WOBBLE_A8": 0x00A8,
    "SURFACE_PAINTING_WOBBLE_A9": 0x00A9,
    "SURFACE_PAINTING_WOBBLE_AA": 0x00AA,
    "SURFACE_PAINTING_WOBBLE_AB": 0x00AB,
    "SURFACE_PAINTING_WOBBLE_AC": 0x00AC,
    "SURFACE_PAINTING_WOBBLE_AD": 0x00AD,
    "SURFACE_PAINTING_WOBBLE_AE": 0x00AE,
    "SURFACE_PAINTING_WOBBLE_AF": 0x00AF,
    "SURFACE_PAINTING_WOBBLE_B0": 0x00B0,
    "SURFACE_PAINTING_WOBBLE_B1": 0x00B1,
    "SURFACE_PAINTING_WOBBLE_B2": 0x00B2,
    "SURFACE_PAINTING_WOBBLE_B3": 0x00B3,
    "SURFACE_PAINTING_WOBBLE_B4": 0x00B4,
    "SURFACE_PAINTING_WOBBLE_B5": 0x00B5,
    "SURFACE_PAINTING_WOBBLE_B6": 0x00B6,
    "SURFACE_PAINTING_WOBBLE_B7": 0x00B7,
    "SURFACE_PAINTING_WOBBLE_B8": 0x00B8,
    "SURFACE_PAINTING_WOBBLE_B9": 0x00B9,
    "SURFACE_PAINTING_WOBBLE_BA": 0x00BA,
    "SURFACE_PAINTING_WOBBLE_BB": 0x00BB,
    "SURFACE_PAINTING_WOBBLE_BC": 0x00BC,
    "SURFACE_PAINTING_WOBBLE_BD": 0x00BD,
    "SURFACE_PAINTING_WOBBLE_BE": 0x00BE,
    "SURFACE_PAINTING_WOBBLE_BF": 0x00BF,
    "SURFACE_PAINTING_WOBBLE_C0": 0x00C0,
    "SURFACE_PAINTING_WOBBLE_C1": 0x00C1,
    "SURFACE_PAINTING_WOBBLE_C2": 0x00C2,
    "SURFACE_PAINTING_WOBBLE_C3": 0x00C3,
    "SURFACE_PAINTING_WOBBLE_C4": 0x00C4,
    "SURFACE_PAINTING_WOBBLE_C5": 0x00C5,
    "SURFACE_PAINTING_WOBBLE_C6": 0x00C6,
    "SURFACE_PAINTING_WOBBLE_C7": 0x00C7,
    "SURFACE_PAINTING_WOBBLE_C8": 0x00C8,
    "SURFACE_PAINTING_WOBBLE_C9": 0x00C9,
    "SURFACE_PAINTING_WOBBLE_CA": 0x00CA,
    "SURFACE_PAINTING_WOBBLE_CB": 0x00CB,
    "SURFACE_PAINTING_WOBBLE_CC": 0x00CC,
    "SURFACE_PAINTING_WOBBLE_CD": 0x00CD,
    "SURFACE_PAINTING_WOBBLE_CE": 0x00CE,
    "SURFACE_PAINTING_WOBBLE_CF": 0x00CF,
    "SURFACE_PAINTING_WOBBLE_D0": 0x00D0,
    "SURFACE_PAINTING_WOBBLE_D1": 0x00D1,
    "SURFACE_PAINTING_WOBBLE_D2": 0x00D2,
    "SURFACE_PAINTING_WARP_D3": 0x00D3,
    "SURFACE_PAINTING_WARP_D4": 0x00D4,
    "SURFACE_PAINTING_WARP_D5": 0x00D5,
    "SURFACE_PAINTING_WARP_D6": 0x00D6,
    "SURFACE_PAINTING_WARP_D7": 0x00D7,
    "SURFACE_PAINTING_WARP_D8": 0x00D8,
    "SURFACE_PAINTING_WARP_D9": 0x00D9,
    "SURFACE_PAINTING_WARP_DA": 0x00DA,
    "SURFACE_PAINTING_WARP_DB": 0x00DB,
    "SURFACE_PAINTING_WARP_DC": 0x00DC,
    "SURFACE_PAINTING_WARP_DD": 0x00DD,
    "SURFACE_PAINTING_WARP_DE": 0x00DE,
    "SURFACE_PAINTING_WARP_DF": 0x00DF,
    "SURFACE_PAINTING_WARP_E0": 0x00E0,
    "SURFACE_PAINTING_WARP_E1": 0x00E1,
    "SURFACE_PAINTING_WARP_E2": 0x00E2,
    "SURFACE_PAINTING_WARP_E3": 0x00E3,
    "SURFACE_PAINTING_WARP_E4": 0x00E4,
    "SURFACE_PAINTING_WARP_E5": 0x00E5,
    "SURFACE_PAINTING_WARP_E6": 0x00E6,
    "SURFACE_PAINTING_WARP_E7": 0x00E7,
    "SURFACE_PAINTING_WARP_E8": 0x00E8,
    "SURFACE_PAINTING_WARP_E9": 0x00E9,
    "SURFACE_PAINTING_WARP_EA": 0x00EA,
    "SURFACE_PAINTING_WARP_EB": 0x00EB,
    "SURFACE_PAINTING_WARP_EC": 0x00EC,
    "SURFACE_PAINTING_WARP_ED": 0x00ED,
    "SURFACE_PAINTING_WARP_EE": 0x00EE,
    "SURFACE_PAINTING_WARP_EF": 0x00EF,
    "SURFACE_PAINTING_WARP_F0": 0x00F0,
    "SURFACE_PAINTING_WARP_F1": 0x00F1,
    "SURFACE_PAINTING_WARP_F2": 0x00F2,
    "SURFACE_PAINTING_WARP_F3": 0x00F3,
    "SURFACE_TTC_PAINTING_1": 0x00F4,
    "SURFACE_TTC_PAINTING_2": 0x00F5,
    "SURFACE_TTC_PAINTING_3": 0x00F6,
    "SURFACE_PAINTING_WARP_F7": 0x00F7,
    "SURFACE_PAINTING_WARP_F8": 0x00F8,
    "SURFACE_PAINTING_WARP_F9": 0x00F9,
    "SURFACE_PAINTING_WARP_FA": 0x00FA,
    "SURFACE_PAINTING_WARP_FB": 0x00FB,
    "SURFACE_PAINTING_WARP_FC": 0x00FC,
    "SURFACE_WOBBLING_WARP": 0x00FD,
    "SURFACE_TRAPDOOR": 0x00FF,

    "TERRAIN_GRASS": 0x0000,
    "TERRAIN_STONE": 0x0001,
    "TERRAIN_SNOW": 0x0002,
    "TERRAIN_SAND": 0x0003,
    "TERRAIN_SPOOKY": 0x0004,
    "TERRAIN_WATER": 0x0005,
    "TERRAIN_SLIDE": 0x0006,
    "TERRAIN_MASK": 0x0007,
}