
from bitreader import *
from jpg import *

def readStartOfFrame(br: Bitreader, image: JPGImage):
    print('Reading SOF Marker')
    assert image.numComponents == 0, 'Error - Multiple SOFs detected'

    length = br.readWord()
    precission = br.readByte()

    assert precission == 8, f'Error - Invalid precision: {precission}'

    image.height = br.readWord()
    image.width = br.readWord()

    assert image.height != 0 and image.width != 0, 'Error - Invalid dimensions'

    image.blockHeight = (image.height + 7) // 8
    image.blockWidth = (image.width + 7) // 8
    image.blockHeightReal = image.blockHeight
    image.blockWidthReal = image.blockWidth

    image.numComponents = br.readByte()

    assert image.numComponents != 4, 'Error - CMYK color mode not supported'
    assert image.numComponents == 1 or image.numComponents == 3, \
        f'Error - {image.numComponents} color components given (1 or 3 required)'

    for i in range(image.numComponents):
        componentID = br.readByte()

        if componentID == 0 and i == 0:
            image.zeroBased = True

        if image.zeroBased:
            componentID += 1

        assert componentID != 0 and componentID <= image.numComponents, \
            f'Error - Invalid component ID: {componentID}'
        
        component: ColorComponent = image.colorComponents[componentID - 1]
        assert not component.usedInFrame, f'Error - Duplicate color component ID: {componentID}'

        component.usedInFrame = True
        samplingFactor = br.readByte()
        component.horizontalSamplingFactor = samplingFactor >> 4
        component.verticalSamplingFactor = samplingFactor & 0x0F

        if componentID == 1:
            assert component.horizontalSamplingFactor == 1 and component.horizontalSamplingFactor != 2, \
                'Error - Sampling factors not supported'
            assert component.verticalSamplingFactor == 1 and component.verticalSamplingFactor != 2, \
                'Error - Sampling factors not supported'

            if (component.horizontalSamplingFactor == 2 and image.blockWidth % 2 == 1):
                image.blockWidthReal += 1

            if (component.verticalSamplingFactor == 2 and image.blockHeight % 2 == 1):
                image.blockHeightReal += 1

            image.horizontalSamplingFactor = component.horizontalSamplingFactor
            image.verticalSamplingFactor = component.verticalSamplingFactor
        else:
            assert component.horizontalSamplingFactor == 1 and component.verticalSamplingFactor == 1, \
                'Error - Sampling factors not supported'
            
        component.quantizationTableID = br.readByte()
        assert component.quantizationTableID <= 3, f'Error - Invalid quantization table ID: {component.quantizationTableID}'

    assert length - 8 - (3 * image.numComponents) == 0, 'Error - SOF invalid'


def readQuantizationTable(br: Bitreader, image: JPGImage):
    print('Reading DQT Marker')

    length = br.readWord()
    length -= 2

    while length > 0:
        tableInfo = br.readByte()
        length -= 1
        tableID = tableInfo & 0x0f

        assert tableID <= 3, f'Error - Invalid quantization table ID: {tableID}'

        qTable: QuantizationTable = image.quantizationTables[tableID]
        assert not qTable.set
        qTable.set = True

        table = [0] * len(qTable.table)

        if (tableInfo >> 4) != 0:
            for i in range(64):
                table[zigZagMap[i]] = br.readWord()
            length -= 128
        else:
            for i in range(64):
                table[zigZagMap[i]] = br.readByte()
            length -= 64

        qTable.table = table

def generateCodes(offsets: list, codes: list):
    code = 0
    for i in range(len(offsets)-1):
        for j in range(offsets[i], offsets[i + 1]):
            codes[j] = code
            code += 1
        code <<= 1
    return codes

