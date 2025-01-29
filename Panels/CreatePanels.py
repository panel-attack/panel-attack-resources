#pip3 install pillow
#pip3 install blend_modes
import os
import sys
import shutil
import colorsys
from PIL import Image, ImageEnhance
import numpy as numpy
import blend_modes as blend_modes

def rgb_to_hsl(rgb):
    """Convert RGB to HSL.

    Args:
        rgb (numpy.ndarray): Array of RGB values, shape (N, 3), where R, G, B are in [0, 255].

    Returns:
        numpy.ndarray: Array of HSL values, shape (N, 3),
                       where H is in [0, 360], S and L are in [0, 1].
    """
    rgb = rgb.astype(float) / 255.0  # Normalize RGB to [0, 1]
    hsl = numpy.array([colorsys.rgb_to_hls(r, g, b) for r, g, b in rgb])  # Convert to HSL
    h, l, s = numpy.transpose(hsl)
    h = h * 360  # Scale hue to [0, 360]
    return numpy.column_stack((h, s, l))

def hsl_to_rgb(hsl):
    """Convert HSL to RGB.

    Args:
        hsl (numpy.ndarray): Array of HSL values, shape (N, 3),
                             where H is in [0, 360], S and L are in [0, 1].

    Returns:
        numpy.ndarray: Array of RGB values, shape (N, 3), where R, G, B are in [0, 255].
    """
    hsl[:, 0] = hsl[:, 0] / 360.0  # Scale hue to [0, 1]
    rgb = numpy.array([colorsys.hls_to_rgb(h, l, s) for h, s, l in hsl])  # Convert to RGB
    return (rgb * 255).astype(numpy.uint8)  # Scale RGB back to [0, 255]

def modify_hue_and_lightness(rgb, hue, saturation, lightness_factor):
    """Modify the hue and lightness of an RGB array.

    Args:
        rgb (numpy.ndarray): Input RGB array, shape (N, 3).
        hue
        lightness_factor (float): Multiplicative factor to adjust lightness.

    Returns:
        numpy.ndarray: Modified RGB array, shape (N, 3).
    """
    hsl = rgb_to_hsl(rgb)  # Convert to HSL
    h, s, l = numpy.transpose(hsl)
    h.fill(hue % 360)
    l = numpy.clip(l * lightness_factor, 0, 1)  # Adjust lightness and clip to [0, 1]
    s.fill(saturation)
    hsl_modified = numpy.column_stack((h, s, l))
    return hsl_to_rgb(hsl_modified)  # Convert back to RGB

def shiftImageHueNumpy(rgba_input, hue, saturation, lightnessFactor):
  rgbaShaped = rgba_input.reshape((-1,4))
  r, g, b, alpha = numpy.transpose(rgbaShaped)
  rgb = numpy.column_stack((r, g, b))
  hue360 = hue * 360
  rgb_outputShaped = modify_hue_and_lightness(rgb, hue360, saturation, lightnessFactor)
  r2, g2, b2 = numpy.transpose(rgb_outputShaped)
  rgbaChanged = numpy.column_stack((r2, g2, b2, alpha))
  rgba_output = rgbaChanged.reshape((rgba_input.shape[0], rgba_input.shape[1], 4))
  return rgba_output

