import subprocess
import time
import os
import shutil
import numpy as np
import matplotlib.pyplot as plt
import skimage
from PIL import Image

SAVEGAMELOC = "/home/ctralie/.vba/POKEMONRED981.sgm"
PYTHON3 = True
RECORD_TIME = 1
FRAMESPERSEC = 15
Y_OFFSET = -45
HEIGHT_CORRECTION = 50

class Key(object):
    def __init__(self, key, actualkey, prob, image):
        self.key = key
        self.actualkey = actualkey
        self.prob = prob
        self.image = image

KEYS = {}
KEYS["left"] = Key("Left", "left", 0.186,  "PressingLeft.png")
KEYS["right"] = Key("Right", "right", 0.186, "PressingRight.png")
KEYS["up"] = Key("Up", "up", 0.186, "PressingUp.png")
KEYS["down"] = Key("Down", "down", 0.186, "PressingDown.png")
KEYS["a"] = Key("Z", "a", 0.202, "PressingA.png")
KEYS["b"] = Key("X", "b", 0.05, "PressingB.png")
KEYS["start"] = Key("Return", "Start", 0.002, "PressingStart.png")
KEYS["select"] = Key("BackSpace", "Select", 0.002, "PressingSelect.png")

def getRandomKey():
    num = np.random.rand()
    keys = [KEYS[k] for k in KEYS]
    idx = 0
    cumsum = keys[idx].prob
    while cumsum < num and idx < len(KEYS) - 1:
        idx += 1
        cumsum += keys[idx].prob
    return keys[idx].actualkey

def launchGame():
    #subprocess.Popen(["vba", "-4", "POKEMONRED98.GB"])
    FNULL = open(os.devnull, 'w')
    subprocess.Popen(["vba", "POKEMONRED98.GB"], stdout = FNULL, stderr = FNULL)

#Get the window ID of the process
def getWindowID():    
    proc = subprocess.Popen(["xdotool", "search", "--name", "VisualBoy"], stdout=subprocess.PIPE)
    ID = 0
    while True:
        output=proc.stdout.readline()
        if (output == b'' or output == '') and proc.poll() is not None:
            break
        if output:
            ID = int(output.strip())
        rc = proc.poll()
    return ID

def getWindowGeometry(ID):
    proc = subprocess.Popen(["xdotool", "getwindowgeometry", "%i"%ID], stdout=subprocess.PIPE)
    res = []
    while True:
        output=proc.stdout.readline()
        if (output == b'' or output == '') and proc.poll() is not None:
            break
        if output:
            res.append(output.strip())
        rc = proc.poll()
    pos = res[1].split()[1]
    geom = res[2].split()[1]
    return (pos, geom)

#Move to the window and click on it to gain focus
def gainFocus(ID):    
    subprocess.call(["xdotool", "mousemove", "--window", "%i"%ID, "200", "200", "click", "1"])

def saveGame(filename, ID):
    if os.path.exists(SAVEGAMELOC):
        os.remove(SAVEGAMELOC)
    subprocess.call(["xdotool", "keydown", "--window", "%i"%ID, "shift"])
    subprocess.call(["xdotool", "key", "--window", "%i"%ID, "F1"])
    subprocess.call(["xdotool", "keyup", "--window", "%i"%ID, "shift"])
    if not os.path.exists(SAVEGAMELOC):
        print("ERROR TYPE 1 saving game.  Retrying...")
        time.sleep(1)
        saveGame(filename, ID)
    elif os.stat(SAVEGAMELOC).st_size == 0:
        print("ERROR TYPE 2 saving game.  Retrying...")
        time.sleep(1)
        saveGame(filename, ID)
    else:
        shutil.copyfile(SAVEGAMELOC, filename)

def loadGame(filename, ID):
    if os.path.exists(SAVEGAMELOC):
        os.remove(SAVEGAMELOC)
    shutil.copyfile(filename, SAVEGAMELOC)
    subprocess.call(["xdotool", "key", "--window", "%i"%ID, "F1"])

def closeGame(ID):
    subprocess.call(["xdotool", "keydown", "--window", "%i"%ID, "alt"])
    subprocess.call(["xdotool", "key", "--window", "%i"%ID, "F4"])
    subprocess.call(["xdotool", "keyup", "--window", "%i"%ID, "alt"])

#Record window with ID to a file
def startRecording(ID, filename, time = 10):
    (pos, geom) = getWindowGeometry(ID)
    if PYTHON3:
        geom = str(geom)[2:-1]
        pos = str(pos)[2:-1]
    width, height = geom.split("x")
    height = "%i"%(int(height)+HEIGHT_CORRECTION)
    x, y = pos.split(",")
    y = int(y)
    y = "%i"%(y + Y_OFFSET)
    
    command = ["byzanz-record", "-d", "%i"%time, "-x", x, "-y", y, "-w", width, "-h", height, filename]
    FNULL = open(os.devnull, 'w')
    proc = subprocess.Popen(command, stdout = FNULL, stderr = FNULL)
    return proc

def stopRecording(proc):
    proc.terminate()