def readHuffmanTable(br: Bitreader, image: JPGImage):
    print('Reading DHT Marker')
    length = br.readWord()
    length -= 2

    while length > 0:
        tableInfo = br.readByte()
        tableID = tableInfo & 0x0f
        acTable = tableInfo >> 4

        assert tableID <= 3, f'Error - Invalid Huffman table ID: {tableID}'

        hTable: HuffmanTable = image.huffmanACTables[tableID] if acTable else image.huffmanDCTables[tableID]
        assert not hTable.set
        hTable.set = True

        offsets = [0] * len(hTable.offsets)
        symbols = [0] * len(hTable.symbols)
        codes = [0] * len(hTable.codes)

        offsets[0] = 0
        allSymbols = 0
        for i in range(1, 17):
            allSymbols += br.readByte()
            offsets[i] = allSymbols

        assert allSymbols <= 176, f'Error - Too many symbols in Huffman table: {allSymbols}'

        for i in range(allSymbols):
            symbols[i] = br.readByte()

        hTable.offsets = offsets
        hTable.symbols = symbols
        hTable.codes = generateCodes(offsets, codes)

        length -= 17 + allSymbols

def readRestartInterval(br: Bitreader, image: JPGImage):
    print('Reading DRI Marker')

    length = br.readWord()
    image.restartInterval = br.readWord()
    assert length - 4 == 0, 'Error - DRI invalid'

def readAPPN(br: Bitreader, image: JPGImage):
    print('Reading APPN Marker')
    length = br.readWord()

    assert length >= 2, 'Error - APPN invalid'

    for i in range(length-2):
        br.readByte()

def readComment(br: Bitreader, image: JPGImage):
    print('Reading COM Marker')
    length = br.readWord()

    assert length >= 2, 'Error - COM invalid'

    for i in range(length-2):
        br.readByte()

def readFrameHeader(br: Bitreader, image: JPGImage):
    last = br.readByte()
    current = br.readByte()

    assert (last == 0xff) and (current == JPG.SOI), 'Error - SOI invalid'

    last = br.readByte()
    current = br.readByte()

    while image.valid:
        assert last == 0xff, 'Error - Expected a marker'

        if current == JPG.SOF0:
            image.frameType = JPG.SOF0
            readStartOfFrame(br, image)
        elif current == JPG.SOF2:
            image.frameType = JPG.SOF2
            readStartOfFrame(br, image)
        elif current == JPG.DQT:
            readQuantizationTable(br, image)
        elif current == JPG.DHT:
            readHuffmanTable(br, image)
        elif current == JPG.SOS:
            break
        elif current == JPG.DRI:
            readRestartInterval(br, image)
        elif current >= JPG.APP0 and current <= JPG.APP15:
            readAPPN(br, image)
        elif current == JPG.COM:
            readComment(br, image)
        elif (current >= JPG.JPG0 and current <= JPG.JPG13) or \
                current == JPG.DNL or \
                current == JPG.DHP or \
                current == JPG.EXP:
            readComment(br, image)

        elif current == JPG.TEM:
            pass

        elif current == 0xff:
            current = br.readByte()
            continue
        else:
            assert current != JPG.SOI, 'Error - Embedded JPGs not supported'
            assert current != JPG.EOI, 'Error - EOI detected before SOS'
            assert current != JPG.DAC, 'Error - Arithmetic Coding mode not supported'
            assert current < JPG.SOF0 and current > JPG.SOF15, f'Error - SOF marker not supported: {hex(current)}'
            assert current < JPG.RST0 and current > JPG.RST7, 'Error - RSTN detected before SOS'

            assert False, f'Error - Unknown marker: {hex(current)}'

        last = br.readByte()
        current = br.readByte()

