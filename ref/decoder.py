
from bitreader import *
from jpg import *
from huffman import *

class Decoder:

    br: Bitreader
    image: JPGImage
    huff: HuffmanDecoder

    def __init__(self, br: Bitreader) -> None:
        self.br = br
        self.image = JPGImage()
        self.huff = HuffmanDecoder(br)

    def readStartOfFrame(self):
        print('Reading SOF Marker')
        assert self.image.numComponents == 0, 'Error - Multiple SOFs detected'

        length = self.br.readWord()
        precission = self.br.readByte()

        assert precission == 8, f'Error - Invalid precision: {precission}'

        self.image.height = self.br.readWord()
        self.image.width = self.br.readWord()

        assert self.image.height != 0 and self.image.width != 0, 'Error - Invalid dimensions'

        self.image.blockHeight = (self.image.height + 7) // 8
        self.image.blockWidth = (self.image.width + 7) // 8
        self.image.blockHeightReal = self.image.blockHeight
        self.image.blockWidthReal = self.image.blockWidth

        self.image.numComponents = self.br.readByte()

        assert self.image.numComponents != 4, 'Error - CMYK color mode not supported'
        assert self.image.numComponents == 1 or self.image.numComponents == 3, \
            f'Error - {self.image.numComponents} color components given (1 or 3 required)'

        for i in range(self.image.numComponents):
            componentID = self.br.readByte()

            if componentID == 0 and i == 0:
                self.image.zeroBased = True

            if self.image.zeroBased:
                componentID += 1

            assert componentID != 0 and componentID <= self.image.numComponents, \
                f'Error - Invalid component ID: {componentID}'
            
            component: ColorComponent = self.image.colorComponents[componentID - 1]
            assert not component.usedInFrame, f'Error - Duplicate color component ID: {componentID}'

            component.usedInFrame = True
            samplingFactor = self.br.readByte()
            component.horizontalSamplingFactor = samplingFactor >> 4
            component.verticalSamplingFactor = samplingFactor & 0x0F

            if componentID == 1:
                assert component.horizontalSamplingFactor == 1 and component.horizontalSamplingFactor != 2, \
                    'Error - Sampling factors not supported'
                assert component.verticalSamplingFactor == 1 and component.verticalSamplingFactor != 2, \
                    'Error - Sampling factors not supported'

                if (component.horizontalSamplingFactor == 2 and self.image.blockWidth % 2 == 1):
                    self.image.blockWidthReal += 1

                if (component.verticalSamplingFactor == 2 and self.image.blockHeight % 2 == 1):
                    self.image.blockHeightReal += 1

                self.image.horizontalSamplingFactor = component.horizontalSamplingFactor
                self.image.verticalSamplingFactor = component.verticalSamplingFactor
            else:
                assert component.horizontalSamplingFactor == 1 and component.verticalSamplingFactor == 1, \
                    'Error - Sampling factors not supported'
                
            component.quantizationTableID = self.br.readByte()
            assert component.quantizationTableID <= 3, f'Error - Invalid quantization table ID: {component.quantizationTableID}'

        assert length - 8 - (3 * self.image.numComponents) == 0, 'Error - SOF invalid'


    def readQuantizationTable(self):
        print('Reading DQT Marker')

        length = self.br.readWord()
        length -= 2

        while length > 0:
            tableInfo = self.br.readByte()
            length -= 1
            tableID = tableInfo & 0x0f

            assert tableID <= 3, f'Error - Invalid quantization table ID: {tableID}'

            qTable: QuantizationTable = self.image.quantizationTables[tableID]
            assert not qTable.set
            qTable.set = True

            table = [0] * len(qTable.table)

            if (tableInfo >> 4) != 0:
                for i in range(64):
                    table[zigZagMap[i]] = self.br.readWord()
                length -= 128
            else:
                for i in range(64):
                    table[zigZagMap[i]] = self.br.readByte()
                length -= 64

            qTable.table = table

    def readRestartInterval(self):
        print('Reading DRI Marker')

        length = self.br.readWord()
        self.image.restartInterval = self.br.readWord()
        assert length - 4 == 0, 'Error - DRI invalid'

    def readAPPN(self):
        print('Reading APPN Marker')
        length = self.br.readWord()

        assert length >= 2, 'Error - APPN invalid'

        for _ in range(length-2):
            self.br.readByte()

    def readComment(self):
        print('Reading COM Marker')
        length = self.br.readWord()

        assert length >= 2, 'Error - COM invalid'

        for _ in range(length-2):
            self.br.readByte()

    def readFrameHeader(self):
        last = self.br.readByte()
        current = self.br.readByte()

        assert (last == 0xff) and (current == JPG.SOI), 'Error - SOI invalid'

        last = self.br.readByte()
        current = self.br.readByte()

        while self.image.valid:
            assert last == 0xff, 'Error - Expected a marker'

            if current == JPG.SOF0:
                self.image.frameType = JPG.SOF0
                self.readStartOfFrame()
            elif current == JPG.SOF2:
                self.image.frameType = JPG.SOF2
                self.readStartOfFrame()
            elif current == JPG.DQT:
                self.readQuantizationTable()
            elif current == JPG.DHT:
                self.huff.readHuffmanTable()
            elif current == JPG.SOS:
                break
            elif current == JPG.DRI:
                self.readRestartInterval()
            elif current >= JPG.APP0 and current <= JPG.APP15:
                self.readAPPN()
            elif current == JPG.COM:
                self.readComment()
            elif (current >= JPG.JPG0 and current <= JPG.JPG13) or \
                    current == JPG.DNL or \
                    current == JPG.DHP or \
                    current == JPG.EXP:
                self.readComment()

            elif current == JPG.TEM:
                pass

            elif current == 0xff:
                current = self.br.readByte()
                continue
            else:
                assert current != JPG.SOI, 'Error - Embedded JPGs not supported'
                assert current != JPG.EOI, 'Error - EOI detected before SOS'
                assert current != JPG.DAC, 'Error - Arithmetic Coding mode not supported'
                assert current < JPG.SOF0 and current > JPG.SOF15, f'Error - SOF marker not supported: {hex(current)}'
                assert current < JPG.RST0 and current > JPG.RST7, 'Error - RSTN detected before SOS'

                assert False, f'Error - Unknown marker: {hex(current)}'

            last = self.br.readByte()
            current = self.br.readByte()

    def readStartOfScan(self):
        print('Reading SOS Marker')

        assert self.image.numComponents != 0
        length = self.br.readWord()
        
        for i in range(self.image.numComponents):
            self.image.colorComponents[i].usedInScan = False

        self.image.componentsInScan = self.br.readByte()
        assert self.image.componentsInScan != 0

        for i in range (self.image.componentsInScan):
            componentID = self.br.readByte()

            if self.image.zeroBased:
                componentID += 1

            assert componentID != 0 and componentID <= self.image.numComponents, \
                f'Error - Invalid color component ID: {componentID}'
            
            component: ColorComponent = self.image.colorComponents[componentID - 1]
            assert component.usedInFrame, f'Error - Invalid color component ID: {componentID}'

            assert not component.usedInScan, f'Error - Duplicate color component ID: {componentID}'

            component.usedInScan = True

            huffmanTableIDs = self.br.readByte()
            component.huffmanDCTableID = huffmanTableIDs >> 4
            component.huffmanACTableID = huffmanTableIDs & 0x0F

            assert component.huffmanDCTableID <= 3, f'Error - Invalid Huffman DC table ID: {component.huffmanDCTableID}'
            assert component.huffmanACTableID <= 3, f'Error - Invalid Huffman AC table ID: {component.huffmanACTableID}'

        self.image.startOfSelection = self.br.readByte()
        self.image.endOfSelection = self.br.readByte()
        successiveApproximation = self.br.readByte()

        self.image.successiveApproximationHigh = successiveApproximation >> 4
        self.image.successiveApproximationLow = successiveApproximation & 0x0F

        if self.image.frameType == JPG.SOF0:
            assert self.image.startOfSelection == 0 and self.image.endOfSelection == 63, \
                'Error - Invalid spectral selection'
            
            assert self.image.successiveApproximationHigh == 0 and self.image.successiveApproximationLow == 0, \
                'Error - Invalid successive approximation'
        elif self.image.frameType == JPG.SOF2:
            assert False, 'JPG.SOF2: Not supported'

        for i in range(self.image.numComponents):
            component: ColorComponent = self.image.colorComponents[i]

            if component.usedInScan:
                assert self.huff.dcTables[component.huffmanDCTableID].set, \
                    'Error - Color component using uninitialized Huffman DC table'

                assert self.huff.acTables[component.huffmanACTableID].set, \
                    'Error - Color component using uninitialized Huffman AC table'

        assert length - 6 - (2 * self.image.componentsInScan) == 0, 'Error - SOS invalid'

    def printScanInfo(self):
        print("SOS=============\n")
        print(f"Start of Selection: {self.image.startOfSelection}")
        print(f"End of Selection: {self.image.endOfSelection}")
        print(f"Successive Approximation High: {self.image.successiveApproximationHigh}")
        print(f"Successive Approximation Low: {self.image.successiveApproximationLow}")
        print("Color Components:\n")
        for i in range(self.image.numComponents):
            if (self.image.colorComponents[i].usedInScan):
                print(f"Component ID: {(i + 1)}")
                print(f"Huffman DC Table ID: {self.image.colorComponents[i].huffmanDCTableID}")
                print(f"Huffman AC Table ID: {self.image.colorComponents[i].huffmanACTableID}")

        self.huff.printScanInfo()

        print("DRI=============\n")
        print(f"Restart Interval: {self.image.restartInterval}")

    def decodeHuffmanData(self):
        previousDCs = [0] * 3

        luminanceOnly = self.image.componentsInScan == 1 and self.image.colorComponents[0].usedInScan
        yStep = 1 if luminanceOnly else self.image.verticalSamplingFactor
        xStep = 1 if luminanceOnly else self.image.horizontalSamplingFactor
        restartInterval = int(self.image.restartInterval * xStep * yStep)

        for y in range(0, self.image.blockHeight, yStep):
            for x in range(0, self.image.blockWidth, xStep):
                if restartInterval != 0 and ((y * self.image.blockWidthReal + x) % restartInterval) == 0:
                    previousDCs = [0] * 3
                    self.br.align()

                for i in range(self.image.numComponents):
                    component: ColorComponent = self.image.colorComponents[i]
                    if component.usedInScan:
                        vMax = 1 if luminanceOnly else component.verticalSamplingFactor
                        hMax = 1 if luminanceOnly else component.horizontalSamplingFactor

                        for v in range(vMax):
                            for h in range(hMax):
                                block = self.image.blocks[(y + v) * self.image.blockWidthReal + (x + h)].get(i)
                                previousDCs[i] = self.huff.decodeBlockComponent(
                                        block,
                                        previousDCs[i],
                                        component.huffmanDCTableID,
                                        component.huffmanACTableID)

                                self.image.blocks[(y + v) * self.image.blockWidthReal + (x + h)].set(i, block)

    def readScans(self):
        self.readStartOfScan()

        self.printScanInfo()

        self.decodeHuffmanData()

        last = self.br.readByte()
        current = self.br.readByte()

        while True:

            assert last == 0xff, 'Error - Expected a marker'

            if current == JPG.EOI:
                break

            assert self.image.frameType != JPG.SOF2

            if current >= JPG.RST0 and current <= JPG.RST7:
                pass

            elif current == 0xff:
                current = self.br.readByte()
                continue
            else:
                assert False, f'Error - Invalid marker: {current}'

            last = self.br.readByte()
            current = self.br.readByte()

    def printFrameInfo(self):
        print("SOF=============")
        print(f"Frame Type: {hex(self.image.frameType)}")
        print(f"Height: {self.image.height}")
        print(f"Width: {self.image.width}")
        print("Color Components:")
        for i in range(self.image.numComponents):
            if (self.image.colorComponents[i].usedInFrame):
                print(f"Component ID: {i + 1}")
                print(f"Horizontal Sampling Factor: {self.image.colorComponents[i].horizontalSamplingFactor}")
                print(f"Vertical Sampling Factor: {self.image.colorComponents[i].verticalSamplingFactor}")
                print(f"Quantization Table ID: {self.image.colorComponents[i].quantizationTableID}")

        print("DQT=============")
        for i in range (len(self.image.quantizationTables)):
            qTable: QuantizationTable = self.image.quantizationTables[i]
            if (qTable.set):
                print(f"Table ID: {i}")
                print("Table Data:")
                for j, v in enumerate(qTable.table):
                    if (j % 8) == 0:
                        print('')
                    print(f"{v} ", end='')
                print('')



    def dequantizeBlockComponent(self, qTable: QuantizationTable, component: list):
        for i in range(64):
            component[i] *= qTable.table[i]

    def dequantize(self):
        for y in range(0, self.image.blockHeight, self.image.verticalSamplingFactor):
            for x in range(0, self.image.blockWidth, self.image.horizontalSamplingFactor):
                for i in range(self.image.numComponents):
                    component: ColorComponent = self.image.colorComponents[i]
                    for v in range(component.verticalSamplingFactor):
                        for h in range(component.horizontalSamplingFactor):
                            block = self.image.blocks[(y + v) * self.image.blockWidthReal + (x + h)].get(i).copy()

                            self.dequantizeBlockComponent(self.image.quantizationTables[component.quantizationTableID],
                                                    block)
                            
                            self.image.blocks[(y + v) * self.image.blockWidthReal + (x + h)].set(i, block)

    def inverseDCTBlockComponent(self, component: list):

        intermediate: list = [0.0] * 64

        for i in range(8):
            g0 = component[0 * 8 + i] * s0
            g1 = component[4 * 8 + i] * s4
            g2 = component[2 * 8 + i] * s2
            g3 = component[6 * 8 + i] * s6
            g4 = component[5 * 8 + i] * s5
            g5 = component[1 * 8 + i] * s1
            g6 = component[7 * 8 + i] * s7
            g7 = component[3 * 8 + i] * s3

            f0 = g0
            f1 = g1
            f2 = g2
            f3 = g3
            f4 = g4 - g7
            f5 = g5 + g6
            f6 = g5 - g6
            f7 = g4 + g7

            e0 = f0
            e1 = f1
            e2 = f2 - f3
            e3 = f2 + f3
            e4 = f4
            e5 = f5 - f7
            e6 = f6
            e7 = f5 + f7
            e8 = f4 + f6

            d0 = e0
            d1 = e1
            d2 = e2 * m1
            d3 = e3
            d4 = e4 * m2
            d5 = e5 * m3
            d6 = e6 * m4
            d7 = e7
            d8 = e8 * m5

            c0 = d0 + d1
            c1 = d0 - d1
            c2 = d2 - d3
            c3 = d3
            c4 = d4 + d8
            c5 = d5 + d7
            c6 = d6 - d8
            c7 = d7
            c8 = c5 - c6

            b0 = c0 + c3
            b1 = c1 + c2
            b2 = c1 - c2
            b3 = c0 - c3
            b4 = c4 - c8
            b5 = c8
            b6 = c6 - c7
            b7 = c7

            intermediate[0 * 8 + i] = b0 + b7
            intermediate[1 * 8 + i] = b1 + b6
            intermediate[2 * 8 + i] = b2 + b5
            intermediate[3 * 8 + i] = b3 + b4
            intermediate[4 * 8 + i] = b3 - b4
            intermediate[5 * 8 + i] = b2 - b5
            intermediate[6 * 8 + i] = b1 - b6
            intermediate[7 * 8 + i] = b0 - b7

        for i in range(8):
            g0 = intermediate[i * 8 + 0] * s0
            g1 = intermediate[i * 8 + 4] * s4
            g2 = intermediate[i * 8 + 2] * s2
            g3 = intermediate[i * 8 + 6] * s6
            g4 = intermediate[i * 8 + 5] * s5
            g5 = intermediate[i * 8 + 1] * s1
            g6 = intermediate[i * 8 + 7] * s7
            g7 = intermediate[i * 8 + 3] * s3

            f0 = g0
            f1 = g1
            f2 = g2
            f3 = g3
            f4 = g4 - g7
            f5 = g5 + g6
            f6 = g5 - g6
            f7 = g4 + g7

            e0 = f0
            e1 = f1
            e2 = f2 - f3
            e3 = f2 + f3
            e4 = f4
            e5 = f5 - f7
            e6 = f6
            e7 = f5 + f7
            e8 = f4 + f6

            d0 = e0
            d1 = e1
            d2 = e2 * m1
            d3 = e3
            d4 = e4 * m2
            d5 = e5 * m3
            d6 = e6 * m4
            d7 = e7
            d8 = e8 * m5

            c0 = d0 + d1
            c1 = d0 - d1
            c2 = d2 - d3
            c3 = d3
            c4 = d4 + d8
            c5 = d5 + d7
            c6 = d6 - d8
            c7 = d7
            c8 = c5 - c6

            b0 = c0 + c3
            b1 = c1 + c2
            b2 = c1 - c2
            b3 = c0 - c3
            b4 = c4 - c8
            b5 = c8
            b6 = c6 - c7
            b7 = c7

            component[i * 8 + 0] = b0 + b7 + 0.5
            component[i * 8 + 1] = b1 + b6 + 0.5
            component[i * 8 + 2] = b2 + b5 + 0.5
            component[i * 8 + 3] = b3 + b4 + 0.5
            component[i * 8 + 4] = b3 - b4 + 0.5
            component[i * 8 + 5] = b2 - b5 + 0.5
            component[i * 8 + 6] = b1 - b6 + 0.5
            component[i * 8 + 7] = b0 - b7 + 0.5

    def inverseDCT(self):
        for y in range(0, self.image.blockHeight, self.image.verticalSamplingFactor):
            for x in range(0, self.image.blockWidth, self.image.horizontalSamplingFactor):
                for i in range(self.image.numComponents):
                    component: ColorComponent = self.image.colorComponents[i]
                    for v in range(component.verticalSamplingFactor):
                        for h in range(component.horizontalSamplingFactor):
                            block = self.image.blocks[(y + v) * self.image.blockWidthReal + (x + h)].get(i)
                            self.inverseDCTBlockComponent(block)
                            self.image.blocks[(y + v) * self.image.blockWidthReal + (x + h)].set(i, block)

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

    def YCbCrToRGB(self):
        vSamp = self.image.verticalSamplingFactor
        hSamp = self.image.horizontalSamplingFactor
        for y in range(0, self.image.blockHeight, vSamp):
            for x in range(0, self.image.blockWidth, hSamp):
                cbcrBlock: Block = self.image.blocks[y * self.image.blockWidthReal + x]
                for v in range(vSamp-1, -1, -1):
                    for h in range(hSamp-1, -1, -1):
                        yBlock: Block = self.image.blocks[(y + v) * self.image.blockWidthReal + (x + h)]
                        self.YCbCrToRGBBlock(yBlock, cbcrBlock, vSamp, hSamp, v, h)



