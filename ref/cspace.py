
from jpg import *

class CSpace:

    def __init__(self) -> None:
        pass

    def YCbCrToRGBBlock(self, yBlock: Block, cbcrBlock: Block, vSamp, hSamp, v, h):
        for y in range(7, -1, -1):
            for x in range(7, -1, -1):
                pixel = y * 8 + x
                cbcrPixelRow = y // vSamp + 4 * v
                cbcrPixelColumn = x // hSamp + 4 * h
                cbcrPixel = cbcrPixelRow * 8 + cbcrPixelColumn
                r = yBlock.y_r[pixel]                                    + 1.402 * cbcrBlock.cr_b[cbcrPixel] + 128
                g = yBlock.y_r[pixel] - 0.344 * cbcrBlock.cb_g[cbcrPixel] - 0.714 * cbcrBlock.cr_b[cbcrPixel] + 128
                b = yBlock.y_r[pixel] + 1.772 * cbcrBlock.cb_g[cbcrPixel]                                    + 128
                if (r < 0):   r = 0
                if (r > 255): r = 255
                if (g < 0):   g = 0
                if (g > 255): g = 255
                if (b < 0):   b = 0
                if (b > 255): b = 255
                yBlock.y_r[pixel] = r
                yBlock.cb_g[pixel] = g
                yBlock.cr_b[pixel] = b

    def YCbCrToRGB(self, image: JPGImage):
        vSamp = image.verticalSamplingFactor
        hSamp = image.horizontalSamplingFactor

        if vSamp != 1 or hSamp != 1:
            assert False, 'Not supported'
            self.YCbCrToRGBSample(image)
        else:
            self.YCbCrToRGBNoSample(image)

    def YCbCrToRGBSample(self, image: JPGImage):
        vSamp = image.verticalSamplingFactor
        hSamp = image.horizontalSamplingFactor

        for y in range(0, image.blockHeight, vSamp):
            for x in range(0, image.blockWidth, hSamp):
                cbcrBlock: Block = image.blocks[y * image.blockWidthReal + x]
                for v in range(vSamp-1, -1, -1):
                    for h in range(hSamp-1, -1, -1):
                        print(f'{v=} {h=}')
                        yBlock: Block = image.blocks[y * image.blockWidthReal + x]
                        self.YCbCrToRGBBlock(yBlock, cbcrBlock, vSamp, hSamp, v, h)


    def YCbCrToRGBNoSample(self, image: JPGImage):
        for block in image.blocks:
            self.YCbCrToRGBBlock(block, block, 1, 1, 0, 0)