def readStartOfScan(br: Bitreader, image: JPGImage):
    print('Reading SOS Marker')

    assert image.numComponents != 0
    length = br.readWord()
    
    for i in range(image.numComponents):
        image.colorComponents[i].usedInScan = False

    image.componentsInScan = br.readByte()
    assert image.componentsInScan != 0

    for i in range (image.componentsInScan):
        componentID = br.readByte()

        if image.zeroBased:
            componentID += 1

        assert componentID != 0 and componentID <= image.numComponents, \
            f'Error - Invalid color component ID: {componentID}'
        
        component: ColorComponent = image.colorComponents[componentID - 1]
        assert component.usedInFrame, f'Error - Invalid color component ID: {componentID}'

        assert not component.usedInScan, f'Error - Duplicate color component ID: {componentID}'

        component.usedInScan = True

        huffmanTableIDs = br.readByte()
        component.huffmanDCTableID = huffmanTableIDs >> 4
        component.huffmanACTableID = huffmanTableIDs & 0x0F

        assert component.huffmanDCTableID <= 3, f'Error - Invalid Huffman DC table ID: {component.huffmanDCTableID}'
        assert component.huffmanACTableID <= 3, f'Error - Invalid Huffman AC table ID: {component.huffmanACTableID}'

    image.startOfSelection = br.readByte()
    image.endOfSelection = br.readByte()
    successiveApproximation = br.readByte()

    image.successiveApproximationHigh = successiveApproximation >> 4
    image.successiveApproximationLow = successiveApproximation & 0x0F

    if image.frameType == JPG.SOF0:
        assert image.startOfSelection == 0 and image.endOfSelection == 63, \
            'Error - Invalid spectral selection'
        
        assert image.successiveApproximationHigh == 0 and image.successiveApproximationLow == 0, \
            'Error - Invalid successive approximation'
    elif image.frameType == JPG.SOF2:
        assert False, 'JPG.SOF2: Not supported'

    for i in range(image.numComponents):
        component: ColorComponent = image.colorComponents[i]

        if component.usedInScan:
            assert image.huffmanDCTables[component.huffmanDCTableID].set, \
                'Error - Color component using uninitialized Huffman DC table'

            assert image.huffmanACTables[component.huffmanACTableID].set, \
                'Error - Color component using uninitialized Huffman AC table'

    assert length - 6 - (2 * image.componentsInScan) == 0, 'Error - SOS invalid'

def printScanInfo(image: JPGImage):
    print("SOS=============\n")
    print(f"Start of Selection: {image.startOfSelection}")
    print(f"End of Selection: {image.endOfSelection}")
    print(f"Successive Approximation High: {image.successiveApproximationHigh}")
    print(f"Successive Approximation Low: {image.successiveApproximationLow}")
    print("Color Components:\n")
    for i in range(image.numComponents):
        if (image.colorComponents[i].usedInScan):
            print(f"Component ID: {(i + 1)}")
            print(f"Huffman DC Table ID: {image.colorComponents[i].huffmanDCTableID}")
            print(f"Huffman AC Table ID: {image.colorComponents[i].huffmanACTableID}")

    print("DHT=============\n")
    print("DC Tables:\n")
    for i in range(4):
        if (image.huffmanDCTables[i].set):
            print(f"Table ID: {i}")
            print("Symbols:\n")
            for j in range(16):
                print(f"{(j + 1)}: ", end='')
                for k in range(image.huffmanDCTables[i].offsets[j], image.huffmanDCTables[i].offsets[j + 1]):
                    print(f"{hex(image.huffmanDCTables[i].symbols[k])} ", end='')
                print("")
 
    print("AC Tables:\n")
    for i in range(4):
        if (image.huffmanACTables[i].set):
            print(f"Table ID: {i}")
            print("Symbols:\n")
            for j in range(16):
                print(f"{(j + 1)}: ", end='')
                for k in range(image.huffmanACTables[i].offsets[j], image.huffmanACTables[i].offsets[j + 1]):
                    print(f"{hex(image.huffmanACTables[i].symbols[k])} ", end='')
                print("")

    print("DRI=============\n")
    print(f"Restart Interval: {image.restartInterval}")

def getNextSymbol(br: Bitreader, hTable: HuffmanTable):
    currentCode = 0

    for i in range(16):
        bit = br.readBit()
        currentCode = (currentCode << 1) | bit
        for j in range(hTable.offsets[i], hTable.offsets[i+1]):
            if currentCode == hTable.codes[j]:
                return hTable.symbols[j]
            
    assert False, 'getNextSymbol: No such symbol'

