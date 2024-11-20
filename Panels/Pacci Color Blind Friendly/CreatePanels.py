#brew install pillow
import shutil
from PIL import Image, ImageEnhance


def doubleBrightness(image, multiplier, exponent):

    r, g, b, a = image.split()
    r = r.point(lambda pixel: max(0, min(255, int((pixel * multiplier) ** exponent)))) 
    g = g.point(lambda pixel: max(0, min(255, int((pixel * multiplier) ** exponent)))) 
    b = b.point(lambda pixel: max(0, min(255, int((pixel * multiplier) ** exponent)))) 
    return Image.merge("RGBA", (r, g, b, a))

def adjustExtremes(image, minValue=0, maxValue=255):

    r, g, b, a = image.split()
    r = r.point(lambda pixel: max(minValue, min(maxValue, minValue + int(pixel / 255 * (maxValue - minValue))))) 
    g = g.point(lambda pixel: max(minValue, min(maxValue, minValue + int(pixel / 255 * (maxValue - minValue))))) 
    b = b.point(lambda pixel: max(minValue, min(maxValue, minValue + int(pixel / 255 * (maxValue - minValue))))) 
    return Image.merge("RGBA", (r, g, b, a))

def adjust_levels(image, black_point=0, white_point=255):
    """Adjusts levels of an image.

    Args:
        image: The PIL Image object.
        black_point: The new black point (0-255).
        white_point: The new white point (0-255).
    """

    r, g, b, a = image.split()
    r = r.point(lambda pixel: max(0, min(255, int((pixel - black_point) * 255 / (white_point - black_point)))) ) 
    g = g.point(lambda pixel: max(0, min(255, int((pixel - black_point) * 255 / (white_point - black_point)))) ) 
    b = b.point(lambda pixel: max(0, min(255, int((pixel - black_point) * 255 / (white_point - black_point)))) ) 
    return Image.merge("RGBA", (r, g, b, a))

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
    # print(self.x)

  def endAnimation(self):
    return
  
  def buildSheet(self, index):

    self.buildNormalAnimation()
    self.buildHoveringAnimation()
    self.buildFallingAnimation()
    self.buildDimmedAnimation()
    self.buildDeadAnimation()
    self.buildLandingAnimation()
    self.buildDangerAnimation()
    self.buildFlashAnimation()
    self.buildFaceAnimation()
    self.buildPopAnimation()
    self.sheetImage.save(self.panelConfig.outputFolder + "panel-" + index + "@2x.png"),(0,0)

  def standardPanelImage(self):
    panelImage = Image.alpha_composite(self.backgroundImage, self.borderImage)
    panelImage = Image.alpha_composite(panelImage, self.shapeImage)
    return panelImage

  def buildNormalAnimation(self):
    self.startAnimation()
    panelImage = self.standardPanelImage()
    self.addFrame(panelImage)
    self.endAnimation()

  def buildHoveringAnimation(self):
    self.startAnimation()
    panelImage = self.standardPanelImage()
    self.addFrame(panelImage)
    self.endAnimation()

  def buildFallingAnimation(self):
    self.startAnimation()
    panelImage = self.standardPanelImage()
    self.addFrame(panelImage)
    self.endAnimation()

  def buildDimmedAnimation(self):
    self.startAnimation()
    panelImage = self.standardPanelImage()
    panelImage = adjustExtremes(panelImage, 0, 180)
    self.addFrame(panelImage)
    self.endAnimation()

  def buildDeadAnimation(self):
    self.startAnimation()
    panelImage = self.standardPanelImage()
    panelImage = adjustExtremes(panelImage, 0, 150)
    # panelImage = adjust_levels(panelImage, 0, 255)
    self.addFrame(panelImage)
    self.endAnimation()

  def buildLandingAnimation(self):
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

  def buildDangerAnimation(self):
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
  
  def buildFlashAnimation(self):
      self.startAnimation()
      panelImage = self.standardPanelImage()
      self.addFrame(panelImage)
      panelImage = Image.alpha_composite(self.backgroundImage, self.borderImage)
      # panelImage = doubleBrightness(panelImage, 40, 1)
      panelImage = adjustExtremes(panelImage, 60, 255)
      panelImage = adjust_levels(panelImage, 0, 120)
      panelImage.paste(self.shapeImage, (0, 0), self.shapeImage)
      self.addFrame(panelImage)
      self.endAnimation()

  def buildFaceAnimation(self):
      self.startAnimation()
      maskedPanelImage = self.shapeImage.copy()
      for yPixel in range(self.panelSize[1]):
        for xPixel in range(self.panelSize[0]):
            r, g, b, a = maskedPanelImage.getpixel((xPixel, yPixel))
            maskedPanelImage.putpixel((xPixel, yPixel), (r, g, b, int(a * 0.6)))  # Reduce alpha by 50%
      panelImage = Image.alpha_composite(self.backgroundImage, self.borderImage)
      panelImage.paste(maskedPanelImage, (0, 0), maskedPanelImage)
      self.addFrame(panelImage)
      self.endAnimation()

  def buildPopAnimation(self):
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


class PanelsConfig:
  def __init__(self):
    self.folder = "RawImages/"
    self.outputFolder = "OutputPanels/"
    self.landingAnimationCount = 10
    self.dangerAnimationCount = 10
    self.popAnimationCount = 6
    self.maxAnimationFrames = self.dangerAnimationCount
    self.animationCount = 10
  def createSheets(self):
    for i in range(1, 9):
      index = str(i)
      sheet = Sheet(self, index)
      sheet.buildSheet(index)
      if i == 1:
        sheet.sheetImage.show()
    configFileName = "config.json"
    shutil.copyfile(configFileName, self.outputFolder + configFileName)

panelConfig = PanelsConfig()
panelConfig.createSheets()
