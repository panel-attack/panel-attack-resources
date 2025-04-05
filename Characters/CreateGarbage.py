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

class GarbageBlock:
  def __init__(self, garbageConfig, width, height, metal, pop, hue, saturation, lightnessFactor):
    self.garbageConfig = garbageConfig
    self.width = width
    self.height = height
    self.metal = metal
    self.pop = pop
    self.hue = hue
    self.saturation = saturation
    self.lightnessFactor = lightnessFactor
    self.panelSize = self.garbageConfig.panelSize
    self.garbageBlockImage = Image.new('RGBA', (self.panelSize[0] * width, self.panelSize[1] * height), (255, 255, 255, 0))
    self.buildGarbageBlockImage()

  def buildGarbageBlockImage(self):
    panelSize = 96
    doubleFaceHeight = 192
    drawX = (self.width - 1) * panelSize
    drawY = (self.height - 1) * panelSize
    
    halfPanelSize = int(panelSize / 2)
    garbageHeight, garbageWidth = self.height, self.width
    leftX = drawX - (garbageWidth - 1) * panelSize
    topY = drawY - (garbageHeight - 1) * panelSize
    cornerWidth = halfPanelSize
    cornerHeight = 18
    useFiller1 = ((garbageHeight - (garbageHeight % 2)) / 2) % 2 == 0
    filler_w, filler_h = self.panelSize[0], self.panelSize[1]

    if self.pop > 0:
      pop = self.garbageConfig.pop
      if self.pop == 2:
        pop = self.garbageConfig.flash
      for i in range(0, garbageHeight):
        for j in range(0, garbageWidth):
          self.drawGfxScaled(pop, panelSize * j, panelSize * i, 0, panelSize / filler_w, panelSize / filler_h)
    else:
      for i in range(0, garbageHeight):
        for j in range(0, garbageWidth - 1):
          if (useFiller1 or garbageHeight < 3):
            filler = self.garbageConfig.filler1
          else:
            filler = self.garbageConfig.filler2
          self.drawGfxScaled(filler, drawX - panelSize * j - halfPanelSize, topY + panelSize * i, 0, panelSize / filler_w, panelSize / filler_h)
          useFiller1 = not useFiller1
      
      if garbageHeight % 2 == 1:
        if self.garbageConfig.face2 and garbageWidth % 2 == 1:
          face = self.garbageConfig.face2
        else:
          face = self.garbageConfig.face
        face_w, face_h = face.size[0], face.size[1]
        self.drawGfxScaled(face, drawX - halfPanelSize * (garbageWidth - 1), topY + panelSize * int((garbageHeight - 1) / 2), 0, panelSize / face_w, panelSize / face_h)
      else:
        face_w, face_h = self.garbageConfig.doubleface.size[0], self.garbageConfig.doubleface.size[1]
        self.drawGfxScaled(self.garbageConfig.doubleface, drawX - halfPanelSize * (garbageWidth - 1), topY + panelSize * ((garbageHeight - 2) / 2), 0, panelSize / face_w, doubleFaceHeight / face_h)

      corner_w, corner_h = self.garbageConfig.topleft.size[0], self.garbageConfig.topleft.size[1]
      lr_w, lr_h = self.garbageConfig.left.size[0], self.garbageConfig.left.size[1]
      topbottom_w, topbottom_h = self.garbageConfig.top.size[0], self.garbageConfig.top.size[1]
      self.drawGfxScaled(self.garbageConfig.left, leftX, topY + cornerHeight, 0, halfPanelSize / lr_w, (1 / lr_h) * (garbageHeight * panelSize - (cornerHeight*2)))
      self.drawGfxScaled(self.garbageConfig.right, drawX + halfPanelSize, topY + cornerHeight, 0, halfPanelSize / lr_w, (1 / lr_h) * (garbageHeight * panelSize - (cornerHeight*2)))
      self.drawGfxScaled(self.garbageConfig.top, leftX + cornerWidth, topY, 0, (1 / topbottom_w) * (garbageWidth * panelSize - (cornerWidth*2)), 1)
      self.drawGfxScaled(self.garbageConfig.bot, leftX + cornerWidth, drawY + panelSize - topbottom_h, 0, (1 / topbottom_w) * (garbageWidth * panelSize - (cornerWidth*2)), 1)
      self.drawGfxScaled(self.garbageConfig.topleft, leftX, topY, 0, cornerWidth / corner_w, cornerHeight / corner_h)
      self.drawGfxScaled(self.garbageConfig.topright, drawX + halfPanelSize, topY, 0, cornerWidth / corner_w, cornerHeight / corner_h)
      self.drawGfxScaled(self.garbageConfig.botleft, leftX, drawY + panelSize - corner_h, 0, cornerWidth / corner_w, cornerHeight / corner_h)
      self.drawGfxScaled(self.garbageConfig.botright, drawX + halfPanelSize, drawY + panelSize - corner_h, 0, cornerWidth / corner_w, cornerHeight / corner_h)
      
  def drawGfxScaled(self, image, x, y, rot, xScale, yScale):
    newWidth = int(xScale * image.size[0])
    newHeight = int(yScale * image.size[1])
    resizedImage = image.resize([newWidth, newHeight])
    self.garbageBlockImage.alpha_composite(resizedImage, (int(x), int(y)))
  
