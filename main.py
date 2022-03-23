import math
from direct.showbase.ShowBase import ShowBase
from sm64 import *
from panda3d.core import *

class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Load the environment model.

        self.scene = self.loader.loadModel("models/environment")
        print(type(self.scene))

        # Reparent the model to render.

        self.scene.reparentTo(self.render)

        # Apply scale and position transforms on the model.

        self.scene.setScale(0.25, 0.25, 0.25)

        self.scene.setPos(-8, 42, 0)

        # Set up the SM64 state
        self.sm64state = SM64State("sm64.dll", "sm64.z64")

        # Make the collisions
        self.sm64state.make_flat_plane_surface_array(20000)

        # Create the Mario node
        self.mario = SM64Mario(self, self.sm64state, LPoint3f(0, 400, 0))
        print(self.mario)
        self.mario.reparentTo(self.render)
        print(self.mario)

        self.a = False
        self.b = False
        self.z = False

        self.xStick = 0
        self.yStick = 0

        self.xCam = 0
        self.xCamLeftDown = False
        self.xCamRightDown = False

        aButton = 'z'
        bButton = 'x'
        zButton = 'c'
        stickLeftButton = 'arrow_left'
        stickRightButton = 'arrow_right'
        stickUpButton = 'arrow_up'
        stickDownButton = 'arrow_down'

        camLeftButton = 'a'
        camRightButton = 'd'

        self.accept(aButton, self.pressA)
        self.accept(bButton, self.pressB)
        self.accept(zButton, self.pressZ)
        self.accept(aButton + '-up', self.releaseA)
        self.accept(bButton + '-up', self.releaseB)
        self.accept(zButton + '-up', self.releaseZ)

        self.accept(stickLeftButton, self.pressStickLeft)
        self.accept(stickLeftButton + '-up', self.releaseStickLeft)
        self.accept(stickRightButton, self.pressStickRight)
        self.accept(stickRightButton + '-up', self.releaseStickRight)
        self.accept(stickUpButton, self.pressStickUp)
        self.accept(stickUpButton + '-up', self.releaseStickUp)
        self.accept(stickDownButton, self.pressStickDown)
        self.accept(stickDownButton + '-up', self.releaseStickDown)

        self.accept(camLeftButton, self.pressCamLeft)
        self.accept(camLeftButton + '-up', self.releaseCamLeft)
        self.accept(camRightButton, self.pressCamRight)
        self.accept(camRightButton + '-up', self.releaseCamRight)

        self.taskMgr.add(self.handleMario, 'MarioInputs')
    
    def pressA(self): self.a = True
    def pressB(self): self.b = True
    def pressZ(self): self.z = True
    def releaseA(self): self.a = False
    def releaseB(self): self.b = False
    def releaseZ(self): self.z = False
    def pressStickLeft(self): self.xStick += 1
    def releaseStickLeft(self): self.xStick -= 1
    def pressStickRight(self): self.xStick -= 1
    def releaseStickRight(self): self.xStick += 1
    def pressStickUp(self): self.yStick += 1
    def releaseStickUp(self): self.yStick -= 1
    def pressStickDown(self): self.yStick -= 1
    def releaseStickDown(self): self.yStick += 1
    def pressCamLeft(self): self.xCamLeftDown = True
    def releaseCamLeft(self): self.xCamLeftDown = False
    def pressCamRight(self): self.xCamRightDown = True
    def releaseCamRight(self): self.xCamRightDown = False
    
    def handleMario(self, t):
        self.mario.get_input_buttons(self.a, self.b, self.z)
        self.mario.get_input_stick(self.xStick, self.yStick)

#        if self.xCamLeftDown: self.xCam += 0.1
#        if self.xCamRightDown: self.xCam -= 0.1

#        self.mario.get_input_camera(self.xCam, 0)

        self.camera.setPos(self.mario.getX(), self.mario.getY() - 15, self.mario.getZ() + 2)
#        self.camera.setHpr(-self.xCam * (180 / math.pi),0,0)
#        print("X " + str(self.xStick) + " Y " + str(self.yStick))
        return Task.cont

app = MyApp()
app.run()