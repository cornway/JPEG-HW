import numpy as np
from jpg import *
from bitreader import *

class QuantizationTable:
    table: np.ndarray
    set: bool = False

class Quantization:

    br: Bitreader
    quantizationTables: list = declList(QuantizationTable, 4)

    def __init__(self, br: Bitreader) -> None:
        self.br = br

    def readQuantizationTable(self):
        print('Reading DQT Marker')

        length = self.br.readWord()
        length -= 2

        while length > 0:
            tableInfo = self.br.readByte()
            length -= 1
            tableID = tableInfo & 0x0f

            assert tableID <= 3, f'Error - Invalid quantization table ID: {tableID}'

            qTable: QuantizationTable = self.quantizationTables[tableID]
            assert not qTable.set
            qTable.set = True

            qTable.table = np.zeros(64)

            if (tableInfo >> 4) != 0:
                for i in range(64):
                    qTable.table[zigZagMap[i]] = self.br.readWord()
                length -= 128
            else:
                for i in range(64):
                    qTable.table[zigZagMap[i]] = self.br.readByte()
                length -= 64

    def dequantizeBlockComponent(self, qTable: QuantizationTable, block: list):
        for i in range(64):
            block[i] *= qTable.table[i]

    def dequantize(self, image: JPGImage):
        if image.verticalSamplingFactor != 1 or image.horizontalSamplingFactor != 1:
            assert False, 'Not Suported'
            self.dequantizeSample(image)
        else:
            self.dequantizeNoSample(image)

    def dequantizeSample(self, image: JPGImage):
        for y in range(0, image.blockHeight, image.verticalSamplingFactor):
            for x in range(0, image.blockWidth, image.horizontalSamplingFactor):
                for i in range(image.numComponents):
                    component: ColorComponent = image.colorComponents[i]
                    for v in range(component.verticalSamplingFactor):
                        for h in range(component.horizontalSamplingFactor):
                            block = image.blocks[(y + v) * image.blockWidthReal + (x + h)][i].copy()

                            self.dequantizeBlockComponent(image.quantizationTables[component.quantizationTableID],
                                                    block)
                            
                            image.blocks[(y + v) * image.blockWidthReal + (x + h)][i] = block

    def dequantizeNoSample(self, image: JPGImage):
        for block in image.blocks:
            for i in range(image.numComponents):
                component: ColorComponent = image.colorComponents[i]
                self.dequantizeBlockComponent(self.quantizationTables[component.quantizationTableID],
                                                    block[i])
                
    def printInfo(self):
        print("DQT=============")
        for i in range (len(self.quantizationTables)):
            qTable: QuantizationTable = self.quantizationTables[i]
            if (qTable.set):
                print(f"Table ID: {i}")
                print("Table Data:")
                for j, v in enumerate(qTable.table):
                    if (j % 8) == 0:
                        print('')
                    print(f"{v} ", end='')
                print('')