def decodeBlockComponent(image: JPGImage, br: Bitreader,
                         component: list, previousDC, skips,
                         dcTable: HuffmanTable, acTable: HuffmanTable):
    
    

    assert image.frameType == JPG.SOF0

    length = getNextSymbol(br, dcTable)

    assert length <= 11, 'Error - DC coefficient length greater than 11'
    coeff = br.readBits(length)
    
    if length != 0 and coeff < (1 << (length - 1)):
        coeff -= (1 << length) - 1

    for i in range(64):
        component[i] = 0

    component[0] = coeff + previousDC
    previousDC = component[0]

    i = 1
    while i < 64:
        symbol = getNextSymbol(br, acTable)

        if symbol == 0:
            return previousDC, skips
        
        numZeroes = symbol >> 4
        coeffLength = symbol & 0x0F
        coeff = 0

        assert i + numZeroes < 64, 'Error - Zero run-length exceeded block component'

        i += numZeroes

        assert coeffLength <= 10, 'Error - AC coefficient length greater than 10'

        if coeffLength:

            coeff = br.readBits(coeffLength)

            if coeffLength and coeff < (1 << (coeffLength - 1)):
                coeff -= (1 << coeffLength) - 1

            component[zigZagMap[i]] = coeff

        i += 1

    return previousDC, skips, 

def decodeHuffmanData(br: Bitreader, image: JPGImage):
    previousDCs = [0] * 3
    skips = 0

    luminanceOnly = image.componentsInScan == 1 and image.colorComponents[0].usedInScan
    yStep = 1 if luminanceOnly else image.verticalSamplingFactor
    xStep = 1 if luminanceOnly else image.horizontalSamplingFactor
    restartInterval = int(image.restartInterval * xStep * yStep)

    for y in range(0, image.blockHeight, yStep):
        for x in range(0, image.blockWidth, xStep):
            if restartInterval != 0 and ((y * image.blockWidthReal + x) % restartInterval) == 0:
                previousDCs = [0] * 3
                skips = 0
                br.align()

            for i in range(image.numComponents):
                component: ColorComponent = image.colorComponents[i]
                if component.usedInScan:
                    vMax = 1 if luminanceOnly else component.verticalSamplingFactor
                    hMax = 1 if luminanceOnly else component.horizontalSamplingFactor

                    for v in range(vMax):
                        for h in range(hMax):
                            block = image.blocks[(y + v) * image.blockWidthReal + (x + h)].get(i)
                            previousDCs[i], skips = decodeBlockComponent(
                                    image,
                                    br,
                                    block,
                                    previousDCs[i],
                                    skips,
                                    image.huffmanDCTables[component.huffmanDCTableID],
                                    image.huffmanACTables[component.huffmanACTableID])

                            image.blocks[(y + v) * image.blockWidthReal + (x + h)].set(i, block)

def readScans(br: Bitreader, image: JPGImage):
    readStartOfScan(br, image)

    printScanInfo(image)

    decodeHuffmanData(br, image)

    last = br.readByte()
    current = br.readByte()

    while True:

        assert last == 0xff, 'Error - Expected a marker'

        if current == JPG.EOI:
            break

        assert image.frameType != JPG.SOF2

        if current >= JPG.RST0 and current <= JPG.RST7:
            pass

        elif current == 0xff:
            current = br.readByte()
            continue
        else:
            assert False, f'Error - Invalid marker: {current}'

        last = br.readByte()
        current = br.readByte()

