#brew install pillow
import shutil
from PIL import Image, ImageEnhance



class Sheet:
  def __init__(self, panelConfig, index):
    self.panelConfig = panelConfig
    self.sheetImage = None
    self.x = 0
    self.y = -1
    self.backgroundImage = Image.open(self.panelConfig.folder + index + "background.png", mode = 'r')
    self.borderImage = Image.open(self.panelConfig.folder + index + "border.png", mode = 'r')
    self.shapeImage = Image.open(self.panelConfig.folder + index + "shape.png", mode = 'r')
    self.panelSize = self.backgroundImage.size
    self.sheetImage = Image.new('RGBA', (self.panelSize[0] * self.panelConfig.maxAnimationFrames, self.panelSize[1] * self.panelConfig.animationCount), (255, 0, 0, 0))

  def startAnimation(self):
    self.x = 0 
    self.y += 1
    assert(self.y < self.panelConfig.animationCount)

  def addFrame(self, image):
    assert(self.x < self.panelConfig.maxAnimationFrames)
    self.sheetImage.paste(image, (self.x * self.panelSize[0], self.y * self.panelSize[0]))
    self.x += 1
    print(self.x)

  def endAnimation(self):
    return

  def normalPanel(self):
    self.startAnimation()
    panelImage = Image.alpha_composite(self.backgroundImage, self.borderImage)
    panelImage = Image.alpha_composite(panelImage, self.shapeImage)
    self.addFrame(panelImage)
    self.endAnimation()

  def buildSheet(self, index):

    self.normalPanel()

    # Landing Panels
    self.startAnimation()
    yOffset = 0
    for x in range(0, self.panelConfig.landingAnimationCount):
      panelImage = Image.alpha_composite(self.backgroundImage, self.borderImage)
      panelImage.paste(self.shapeImage, (0, yOffset), self.shapeImage)
      self.addFrame(panelImage)
      if x >= (self.panelConfig.landingAnimationCount-1) / 2:
        yOffset -= 1
      else:
        yOffset += 1
    self.endAnimation()

    # Danger Panels
    self.startAnimation()
    yOffset = 0
    for x in range(0, self.panelConfig.dangerAnimationCount):
      # print(yOffset)
      panelImage = Image.alpha_composite(self.backgroundImage, self.borderImage)
      panelImage.paste(self.shapeImage, (0, yOffset), self.shapeImage)
      self.addFrame(panelImage)
      if x >= (self.panelConfig.dangerAnimationCount-1) / 2:
        yOffset += 1
      else:
        yOffset -= 1
    self.endAnimation()

    # flash animation
    self.startAnimation()
    panelImage = Image.alpha_composite(self.backgroundImage, self.borderImage)
    panelImage = Image.alpha_composite(panelImage, self.shapeImage)
    self.addFrame(panelImage)
    panelImage = self.backgroundImage.copy()
    enhancer = ImageEnhance.Contrast(panelImage)
    panelImage = enhancer.enhance(200)
    enhancer = ImageEnhance.Brightness(panelImage)
    panelImage = enhancer.enhance(200)

    brightBorderImage = self.borderImage.copy()
    enhancer = ImageEnhance.Brightness(brightBorderImage)
    brightBorderImage = enhancer.enhance(4)
    panelImage.paste(brightBorderImage, (0, 0), brightBorderImage)

    darkShapeImage = self.shapeImage.copy()
    enhancer = ImageEnhance.Brightness(darkShapeImage)
    darkShapeImage = enhancer.enhance(0.75)
    panelImage.paste(darkShapeImage, (0, 0), darkShapeImage)
    self.addFrame(panelImage)

    self.endAnimation()
    # print(y)

    # "face" animation
    self.startAnimation()
    maskedPanelImage = self.shapeImage.copy()
    for yPixel in range(self.panelSize[1]):
      for xPixel in range(self.panelSize[0]):
          r, g, b, a = maskedPanelImage.getpixel((xPixel, yPixel))
          maskedPanelImage.putpixel((xPixel, yPixel), (r, g, b, int(a * 0.6)))  # Reduce alpha by 50%
    panelImage = Image.alpha_composite(self.backgroundImage, self.borderImage)
    panelImage.paste(maskedPanelImage, (0, 0), maskedPanelImage)
    self.addFrame(panelImage)
    # print(y)
    self.endAnimation()

    # pop animation
    self.startAnimation()
    yOffset = 0
    multiplier = 1
    multiplierIncrement = 0.2
    multiplierDecrement = 0.3
    for x in range(0, self.panelConfig.popAnimationCount):
      if x >= 2:
        multiplier -= multiplierDecrement
      else:
        multiplier += multiplierIncrement
      panelImage = Image.new('RGBA', self.panelSize, (255, 0, 0, 0))
      newSize = int(self.panelSize[0]*multiplier)
      resizedShapeImage = self.shapeImage.resize((newSize, newSize))
      resizedShapeImageSize = resizedShapeImage.size
      offset = -1 * int((resizedShapeImageSize[0]-self.panelSize[0])/2)
      panelImage.paste(resizedShapeImage, (offset, offset), resizedShapeImage)
      self.addFrame(panelImage)
    self.endAnimation()

    self.sheetImage.save(self.panelConfig.outputFolder + "panel-" + index + "@2x.png"),(0,0)

class PanelsConfig:
  def __init__(self):
    self.folder = "RawImages/"
    self.outputFolder = "OutputPanels/"
    self.landingAnimationCount = 10
    self.dangerAnimationCount = 10
    self.popAnimationCount = 6
    self.maxAnimationFrames = self.dangerAnimationCount
    self.animationCount = 6
  def createSheets(self):
    for i in range(1, 9):
      index = str(i)
      sheet = Sheet(self, index)
      sheet.buildSheet(index)
      sheet.sheetImage.show()
      break
    configFileName = "config.json"
    shutil.copyfile(configFileName, self.outputFolder + configFileName)

panelConfig = PanelsConfig()
panelConfig.createSheets()
