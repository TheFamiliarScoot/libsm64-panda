# SPDX-License-Identifier: LicenseRef-NONE
# TODO(patchmixolydic): ask the libsm64-blender maintainers to add a license.
#     This file would then have to be provided under that license.

# Some classes and constants from libsm64-blender
import ctypes as ct
import os

SM64_TEXTURE_WIDTH = 64 * 11
SM64_TEXTURE_HEIGHT = 64
SM64_GEO_MAX_TRIANGLES = 1024
SM64_SCALE_FACTOR = 50

def make_image(img, buffer):
    i = 0
    for y in range(SM64_TEXTURE_HEIGHT):
        for x in range(SM64_TEXTURE_WIDTH):
            r = float(buffer[i]) / 255
            g = float(buffer[i+1]) / 255
            b = float(buffer[i+2]) / 255
            a = float(buffer[i+3]) / 255
            i += 4
            img.setXelA(x, y, r, g, b, a)

def init_sm64(ref,  dll_dir, rom_dir):
    ref.sm64 = ct.cdll.LoadLibrary(dll_dir)

    ref.sm64.sm64_global_init.argtypes = [ ct.c_char_p, ct.POINTER(ct.c_ubyte), ct.c_char_p ]
    ref.sm64.sm64_static_surfaces_load.argtypes = [ ct.POINTER(SM64Surface), ct.c_uint32 ]
    ref.sm64.sm64_mario_create.argtypes = [ ct.c_int16, ct.c_int16, ct.c_int16 ]
    ref.sm64.sm64_mario_create.restype = ct.c_int32
    ref.sm64.sm64_mario_tick.argtypes = [ ct.c_uint32, ct.POINTER(SM64MarioInputs), ct.POINTER(SM64MarioState), ct.POINTER(SM64MarioGeometryBuffers) ]

    with open(os.path.expanduser(rom_dir), 'rb') as file:
        rom_bytes = bytearray(file.read())
        rom_chars = ct.c_char * len(rom_bytes)
        texture_buff = (ct.c_ubyte * (4 * SM64_TEXTURE_WIDTH * SM64_TEXTURE_HEIGHT))()
        ref.sm64.sm64_global_init(rom_chars.from_buffer(rom_bytes), texture_buff, None)

    return texture_buff

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