def printFrameInfo(image: JPGImage):
    print("SOF=============")
    print(f"Frame Type: {hex(image.frameType)}")
    print(f"Height: {image.height}")
    print(f"Width: {image.width}")
    print("Color Components:")
    for i in range(image.numComponents):
        if (image.colorComponents[i].usedInFrame):
            print(f"Component ID: {i + 1}")
            print(f"Horizontal Sampling Factor: {image.colorComponents[i].horizontalSamplingFactor}")
            print(f"Vertical Sampling Factor: {image.colorComponents[i].verticalSamplingFactor}")
            print(f"Quantization Table ID: {image.colorComponents[i].quantizationTableID}")

    print("DQT=============")
    for i in range (len(image.quantizationTables)):
        qTable: QuantizationTable = image.quantizationTables[i]
        if (qTable.set):
            print(f"Table ID: {i}")
            print("Table Data:")
            for j, v in enumerate(qTable.table):
                if (j % 8) == 0:
                    print('')
                print(f"{v} ", end='')
            print('')

    if False:
        print("DHT=============")
        for acdc in [image.huffmanDCTables, image.huffmanACTables]:
            for i, hTable in enumerate(acdc):
                if (hTable.set):
                    print(f"Table ID: {i}")
                    _map = {
                        'Offsets': hTable.offsets,
                        'Symbols': hTable.symbols,
                        'Codes': hTable.codes
                    }
                    _to_print = ['Symbols', 'Offsets']
                    for k in _map:
                        if k in _to_print:
                            print(f"{k}:")
                            table = _map[k]

                            for j, v in enumerate(table):
                                if (j % 8) == 0:
                                    print('')
                                print(f"{hex(v)} ", end='')
                            print('')


def dequantizeBlockComponent(qTable: QuantizationTable, component: list):
    for i in range(64):
        component[i] *= qTable.table[i]

def dequantize(image: JPGImage):
    for y in range(0, image.blockHeight, image.verticalSamplingFactor):
        for x in range(0, image.blockWidth, image.horizontalSamplingFactor):
            for i in range(image.numComponents):
                component: ColorComponent = image.colorComponents[i]
                for v in range(component.verticalSamplingFactor):
                    for h in range(component.horizontalSamplingFactor):
                        block = image.blocks[(y + v) * image.blockWidthReal + (x + h)].get(i).copy()

                        dequantizeBlockComponent(image.quantizationTables[component.quantizationTableID],
                                                 block)
                        
                        image.blocks[(y + v) * image.blockWidthReal + (x + h)].set(i, block)
                        
                        

def inverseDCTBlockComponent(component: list):

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

def inverseDCT(image: JPGImage):
     for y in range(0, image.blockHeight, image.verticalSamplingFactor):
        for x in range(0, image.blockWidth, image.horizontalSamplingFactor):
            for i in range(image.numComponents):
                component: ColorComponent = image.colorComponents[i]
                for v in range(component.verticalSamplingFactor):
                    for h in range(component.horizontalSamplingFactor):
                           block = image.blocks[(y + v) * image.blockWidthReal + (x + h)].get(i)
                           inverseDCTBlockComponent(block)
                           image.blocks[(y + v) * image.blockWidthReal + (x + h)].set(i, block)

def YCbCrToRGBBlock(yBlock: Block, cbcrBlock: Block, vSamp, hSamp, v, h):
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

def YCbCrToRGB(image: JPGImage):
    vSamp = image.verticalSamplingFactor
    hSamp = image.horizontalSamplingFactor
    for y in range(0, image.blockHeight, vSamp):
        for x in range(0, image.blockWidth, hSamp):
            cbcrBlock: Block = image.blocks[y * image.blockWidthReal + x]
            for v in range(vSamp-1, -1, -1):
                for h in range(hSamp-1, -1, -1):
                    yBlock: Block = image.blocks[(y + v) * image.blockWidthReal + (x + h)]
                    YCbCrToRGBBlock(yBlock, cbcrBlock, vSamp, hSamp, v, h)



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

    image = JPGImage()

    readFrameHeader(br, image)

    assert image.valid

    printFrameInfo(image)

    image.blocks = declList(Block, int(image.blockHeightReal * image.blockWidthReal))

    readScans(br, image)

    dequantize(image)

    inverseDCT(image)

    YCbCrToRGB(image)

    return image

if __name__ == '__main__':
    import sys

    fpath = sys.argv[1]
    outpath = sys.argv[2]

    image = readJPG(fpath)

    writeBMP(image, outpath)