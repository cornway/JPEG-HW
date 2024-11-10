
from jpg import *

class Bmp:
    def putShort(self, buffer: bytearray, v):
        buffer.append((v) & 0xff)
        buffer.append((v >> 8) & 0xff)

    def putInt(self, buffer: bytearray, v):
        buffer.append(v & 0xff)
        buffer.append((v >> 8) & 0xff)
        buffer.append((v >> 16) & 0xff)
        buffer.append((v >> 24) & 0xff)

    def writeBMP(self, image: JPGImage, fpath):

        buffer = bytearray()
        paddingSize = image.width % 4
        size = 14 + 12 + image.height * image.width * 3 + paddingSize * image.height

        buffer.extend('B'.encode('utf-8'))
        buffer.extend('M'.encode('utf-8'))

        self.putInt(buffer, size)
        self.putInt(buffer, 0)
        self.putInt(buffer, 0x1A)
        self.putInt(buffer, 12)
        self.putShort(buffer, image.width)
        self.putShort(buffer, image.height)
        self.putShort(buffer, 1)
        self.putShort(buffer, 24)

        for y in range(image.height-1, -1, -1):
            blockRow = y // 8
            pixelRow = y % 8
            for x in range(image.width):
                blockColumn = x // 8
                pixelColumn = x % 8
                blockIndex = int(blockRow * image.blockWidthReal + blockColumn)
                pixelIndex = int(pixelRow * 8 + pixelColumn)

                b = int(image.blocks[blockIndex].cr_b[pixelIndex])
                g = int(image.blocks[blockIndex].cb_g[pixelIndex])
                r = int(image.blocks[blockIndex].y_r[pixelIndex])

                buffer.append(b)
                buffer.append(g)
                buffer.append(r)

                for i in range(paddingSize):
                    buffer.append(0)


        with open(fpath, 'wb') as f:
            f.write(buffer)
            f.close()