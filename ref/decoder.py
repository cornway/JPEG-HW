
from bitreader import *
from jpg import *
from huffman import *
from quant import *
from dct import *
from cspace import *
from bmp import *

class Decoder:

    br: Bitreader
    image: JPGImage
    huff: HuffmanDecoder
    quant: Quantization
    dct: Dct
    cspace: CSpace

    def __init__(self, br: Bitreader) -> None:
        self.br = br
        self.image = JPGImage()
        self.huff = HuffmanDecoder(br)
        self.quant = Quantization(br)
        self.dct = Dct()
        self.cspace = CSpace()

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
                self.quant.readQuantizationTable()
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

    def readScans(self):
        self.readStartOfScan()

        self.printScanInfo()

        self.huff.decodeHuffmanData(self.image)

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

        self.quant.printInfo()

def readJPG(fpath: str):
    print(f'Reading {fpath}...')
    br = Bitreader(fpath)
    decoder = Decoder(br)

    decoder.readFrameHeader()

    assert decoder.image.valid

    decoder.printFrameInfo()

    decoder.image.blocks = declList(Block, int(decoder.image.blockHeightReal * decoder.image.blockWidthReal))

    decoder.readScans()

    decoder.quant.dequantize(decoder.image)

    decoder.dct.inverseDCT(decoder.image)

    decoder.cspace.YCbCrToRGB(decoder.image)

    return decoder.image

if __name__ == '__main__':
    import sys

    fpath = sys.argv[1]
    outpath = sys.argv[2]

    image = readJPG(fpath)

    bmp = Bmp()

    bmp.writeBMP(image, outpath)