def hitKey(ID, key, delay = 400):
    #A delay (ms) is needed to make sure key taps register in the game
    command = ["xdotool", "key", "--window", "%i"%ID, "--delay", "%i"%delay, key]
    subprocess.call(command)

def holdKey(ID, key):
    #A delay (ms) is needed to make sure key taps register in the game
    command = ["xdotool", "keydown", "--window", "%i"%ID, key]
    subprocess.call(command)

def releaseKey(ID, key):
    #A delay (ms) is needed to make sure key taps register in the game
    command = ["xdotool", "keyup", "--window", "%i"%ID, key]
    subprocess.call(command)

#Return (image, [sx, ex, sy, ey] range for other frames)
def makeFrameTemplate(filename, keyObj, text, wordRange, pad = 10):
    #Load in and resize frame    
    frame = skimage.io.imread(filename)
    W = 640
    frac = float(W)/frame.shape[1]
    frame = skimage.transform.rescale(frame, frac, multichannel=False)
    
    #Load in and resize controls
    controls = skimage.io.imread("ControllerImages/%s"%keyObj.image)
    H = frame.shape[0]
    frac = float(H)/controls.shape[0]
    controls = skimage.transform.rescale(controls, frac, multichannel=False)
    
    #Figure out the width
    W = int(np.ceil(frame.shape[1] + controls.shape[1]))
    
    #Render text
    fin = open("textTemplate.html")
    l = fin.readlines()
    s = "".join(l)
    fin.close()
    s = s.replace("WIDTHGOESHERE", "%i"%W)
    textHTML = text
    print("textHTML", textHTML)
    print("wordRange", wordRange)
    before = textHTML[0:wordRange[0]]
    during = textHTML[wordRange[0]:wordRange[1]]
    after = textHTML[wordRange[1]:]
    s = s.replace("TEXTGOESHERE", "%s<font color = \"red\">%s</font>%s"%(before, during, after))
    fout = open("temp.html", "w")
    fout.write(s)
    fout.close()
    
    FNULL = open(os.devnull, 'w')
    subprocess.call(["wkhtmltopdf", "temp.html", "temp.pdf"], stdout = FNULL, stderr = FNULL)
    subprocess.call(["convert", "-density", "150", "temp.pdf", "-quality", "90", "temp.png"], stdout = FNULL, stderr = FNULL)
    subprocess.call(["convert", "temp.png", "-trim", "+repage", "temp.png"], stdout = FNULL, stderr = FNULL)
    #There's a small border around all sides that causes autocrop to fail the first
    #time
    text = skimage.io.imread("temp.png")
    text = text[2:-2, 2:-2, :]
    im = Image.fromarray(text)
    im.save("temp.png")
    subprocess.call(["convert", "temp.png", "-trim", "+repage", "temp.png"], stdout = FNULL, stderr = FNULL)
    
    #Load in text
    textImg = skimage.io.imread("temp.png")
    frac = float(W)/textImg.shape[1]
    textImg = skimage.transform.rescale(textImg, frac, multichannel=False)
    
    #Finally, set up image, and report range where gameboy frame resides
    H = textImg.shape[0] + controls.shape[0]
    I = 255*np.ones((H + 10*pad, W + 2*pad, 3), dtype=frame.dtype)
    I[pad:pad+frame.shape[0], pad:pad+frame.shape[1], :] = frame[:, :, 0:3]*255
    I[pad:pad+controls.shape[0], pad+frame.shape[1]:pad+frame.shape[1]+controls.shape[1], :] = controls[:, :, 0:3]*255
    I[pad*3+frame.shape[0]:pad*3+frame.shape[0]+textImg.shape[0], pad:pad+textImg.shape[1], :] = textImg[:, :, 0:3]*255
    
    r = [pad, pad+frame.shape[0], pad, pad+frame.shape[1]]
    I = np.array(I, dtype=np.uint8)
    return (I, r)


def hitKeyAndRecord(ID, keyObj, filename):
    """
    Hits a key, records the video
    """
    if os.path.exists(filename):
        os.remove(filename)
    
    #Step 1: Load the saved game state and record the action
    recProc = startRecording(ID, filename, RECORD_TIME)
    hitKey(ID, keyObj.key, 400)

def randomWalk(nframes):
    import time
    launchGame()
    time.sleep(1)
    ID = getWindowID()
    time.sleep(1)
    loadGame("BEGINNING.sgm", ID)
    holdKey(ID, 'space')
    #time.sleep(3)
    keysList = list(KEYS.keys())
    delay = 1000/30
    time = int(np.ceil(delay*nframes*1.1/1000))
    recProc = startRecording(ID, "test.gif", time)
    for i in range(nframes):
        key = KEYS[keysList[np.random.randint(len(KEYS))]]
        hitKey(ID, key.key, delay)
    releaseKey(ID, 'space')
    #saveGame("startScreen.sgm", ID)

def testLeft():
    launchGame()
    time.sleep(1)
    ID = getWindowID()
    time.sleep(1)
    loadGame("BEGINNING.sgm", ID)
    hitKeyAndRecord(ID, KEYS["left"], "Left.gif")

#randomWalk(100)

