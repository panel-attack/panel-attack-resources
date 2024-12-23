#brew install pillow
import os
import sys
import shutil
from PIL import Image, ImageEnhance
import numpy as numpy
import blend_modes as blend_modes

def rgb_to_hsv(rgb):
    # Translated from source of colorsys.rgb_to_hsv
    # r,g,b should be a numpy arrays with values between 0 and 255
    # rgb_to_hsv returns an array of floats between 0.0 and 1.0.
    rgb = rgb.astype('float')
    hsv = numpy.zeros_like(rgb)
    # in case an RGBA array was passed, just copy the A channel
    hsv[..., 3:] = rgb[..., 3:]
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    maxc = numpy.max(rgb[..., :3], axis=-1)
    minc = numpy.min(rgb[..., :3], axis=-1)
    hsv[..., 2] = maxc
    mask = maxc != minc
    hsv[mask, 1] = (maxc - minc)[mask] / maxc[mask]
    rc = numpy.zeros_like(r)
    gc = numpy.zeros_like(g)
    bc = numpy.zeros_like(b)
    rc[mask] = (maxc - r)[mask] / (maxc - minc)[mask]
    gc[mask] = (maxc - g)[mask] / (maxc - minc)[mask]
    bc[mask] = (maxc - b)[mask] / (maxc - minc)[mask]
    hsv[..., 0] = numpy.select(
        [r == maxc, g == maxc], [bc - gc, 2.0 + rc - bc], default=4.0 + gc - rc)
    hsv[..., 0] = (hsv[..., 0] / 6.0) % 1.0
    return hsv

def hsv_to_rgb(hsv):
    # Translated from source of colorsys.hsv_to_rgb
    # h,s should be a numpy arrays with values between 0.0 and 1.0
    # v should be a numpy array with values between 0.0 and 255.0
    # hsv_to_rgb returns an array of uints between 0 and 255.
    rgb = numpy.empty_like(hsv)
    rgb[..., 3:] = hsv[..., 3:]
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    i = (h * 6.0).astype('uint8')
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    i = i % 6
    conditions = [s == 0.0, i == 1, i == 2, i == 3, i == 4, i == 5]
    rgb[..., 0] = numpy.select(conditions, [v, q, p, p, t, v], default=v)
    rgb[..., 1] = numpy.select(conditions, [v, v, v, q, p, p], default=t)
    rgb[..., 2] = numpy.select(conditions, [v, p, t, v, v, q], default=p)
    return rgb.astype('uint8')