def shiftImageHue(image, hue, saturation, lightnessFactor):
  resultImage = Image.fromarray(shiftImageHueNumpy(numpy.array(image), hue, saturation, lightnessFactor), 'RGBA')
  return resultImage

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
  def __init__(self, panelConfig, index, hue, saturation, lightnessFactor):
    self.panelConfig = panelConfig
    self.x = 0
    self.y = -1
    self.index = index
    self.hue = hue
    self.saturation = saturation
    self.lightnessFactor = lightnessFactor
    self.buildPanelBaseImages()
    self.panelSize = self.backgroundImage.size
    self.sheetImage = Image.new('RGBA', (self.panelSize[0] * self.panelConfig.maxAnimationFrames, self.panelSize[1] * self.panelConfig.animationCount), (255, 255, 255, 0))

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
      self.buildPulseDangerAnimation()
      # self.buildShineDangerAnimation()
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
    panelImage = Image.alpha_composite(panelImage, adjustExtremes(self.borderImage, 0, 210))
    panelImage = Image.alpha_composite(panelImage, adjustExtremes(self.shapeImage, 0, 210))
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
  def buildAnimationWithShapeTransforms(self, shapeTransformAnimations, shouldSplit, baseImage=None, shapeImage=None, overlayImage=None):
      self.startAnimation()
      for animation in shapeTransformAnimations:
        assert(len(animation) == 5)
        splitType = self.splitTypeForIndex(self.index, shouldSplit)
        if baseImage == None:
           panelImage = self.backgroundImage.copy()
        else:
           panelImage = baseImage.copy()
        if shapeImage == None:
           shapeImage = self.shapeImage.copy()
        newWidth = int(animation[2] * self.panelSize[0])
        newHeight = int(animation[3] * self.panelSize[1])
        squishedShapeImage = shapeImage.resize([newWidth, newHeight])
        if splitType == 0:
          xOffset = int(animation[0] * self.panelSize[0]) - int(squishedShapeImage.size[0] / 2) + int(self.panelSize[0] / 2)
          yOffset = int(animation[1] * self.panelSize[1]) - int(squishedShapeImage.size[1] / 2) + int(self.panelSize[1] / 2)

          blendImage = Image.new('RGBA', self.panelSize, (255, 255, 255, 0))
          blendImage.alpha_composite(squishedShapeImage, (xOffset, yOffset))
          panelImage = blendImages(panelImage, blendImage, animation[4], blend_modes.normal)
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
          panelImage.alpha_composite(splitImage, (xOffset, yOffset))
          splitImage = squishedShapeImage.crop((middle, top, right, bottom))
          xOffset = -int(animation[0] * self.panelSize[0]) + int(self.panelSize[0] / 2)
          yOffset = -int(animation[1] * self.panelSize[1]) - int(splitImage.size[1] / 2) + int(self.panelSize[1] / 2)
          panelImage.alpha_composite(splitImage, (xOffset, yOffset))
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
          panelImage.alpha_composite(splitImage, (xOffset, yOffset))
          splitImage = squishedShapeImage.crop((left, middle, right, bottom))
          xOffset = -int(animation[1] * self.panelSize[0]) - int(splitImage.size[0] / 2) + int(self.panelSize[0] / 2)
          yOffset = -int(animation[0] * self.panelSize[1]) + int(self.panelSize[1] / 2)
          panelImage.alpha_composite(splitImage, (xOffset, yOffset))
        
        if overlayImage == None:
           overlayImage = self.borderImage.copy()
        panelImage = Image.alpha_composite(panelImage, overlayImage)
        self.addFrame(panelImage)
      self.endAnimation()

  def buildFallingAnimation(self):
      # xOffset, yOffset, xScale, yScale, alpha
      animations = [[0, 0.03, 1.082, 0.92, 1]]
      self.buildAnimationWithShapeTransforms(animations, 0)

  def buildDimmedAnimation(self):
    self.startAnimation()
    panelImage = self.standardPanelImage()
    panelImage = adjustExtremes(panelImage, 0, 150)
    self.addFrame(panelImage)
    self.endAnimation()

  def buildDeadAnimation(self):
    # xOffset, yOffset, xScale, yScale, alpha
    animations = [[-0.05, 0, 1.1, 1.1, 1]]
    self.buildAnimationWithShapeTransforms(animations, 1)
  
  def buildLandingAnimation(self):
      # xOffset, yOffset, xScale, yScale, alpha
      animations = [[0, 0.075, 1.075, 0.85, 1],
                    [0, 0.09, 1.1, 0.8, 1],
                    [0, 0.075, 1.075, 0.85, 1],
                    [0, 0.06, 1.05, 0.9, 1],
                    [0, 0.03, 1.025, 0.95, 1],
                    [0, 0.015, 1.0125, 0.975, 1],
                    [0, 0, 1, 1, 1]
                    ]
      self.buildAnimationWithShapeTransforms(animations, 0)

  def buildPulseDangerAnimation(self):
      # xOffset, yOffset, xScale, yScale, alpha
      frameCount = 10
      multiplier = 1
      multiplierIncrement = 0.2 / frameCount
      alpha = 1
      alphaIncrement = -0.05
      animations = []
      for x in range(0, frameCount):
        animations.append([0, 0, multiplier, multiplier, alpha])
        multiplier += multiplierIncrement
        multiplierIncrement = multiplierIncrement * 1.4
        alpha = max(alphaIncrement + alpha, 0)
        alphaIncrement = alphaIncrement * 1.2

      for x in range(0, 3):
        last_element = animations.pop()
        animations.insert(0, last_element)
      
      overlayImage = self.shapeImage.copy()
      overlayImage = Image.alpha_composite(overlayImage, self.borderImage)
      self.buildAnimationWithShapeTransforms(animations, 0, None, None, overlayImage)

  def buildShineDangerAnimation(self):
      self.startAnimation()
      # amount = self.panelSize[0] / 2
      # for x in numpy.arange(amount, -amount, -2 * amount / 10):
      #   xOffset = int(x)
      #   yOffset = int(-x)
      #   panelImage = self.backgroundImage.copy()

      #   shineOffsetImage = Image.new('RGBA', self.panelSize, (255, 255, 255, 0))
      #   shineImage = Image.open(self.panelConfig.folder + "shine.png", mode = 'r')
      #   shineOffsetImage.alpha_composite(shineImage, (xOffset, yOffset))
        
      #   panelImage = blendImages(panelImage, shineOffsetImage, .75, blend_modes.overlay)
      #   self.addFrame(panelImage)

      alphas = []
      min = 40
      max = 100
      step = int((max - min) / 5)
      for a in numpy.arange(max, min, -step):
        alphas.append(a)
      for a in numpy.arange(min, max, step):
        alphas.append(a)

      for alpha in alphas:
        panelImage = self.backgroundImage.copy()

        shineOffsetImage = Image.new('RGBA', self.panelSize, (255, 255, 255, alpha))
        blendedShineImage = blendImages(self.borderImage, shineOffsetImage, 1, blend_modes.lighten_only)

        panelImage = Image.alpha_composite(panelImage, blendedShineImage)
        panelImage = Image.alpha_composite(panelImage, self.shapeImage)

        self.addFrame(panelImage)
      self.endAnimation()

  def buildBounceDangerAnimation(self):
      # xOffset, yOffset, xScale, yScale, alpha
      animations = [
                    [0, 0.09, 1.1, 0.8, 1],
                    [0, 0.06, 1.05, 0.9, 1],
                    [0, 0, 1, 1, 1],
                    [0, -0.02, 1, 1, 1],
                    [0, -0.04, 1, 1, 1],
                    [0, -0.06, 1, 1, 1],
                    [0, -0.04, 1, 1, 1],
                    [0, -0.02, 1, 1, 1],
                    [0, 0, 1, 1, 1],
                    [0, 0.06, 1.05, 0.9, 1],
                    ]
      if self.panelConfig.dangerBounceReduced:
        animations = map(lambda animation: [animation[0]/2, animation[1]/2, ((animation[2]-1)/2)+1, ((animation[3]-1)/2)+1, animation[4]], animations)
      self.buildAnimationWithShapeTransforms(animations, 0)
  
  def buildFlashAnimation(self):
      self.startAnimation()
      panelImage = self.standardPanelImage()
      self.addFrame(panelImage)
      panelImage = Image.alpha_composite(self.backgroundImage, self.borderImage)
      # panelImage = doubleBrightness(panelImage, 40, 1)
      panelImage = adjustExtremes(panelImage, 60, 255)
      panelImage = adjust_levels(panelImage, 0, 120)
      panelImage = Image.alpha_composite(panelImage, self.shapeImage)
      self.addFrame(panelImage)
      self.endAnimation()

  def faceImage(self):
      maskedPanelImage = self.shapeImage.copy()
      # for yPixel in range(self.panelSize[1]):
      #   for xPixel in range(self.panelSize[0]):
      #       r, g, b, a = maskedPanelImage.getpixel((xPixel, yPixel))
      #       maskedPanelImage.putpixel((xPixel, yPixel), (r, g, b, int(a * 0.6)))  # Reduce alpha by 50%
      maskedPanelImage = adjustExtremes(maskedPanelImage, 0, 150)
      return maskedPanelImage

  def buildFaceAnimation(self):
      self.startAnimation()
      maskedPanelImage = self.faceImage()
      panelImage = Image.alpha_composite(self.backgroundImage, self.borderImage)
      panelImage = Image.alpha_composite(panelImage, maskedPanelImage)
      self.addFrame(panelImage)
      self.endAnimation()

  def buildPopAnimation(self):
      multiplier = 1
      multiplierDecrement = 0.18
      animations = []
      for x in range(0, self.panelConfig.popAnimationCount):
        offset = x * -0.1
        animations.append([offset, 0, multiplier, multiplier, 1])
        multiplier -= multiplierDecrement
      baseImage = Image.new('RGBA', self.panelSize, (255, 255, 255, 0))
      overlayImage = Image.new('RGBA', self.panelSize, (255, 255, 255, 0))
      self.buildAnimationWithShapeTransforms(animations, 1, baseImage, self.faceImage(), overlayImage)

  def buildPanelBaseImages(self):
      self.backgroundImage = Image.open(self.panelConfig.folder + self.index + "background.png", mode = 'r')
      self.backgroundImage = shiftImageHue(self.backgroundImage, self.hue, self.saturation, self.lightnessFactor)
      self.borderImage = Image.open(self.panelConfig.folder + self.index + "border.png", mode = 'r')
      self.borderImage = shiftImageHue(self.borderImage, self.hue, self.saturation, self.lightnessFactor)
      self.shapeImage = Image.open(self.panelConfig.folder + self.index + "shape.png", mode = 'r')
      self.shapeImage = shiftImageHue(self.shapeImage, self.hue, self.saturation, self.lightnessFactor)