def putShort(buffer: bytearray, v):
    buffer.append((v) & 0xff)
    buffer.append((v >> 8) & 0xff)

def putInt(buffer: bytearray, v):
    buffer.append(v & 0xff)
    buffer.append((v >> 8) & 0xff)
    buffer.append((v >> 16) & 0xff)
    buffer.append((v >> 24) & 0xff)

def writeBMP(image: JPGImage, fpath):

    buffer = bytearray()
    paddingSize = image.width % 4
    size = 14 + 12 + image.height * image.width * 3 + paddingSize * image.height

    buffer.extend('B'.encode('utf-8'))
    buffer.extend('M'.encode('utf-8'))

    putInt(buffer, size)
    putInt(buffer, 0)
    putInt(buffer, 0x1A)
    putInt(buffer, 12)
    putShort(buffer, image.width)
    putShort(buffer, image.height)
    putShort(buffer, 1)
    putShort(buffer, 24)

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

def readJPG(fpath: str):
    print(f'Reading {fpath}...')
    br = Bitreader(fpath)
    decoder = Decoder(br)

    decoder.readFrameHeader()

    assert decoder.image.valid

    decoder.printFrameInfo()

    decoder.image.blocks = declList(Block, int(decoder.image.blockHeightReal * decoder.image.blockWidthReal))

    decoder.readScans()

    decoder.dequantize()

    decoder.inverseDCT()

    decoder.YCbCrToRGB()

    return decoder.image

if __name__ == '__main__':
    import sys

    fpath = sys.argv[1]
    outpath = sys.argv[2]

    image = readJPG(fpath)

    writeBMP(image, outpath)