def shiftImageHue(arr,hout):
    hsv=rgb_to_hsv(arr)
    hsv[...,0]=hout
    rgb=hsv_to_rgb(hsv)
    return rgb

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
    self.index = index
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
    self.buildGarbagePopHoveringAnimation()
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

  def standardPanelImage(self):
    panelImage = Image.alpha_composite(self.backgroundImage, self.borderImage)
    panelImage = Image.alpha_composite(panelImage, self.shapeImage)
    return panelImage

  def buildNormalAnimation(self):
    self.startAnimation()
    panelImage = self.standardPanelImage()
    self.addFrame(panelImage)
    self.endAnimation()

  def buildGarbagePopHoveringAnimation(self):
    self.startAnimation()
    panelImage = self.standardPanelImage()
    panelImage = self.backgroundImage.copy()
    panelImage = adjustExtremes(panelImage, 0, 150)
    panelImage = Image.alpha_composite(panelImage, adjustExtremes(self.borderImage, 0, 255))
    panelImage = Image.alpha_composite(panelImage, adjustExtremes(self.shapeImage, 0, 220))
    self.addFrame(panelImage)
    self.endAnimation()

  def splitTypeForIndex(self, index, shouldSplit):
    splitType = 0
    if shouldSplit:
      match index:
        case '1':
            splitType = 1
        case '2':
            splitType = 2
        case '3':
            splitType = 1
        case '4':
            splitType = 1
        case '5':
            splitType = 2
        case '6':
            splitType = 2
        case '7':
            splitType = 1
        case '8':
            splitType = 2
    return splitType
              
  # Builds an animation with the shapes transformed by a set of animations of: xOffset, yOffset, xScale, yScale
  def buildAnimationWithShapeTransforms(self, shapeTransformAnimations, shouldSplit, baseImage, includeBorder=True):
      self.startAnimation()
      for animation in shapeTransformAnimations:
        splitType = self.splitTypeForIndex(self.index, shouldSplit)
        if baseImage == None:
           panelImage = self.backgroundImage.copy()
        else:
           panelImage = baseImage.copy()
        newWidth = int(animation[2] * self.panelSize[0])
        newHeight = int(animation[3] * self.panelSize[1])
        squishedShapeImage = self.shapeImage.resize([newWidth, newHeight])
        if splitType == 0:
          xOffset = int(animation[0] * self.panelSize[0]) - int(squishedShapeImage.size[0] / 2) + int(self.panelSize[0] / 2)
          yOffset = int(animation[1] * self.panelSize[1]) - int(squishedShapeImage.size[1] / 2) + int(self.panelSize[1] / 2)

          panelImage.paste(squishedShapeImage, (xOffset, yOffset), squishedShapeImage)
        elif splitType == 1:
          squishedSize = squishedShapeImage.size
          left = 0
          middle = squishedSize[0] / 2
          right = squishedSize[0]
          top = 0
          bottom = squishedSize[1]
          splitImage = squishedShapeImage.crop((left, top, middle, bottom))
          xOffset = int(animation[0] * self.panelSize[0]) - int(splitImage.size[0]) + int(self.panelSize[0] / 2)
          yOffset = int(animation[1] * self.panelSize[1]) - int(splitImage.size[1] / 2) + int(self.panelSize[1] / 2)
          panelImage.paste(splitImage, (xOffset, yOffset), splitImage)
          splitImage = squishedShapeImage.crop((middle, top, right, bottom))
          xOffset = -int(animation[0] * self.panelSize[0]) + int(self.panelSize[0] / 2)
          yOffset = -int(animation[1] * self.panelSize[1]) - int(splitImage.size[1] / 2) + int(self.panelSize[1] / 2)
          panelImage.paste(splitImage, (xOffset, yOffset), splitImage)
        else:
          squishedSize = squishedShapeImage.size
          left = 0
          right = squishedSize[0]
          top = 0
          middle = squishedSize[1] / 2
          bottom = squishedSize[1]

          splitImage = squishedShapeImage.crop((left, top, right, middle))
          xOffset = int(animation[1] * self.panelSize[0]) - int(splitImage.size[0] / 2) + int(self.panelSize[0] / 2)
          yOffset = int(animation[0] * self.panelSize[1]) - int(splitImage.size[1]) + int(self.panelSize[1] / 2)
          panelImage.paste(splitImage, (xOffset, yOffset), splitImage)
          splitImage = squishedShapeImage.crop((left, middle, right, bottom))
          xOffset = -int(animation[1] * self.panelSize[0]) - int(splitImage.size[0] / 2) + int(self.panelSize[0] / 2)
          yOffset = -int(animation[0] * self.panelSize[1]) + int(self.panelSize[1] / 2)
          panelImage.paste(splitImage, (xOffset, yOffset), splitImage)
        
        if includeBorder:
          panelImage = Image.alpha_composite(panelImage, self.borderImage)
        self.addFrame(panelImage)
      self.endAnimation()

  def buildFallingAnimation(self):
      # xOffset, yOffset, xScale, yScale
      animations = [[0, 0.03, 1.082, 0.92],
                    ]
      self.buildAnimationWithShapeTransforms(animations, 0, None)

  def buildDimmedAnimation(self):
    self.startAnimation()
    panelImage = self.standardPanelImage()
    panelImage = adjustExtremes(panelImage, 0, 150)
    self.addFrame(panelImage)
    self.endAnimation()

  def buildDeadAnimation(self):
    # xOffset, yOffset, xScale, yScale
    animations = [[-0.05, 0, 1.1, 1.1]]
    self.buildAnimationWithShapeTransforms(animations, 1, None)
  
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
      self.buildAnimationWithShapeTransforms(animations, 0, None)

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
      self.buildAnimationWithShapeTransforms(animations, 0, None)
  
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
      multiplier = 1
      multiplierDecrement = 0.18
      animations = []
      for x in range(0, self.panelConfig.popAnimationCount):
        offset = x * -0.1
        animations.append([offset, 0, multiplier, multiplier])
        multiplier -= multiplierDecrement
      baseImage = Image.new('RGBA', self.panelSize, (255, 0, 0, 0))
      self.buildAnimationWithShapeTransforms(animations, 1, baseImage, False)

class Panels:
  def __init__(self, baseFolder):
    self.baseFolder = baseFolder
    self.folder = self.baseFolder + "/RawImages/"
    self.configFileName = "config.json"
    self.landingAnimationCount = 7
    self.popAnimationCount = 6
    self.maxAnimationFrames = 10
    self.animationCount = 10
    self.useDangerBounce = True
    self.dangerBounceReduced = True
    self.makeAlternates = False
    self.previewImage = None

  def createSheets(self, saveDirectory):
    baseFolder = os.path.normpath(self.baseFolder)
    folderName = baseFolder.split(os.sep)[-1]
    outputFolder = saveDirectory + folderName + "/"
    os.makedirs(os.path.dirname(outputFolder), exist_ok=True)

    panelColorCount = 9
    for i in range(1, panelColorCount):
      index = str(i)
      sheet = Sheet(self, index)
      sheet.buildSheet(index)
      # if i == 2:
        # sheet.sheetImage.show()
      if self.previewImage == None: 
        self.previewImage = Image.new('RGBA', (sheet.panelSize[0] * panelColorCount, sheet.panelSize[1] * sheet.panelConfig.animationCount), (255, 0, 0, 0))
      self.previewImage.paste(sheet.sheetImage, ((i-1) * sheet.panelSize[0], 0))
      sheet.sheetImage.save(outputFolder + "panel-" + index + "@2x.png")

      if self.makeAlternates and i < 8:
        alternateColorsFolder = outputFolder + "/Alternate Colors/"
        os.makedirs(os.path.dirname(alternateColorsFolder), exist_ok=True)
        for hue in numpy.arange(0, 1, 0.025):
          coloredSheet = Image.fromarray(shiftImageHue(numpy.array(sheet.sheetImage), hue), 'RGBA')
          coloredSheet.save(alternateColorsFolder + "panel-" + index + "-" + str(int(hue * 100)) + "@2x.png")

    fileSuffix = "@2x.png"
    panel0Name = "panel00"
    shutil.copyfile(self.folder + panel0Name + ".png", outputFolder + panel0Name + fileSuffix)
    shutil.copyfile(self.baseFolder + "/" + self.configFileName, outputFolder + self.configFileName)

    self.previewImage.show()

panelConfig = Panels(sys.argv[1])
panelConfig.createSheets(sys.argv[2])
