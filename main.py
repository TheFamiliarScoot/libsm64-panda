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
        self.mario = SM64Mario(self, self.sm64state, LPoint3f(0, 20, 0))
        print(self.mario)
        self.mario.reparentTo(self.render)
        print(self.mario)

        print(self.mario.node())

        self.a = False
        self.b = False
        self.z = False

        self.xStick = 0
        self.yStick = 0

        aButton = 'space'
        bButton = 'control'
        zButton = 'shift'
        stickLeftButton = 'a'
        stickRightButton = 'd'
        stickUpButton = 'w'
        stickDownButton = 's'

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

        self.taskMgr.add(self.inputs, 'MarioInputs')
    
    def pressA(self): self.a = True
    def pressB(self): self.b = True
    def pressZ(self): self.z = True
    def releaseA(self): self.a = False
    def releaseB(self): self.b = False
    def releaseZ(self): self.z = False
    def pressStickLeft(self): self.xStick -= 1
    def releaseStickLeft(self): self.xStick += 1
    def pressStickRight(self): self.xStick += 1
    def releaseStickRight(self): self.xStick -= 1
    def pressStickUp(self): self.yStick += 1
    def releaseStickUp(self): self.yStick -= 1
    def pressStickDown(self): self.yStick -= 1
    def releaseStickDown(self): self.yStick += 1
    
    def inputs(self, t):
        self.mario.get_input_buttons(self.a, self.b, self.z)
        self.mario.get_input_stick(self.xStick, self.yStick)
#        print("X " + str(self.xStick) + " Y " + str(self.yStick))
        return Task.cont

app = MyApp()
app.run()