class Garbage:
  def __init__(self, baseFolder, panelSettings):
    self.folder = baseFolder + "/"
    self.previewImage = None
    self.panelSettings = panelSettings
    self.panelSize = [96, 96]
    self.loadBaseImages()

  def loadBaseImages(self):
      self.portrait = self.loadImageWithError("portrait")
      self.icon = self.loadImageWithDefault("icon")
      self.face = self.loadImageWithDefault("face")

      self.bot = self.loadImageWithDefault("bot")
      self.botleft = self.loadImageWithDefault("botleft")
      self.botright = self.loadImageWithDefault("botright")
      self.burst = self.loadImageWithDefault("burst")
      self.doubleface = self.loadImageWithDefault("doubleface")
      self.fade = self.loadImageWithDefault("fade")
      self.filler1 = self.loadImageWithDefault("filler1")
      self.filler2 = self.loadImageWithDefault("filler2")
      self.flash = self.loadImageWithDefault("flash")
      self.left = self.loadImageWithDefault("left")
      self.pop = self.loadImageWithDefault("pop")
      self.right = self.loadImageWithDefault("right")
      self.attack = self.loadImageWithDefault("telegraph/attack")
      self.top = self.loadImageWithDefault("top")
      self.topleft = self.loadImageWithDefault("topleft")
      self.topright = self.loadImageWithDefault("topright")

      self.face2 = self.loadImageOptional("face2")

  def loadImageWithDefault(self, filename):
    result = Image.open(self.folder + filename + "@2x.png", mode = 'r')
    if result == None:
      result = Image.open(self.defaultFolder + filename + "@2x.png", mode = 'r')
    result = result.convert("RGBA")
    return result

  def loadImageOptional(self, filename):
    fullPath = self.folder + filename + "@2x.png"
    result = None
    if os.path.isfile(fullPath):
      result = Image.open(fullPath, mode = 'r')
    return result
  
  def loadImageWithError(self, filename):
    result = Image.open(self.folder + filename + "@2x.png", mode = 'r')
    assert(result != None)
    return result
  
  def createGarbage(self, saveDirectory):
    outputFolder = saveDirectory + "/"
    os.makedirs(os.path.dirname(outputFolder), exist_ok=True)

    self.garbageBlocks = []
    blockSettings = [[3, 1, 0, 0],
                    [4, 1, 0, 0],
                    [5, 1, 0, 0],
                    [6, 1, 0, 0],
                    [6, 2, 0, 0],
                    [6, 3, 0, 0],
                    [6, 1, 1, 0],
                    [6, 1, 0, 1],
                    [6, 1, 0, 2]
                    ]
    
    for blockSetting in blockSettings:
      hue = self.panelSettings[0]
      saturation = self.panelSettings[1]
      lightnessFactor = self.panelSettings[2]
      width = blockSetting[0]
      height = blockSetting[1]
      metal = blockSetting[2] == 1
      pop = blockSetting[3]
      garbageBlock = GarbageBlock(self, width, height, metal, pop, hue, saturation, lightnessFactor)
      # garbageBlock.garbageBlockImage.show()
      # sys.exit()
      # self.previewImage.paste(garbageBlock.garbageBlockImage, ((i-1) * garbageBlock.panelSize[0], 0))
      # garbageBlock.garbageBlockImage.save(outputFolder + "panel-" + index + "@2x.png")
      self.garbageBlocks.append(garbageBlock)

    previewWidth = 0
    previewHeight = 0
    for garbageBlock in self.garbageBlocks:
      previewWidth = max(garbageBlock.garbageBlockImage.size[0], previewWidth)
      previewHeight += garbageBlock.garbageBlockImage.size[1]
      
    drawX = 0
    drawY = 0
    self.previewImage = Image.new('RGBA', (previewWidth, previewHeight), (255, 255, 255, 0))
    for garbageBlock in self.garbageBlocks:
      self.previewImage.alpha_composite(garbageBlock.garbageBlockImage, (drawX, drawY))
      drawY += garbageBlock.garbageBlockImage.size[1]

    self.previewImage.show()

baseFolder = sys.argv[1]
saveFolder = sys.argv[2]
garbageSettings = [359 / 360.0, 1.00, 0.85]

garbage = Garbage(baseFolder, garbageSettings)
garbage.createGarbage(saveFolder)
