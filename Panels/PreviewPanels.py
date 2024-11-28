#brew install pillow
import os
import sys
import shutil
from PIL import Image, ImageDraw, ImageEnhance, ImageFont
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
  def __init__(self, panelConfig, folder):
    self.folder = folder
    self.panelConfig = panelConfig
    self.x = 0
    self.sheetImage = None

  def addFrame(self, image):
    assert(self.x < 8)
    if self.sheetImage == None: 
      self.sheetImage = Image.new('RGBA', (self.panelConfig.panelSize[0] * self.panelConfig.colorCount + self.panelConfig.panelNameWidth, self.panelConfig.panelSize[1]), (255, 0, 0, 0))

    self.sheetImage.paste(image, (self.x * self.panelConfig.panelSize[0], 0))
    self.x += 1
    # print(self.x)

  def loadSheet(self):
    for i in range(1, self.panelConfig.colorCount+1):
      panelImage = self.panelImageForIndex(str(i))
      self.addFrame(panelImage)

    text = self.folder.split("/")[-1]
    font = ImageFont.truetype("Oswald-Light.ttf", 48)
    text_color = (255, 255, 255)  # White color

    # Draw the text on the image
    draw = ImageDraw.Draw(self.sheetImage)
    draw.text((self.panelConfig.panelSize[0] * self.panelConfig.colorCount + 10, 10), text, font=font, fill=text_color)

  def panelImageForIndex(self, index):
    singleImagePath = self.folder + "/panel" + index + "1.png"
    singleImagePathHiRes = self.folder + "/panel" + index + "1@2x.png"
    sheetImagePath = self.folder + "/panel-" + index + ".png"
    sheetImagePathHiRes = self.folder + "/panel-" + index + "@2x.png"
    if os.path.exists(singleImagePathHiRes):
      panelImage = Image.open(singleImagePathHiRes, mode = 'r')
    elif os.path.exists(singleImagePath):
      panelImage = Image.open(singleImagePath, mode = 'r')
      panelImage = panelImage.resize([self.panelConfig.panelSize[0], self.panelConfig.panelSize[1]])
    elif os.path.exists(sheetImagePathHiRes):
      panelImage = Image.open(sheetImagePathHiRes, mode = 'r')
    elif os.path.exists(sheetImagePath):
      panelImage = Image.open(sheetImagePath, mode = 'r')
      panelImage = panelImage.resize([panelImage.size[0]*2, panelImage.size[1]*2])
    else:
      panelImage = Image.new('RGBA', (96, 96), (255, 0, 0, 0))


    return panelImage


class PanelsConfig:
  def __init__(self, baseFolder):
    self.baseFolder = baseFolder
    self.previewImage = None
    self.panelFolders = []
    self.currentRow = 0
    self.panelSize = [96, 96]
    self.panelNameWidth = 400

  def addPanelsFromDirectory(self, directory):
    print(directory)
    sheet = Sheet(self, directory)
    sheet.loadSheet()

    if self.previewImage == None: 
      self.previewImage = Image.new('RGBA', (sheet.sheetImage.size[0], sheet.sheetImage.size[1] * len(self.panelFolders)), (255, 0, 0, 0))
    self.previewImage.paste(sheet.sheetImage, (0, self.currentRow * self.panelSize[1]))   

    self.currentRow += 1

  def searchDirectory(self, directory):
    for root, dirs, files in os.walk(directory):
      if "__" in root:
        continue

      for fileName in files:
        if fileName == "config.json":
          self.panelFolders.append(root)
    
  def createSheets(self):
    self.colorCount = 8

    self.searchDirectory(self.baseFolder)
    
    for panelFolder in self.panelFolders:
      self.addPanelsFromDirectory(panelFolder)

    self.previewImage.show()

panelConfig = PanelsConfig(sys.argv[1])
panelConfig.createSheets()