class Panels:
  def __init__(self, baseFolder, panelSettings):
    self.baseFolder = baseFolder
    self.folder = self.baseFolder + "/RawImages/"
    self.configFileName = "config.json"
    self.landingAnimationCount = 7
    self.popAnimationCount = 6
    self.maxAnimationFrames = 10
    self.animationCount = 10
    self.useDangerBounce = True
    self.dangerBounceReduced = True
    self.previewImage = None
    self.panelSettings = panelSettings

  def createSheets(self, saveDirectory):
    baseFolder = os.path.normpath(self.baseFolder)
    folderName = baseFolder.split(os.sep)[-1]
    outputFolder = saveDirectory + folderName + "/"
    os.makedirs(os.path.dirname(outputFolder), exist_ok=True)

    panelColorCount = 8
    for i in range(1, panelColorCount+1):
      index = str(i)
      hue = self.panelSettings[i-1][0]
      saturation = self.panelSettings[i-1][1]
      lightnessFactor = self.panelSettings[i-1][2]
      sheet = Sheet(self, index, hue, saturation, lightnessFactor)
      sheet.buildSheet(index)
      if i == 1:
        sheet.sheetImage.show()
        # sys.exit()
      if self.previewImage == None: 
        self.previewImage = Image.new('RGBA', (sheet.panelSize[0] * (panelColorCount), sheet.panelSize[1] * sheet.panelConfig.animationCount), (255, 255, 255, 0))
      self.previewImage.paste(sheet.sheetImage, ((i-1) * sheet.panelSize[0], 0))
      sheet.sheetImage.save(outputFolder + "panel-" + index + "@2x.png")

    fileSuffix = "@2x.png"
    panel0Name = "panel00"
    shutil.copyfile(self.folder + panel0Name + ".png", outputFolder + panel0Name + fileSuffix)
    shutil.copyfile(self.baseFolder + "/" + self.configFileName, outputFolder + self.configFileName)

    self.previewImage.show()

