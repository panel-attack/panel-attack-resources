#brew install pillow
import os
import sys
import shutil
from PIL import Image, ImageEnhance
import numpy as numpy
import blend_modes as blend_modes

def blendImages(background, foreground, opacity, functionToRun):
  background_img = numpy.array(background)  # Inputs to blend_modes need to be numpy arrays.
  background_img_float = background_img.astype(float)  # Inputs to blend_modes need to be floats.

  foreground_img = numpy.array(foreground)  # Inputs to blend_modes need to be numpy arrays.
  foreground_img_float = foreground_img.astype(float)  # Inputs to blend_modes need to be floats.

  blended_img_float = functionToRun(background_img_float, foreground_img_float, opacity)

  # Convert blended image back into PIL image
  blended_img = numpy.uint8(blended_img_float)  # Image needs to be converted back to uint8 type for PIL handling.
  blended_img_raw = Image.fromarray(blended_img)  # Note that alpha channels are displayed in black by PIL by default.
                                                  # This behavior is difficult to change (although possible).
                                                  # If you have alpha channels in your images, then you should give
                                                  # OpenCV a try.
  return blended_img_raw

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
    if self.panelConfig.useDangerBounce:
      self.buildBounceDangerAnimation()
    else:
      self.buildShineDangerAnimation()
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
    panelImage = adjustExtremes(panelImage, 0, 150)
    self.addFrame(panelImage)
    self.endAnimation()

  def buildDeadAnimation(self):
    self.startAnimation()
    panelImage = self.standardPanelImage()
    panelImage = adjustExtremes(panelImage, 0, 140)
    # panelImage = adjust_levels(panelImage, 0, 255)
    self.addFrame(panelImage)
    self.endAnimation()

  # Builds an animation with the shapes transformed by a set of animations of: xOffset, yOffset, xScale, yScale
  def buildAnimationWithShapeTransforms(self, shapeTransformAnimations):
      self.startAnimation()
      for animation in shapeTransformAnimations:
        newWidth = int(animation[2] * self.panelSize[0])
        newHeight = int(animation[3] * self.panelSize[1])
        xOffset = int(animation[0] * self.panelSize[0]) + int((self.panelSize[0] - newWidth) / 2)
        yOffset = int(animation[1] * self.panelSize[1]) + int((self.panelSize[1] - newHeight) / 2)
        panelImage = Image.alpha_composite(self.backgroundImage, self.borderImage)
        squishedShapeImage = self.shapeImage.resize([newWidth, newHeight])
        panelImage.paste(squishedShapeImage, (xOffset, yOffset), squishedShapeImage)
        self.addFrame(panelImage)
      self.endAnimation()

  def buildLandingAnimation(self):
      # xOffset, yOffset, xScale, yScale
      animations = [[0, 0.075, 1.075, 0.85],
                    [0, 0.09, 1.1, 0.8],
                    [0, 0.075, 1.075, 0.85],
                    [0, 0.06, 1.05, 0.9],
                    [0, 0.03, 1.025, 0.95],
                    [0, 0.015, 1.0125, 0.975],
                    [0, 0, 1, 1]
                    ]
      self.buildAnimationWithShapeTransforms(animations)

  def buildShineDangerAnimation(self):
      self.startAnimation()
      # amount = self.panelSize[0] / 2
      # for x in numpy.arange(amount, -amount, -2 * amount / 10):
      #   xOffset = int(x)
      #   yOffset = int(-x)
      #   panelImage = self.backgroundImage.copy()

      #   shineOffsetImage = Image.new('RGBA', self.panelSize, (255, 0, 0, 0))
      #   shineImage = Image.open(self.panelConfig.folder + "shine.png", mode = 'r')
      #   shineOffsetImage.paste(shineImage, (xOffset, yOffset), shineImage)
        
      #   panelImage = blendImages(panelImage, shineOffsetImage, .75, blend_modes.overlay)
      #   self.addFrame(panelImage)

      alphas = []
      min = 150
      max = 255
      step = int((max - min) / 5)
      for a in numpy.arange(min, max, step):
        alphas.append(a)
      for a in numpy.arange(max, min, -step):
        alphas.append(a)

      for alpha in alphas:
        panelImage = self.backgroundImage.copy()

        shineOffsetImage = Image.new('RGBA', self.panelSize, (255, 255, 255, alpha))
        blendedShineImage = blendImages(self.borderImage, shineOffsetImage, 0.5, blend_modes.overlay)

        panelImage = Image.alpha_composite(panelImage, blendedShineImage)
        panelImage = Image.alpha_composite(panelImage, self.shapeImage)

        self.addFrame(panelImage)
      self.endAnimation()

  def buildBounceDangerAnimation(self):
      # xOffset, yOffset, xScale, yScale
      animations = [[0, 0, 1, 1],
                    [0, -0.02, 1, 1],
                    [0, -0.04, 1, 1],
                    [0, -0.06, 1, 1],
                    [0, -0.04, 1, 1],
                    [0, -0.02, 1, 1],
                    [0, 0, 1, 1],
                    [0, 0.06, 1.05, 0.9],
                    [0, 0.09, 1.1, 0.8],
                    [0, 0.06, 1.05, 0.9],
                    ]
      if self.panelConfig.dangerBounceReduced:
        animations = map(lambda animation: [animation[0]/2, animation[1]/2, ((animation[2]-1)/2)+1, ((animation[3]-1)/2)+1], animations)
      self.buildAnimationWithShapeTransforms(animations)
  
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
  def __init__(self, baseFolder):
    self.baseFolder = baseFolder
    self.folder = self.baseFolder + "/RawImages/"
    self.outputFolder = self.baseFolder + "/OutputPanels/"
    self.configFileName = "config.json"
    self.landingAnimationCount = 7
    self.popAnimationCount = 6
    self.maxAnimationFrames = 10
    self.animationCount = 10
    self.useDangerBounce = True
    self.dangerBounceReduced = True
    self.previewImage = None

  def createSheets(self):
    os.makedirs(os.path.dirname(self.outputFolder), exist_ok=True)

    panelColorCount = 9
    for i in range(1, panelColorCount):
      index = str(i)
      sheet = Sheet(self, index)
      sheet.buildSheet(index)
      if i == 2:
        sheet.sheetImage.show()
      if self.previewImage == None: 
        self.previewImage = Image.new('RGBA', (sheet.panelSize[0] * panelColorCount, sheet.panelSize[1] * sheet.panelConfig.animationCount), (255, 0, 0, 0))
      self.previewImage.paste(sheet.sheetImage, ((i-1) * sheet.panelSize[0], 0))

    shutil.copyfile(self.baseFolder + "/" + self.configFileName, self.outputFolder + self.configFileName)

    self.previewImage.show()

panelConfig = PanelsConfig(sys.argv[1])
panelConfig.createSheets()
