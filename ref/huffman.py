
import numpy as np
from bitreader import *
from jpg import *

class HuffmanTable:
    offsets: np.ndarray = np.zeros(17, dtype=np.uint16)
    symbols: list = np.zeros(176, dtype=np.uint16)
    codes: list = np.zeros(176, dtype=np.uint16)
    set: bool = False

class HuffmanDecoder:
    dcTables: list = [ HuffmanTable() for _ in range(4) ]
    acTables: list = [ HuffmanTable() for _ in range(4) ]

    br: Bitreader

    def __init__(self, br: Bitreader) -> None:
        self.br = br

    def generateCodes(self, offsets: list, codes: list):
        code = 0
        for i in range(len(offsets)-1):
            for j in range(offsets[i], offsets[i + 1]):
                codes[j] = code
                code += 1
            code <<= 1
        return codes

    def readHuffmanTable(self):
        print('Reading DHT Marker')
        length = self.br.readWord()
        length -= 2

        while length > 0:
            tableInfo = self.br.readByte()
            tableID = tableInfo & 0x0f
            acTable = tableInfo >> 4

            assert tableID <= 3, f'Error - Invalid Huffman table ID: {tableID}'

            hTable: HuffmanTable = self.acTables[tableID] if acTable else self.dcTables[tableID]
            assert not hTable.set
            hTable.set = True

            offsets = [0] * len(hTable.offsets)
            symbols = [0] * len(hTable.symbols)
            codes = [0] * len(hTable.codes)

            offsets[0] = 0
            allSymbols = 0
            for i in range(1, 17):
                allSymbols += self.br.readByte()
                offsets[i] = allSymbols

            assert allSymbols <= 176, f'Error - Too many symbols in Huffman table: {allSymbols}'

            for i in range(allSymbols):
                symbols[i] = self.br.readByte()

            hTable.offsets = offsets
            hTable.symbols = symbols
            hTable.codes = self.generateCodes(offsets, codes)

            length -= 17 + allSymbols

    def getNextSymbol(self, hTable: HuffmanTable):
        currentCode = 0

        for i in range(16):
            bit = self.br.readBit()
            currentCode = (currentCode << 1) | bit
            for j in range(hTable.offsets[i], hTable.offsets[i+1]):
                if currentCode == hTable.codes[j]:
                    return hTable.symbols[j]
                
        assert False, 'getNextSymbol: No such symbol'


    def decodeBlockComponent(self, block: np.ndarray, previousDC,
                            dcTableId, acTableId):
    
        dcTable: HuffmanTable = self.dcTables[dcTableId]
        acTable: HuffmanTable = self.acTables[acTableId]

        length = self.getNextSymbol(dcTable)

        assert length <= 11, 'Error - DC coefficient length greater than 11'
        coeff = self.br.readBits(length)
        
        if length != 0 and coeff < (1 << (length - 1)):
            coeff -= (1 << length) - 1

        for i in range(64):
            block[i] = 0

        block[0] = coeff + previousDC
        previousDC = block[0]

        i = 1
        while i < 64:
            symbol = self.getNextSymbol(acTable)

            if symbol == 0:
                return previousDC
            
            numZeroes = symbol >> 4
            coeffLength = symbol & 0x0F
            coeff = 0

            assert i + numZeroes < 64, 'Error - Zero run-length exceeded block component'

            i += numZeroes

            assert coeffLength <= 10, 'Error - AC coefficient length greater than 10'

            if coeffLength:

                coeff = self.br.readBits(coeffLength)

                if coeffLength and coeff < (1 << (coeffLength - 1)):
                    coeff -= (1 << coeffLength) - 1

                block[zigZagMap[i]] = coeff

            i += 1

        return previousDC


    def printScanInfo(self):
        print("DHT=============\n")
        print("DC Tables:\n")
        for i, hf in enumerate(self.dcTables):
            if (hf.set):
                print(f"Table ID: {i}")
                print("Symbols:\n")
                for j in range(16):
                    print(f"{(j + 1)}: ", end='')
                    for k in range(hf.offsets[j], hf.offsets[j + 1]):
                        print(f"{hex(hf.symbols[k])} ", end='')
                    print("")
    
        print("AC Tables:\n")
        for i, hf in enumerate(self.acTables):
            if (hf.set):
                print(f"Table ID: {i}")
                print("Symbols:\n")
                for j in range(16):
                    print(f"{(j + 1)}: ", end='')
                    for k in range(hf.offsets[j], hf.offsets[j + 1]):
                        print(f"{hex(hf.symbols[k])} ", end='')
                    print("")