baseFolder = sys.argv[1]
saveFolder = sys.argv[2]
panelSettings = []
# Classic
panelSettings += [[[359 / 360.0, 1.00, 0.85],
                  [120 / 360.0, 1.00, 0.85],
                  [180 / 360.0, 1.00, 0.86],
                  [60  / 360.0, 1.00, 0.86],
                  [300 / 360.0, 1.00, 0.93],
                  [225 / 360.0, 1.00, 1.071],
                  [19  / 360.0, 1.00, 1.153],
                  [0   / 360.0, 0.00, 1.38],
                 ]]
# JamBox
panelSettings += [[[0   / 360.0, 1, 1],
                  [126 / 360.0, 1, 1.1],
                  [194 / 360.0, 1, 1],
                  [67  / 360.0, 1, 0.97],
                  [326 / 360.0, 1, 1.07],
                  [237 / 360.0, 1, 0.90],
                  [26  / 360.0, 1, 1],
                  [0   / 360.0, 0.00, 1.38],
                  ]]
# PACCI Classic
panelSettings += [[[6   / 360.0, 1.00, 1.08],
                   [75  / 360.0, 0.70, 0.90],
                   [206 / 360.0, 0.90, 1.08],
                   [48  / 360.0, 0.79, 1.19],
                   [304 / 360.0, 0.60, 1.18],
                   [35  / 360.0, 0.91, 1.04],
                   [359 / 360.0, 0.34, 0.97],
                   [0   / 360.0, 0.00, 1.38],
                  ]]
panelConfig = Panels(baseFolder, panelSettings[1])
panelConfig.createSheets(saveFolder)
