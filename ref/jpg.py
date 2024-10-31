
from enum import IntEnum

class JPG(IntEnum):

    # Restart interval Markers
    RST0 = 0xD0
    RST1 = 0xD1
    RST2 = 0xD2
    RST3 = 0xD3
    RST4 = 0xD4
    RST5 = 0xD5
    RST6 = 0xD6
    RST7 = 0xD7

    # Other Markers
    SOI = 0xD8 # Start of Image
    EOI = 0xD9 # End of Image
    SOS = 0xDA # Start of Scan
    DQT = 0xDB # Define Quantization Table(s)
    DNL = 0xDC # Define Number of Lines
    DRI = 0xDD # Define Restart Interval
    DHP = 0xDE # Define Hierarchical Progression
    EXP = 0xDF # Expand Reference Component(s)

    # Define Huffman Table(s)
    DHT = 0xC4

    # JPEG extensions
    JPG = 0xC8

    # Define Arithmetic Coding Conditioning(s)
    DAC = 0xCC


    # Start of Frame markers, non-differential, Huffman coding
    SOF0 = 0xC0 # Baseline DCT
    SOF1 = 0xC1 # Extended sequential DCT
    SOF2 = 0xC2 # Progressive DCT
    SOF3 = 0xC3 # Lossless (sequential)

    # Start of Frame markers, differential, Huffman coding
    SOF5 = 0xC5 # Differential sequential DCT
    SOF6 = 0xC6 # Differential progressive DCT
    SOF7 = 0xC7 # Differential lossless (sequential)

    # Start of Frame markers, non-differential, arithmetic coding
    SOF9 = 0xC9 # Extended sequential DCT
    SOF10 = 0xCA # Progressive DCT
    SOF11 = 0xCB # Lossless (sequential)

    # Start of Frame markers, differential, arithmetic coding
    SOF13 = 0xCD # Differential sequential DCT
    SOF14 = 0xCE # Differential progressive DCT
    SOF15 = 0xCF # Differential lossless (sequential)

    # APPN Markers
    APP0 = 0xE0
    APP1 = 0xE1
    APP2 = 0xE2
    APP3 = 0xE3
    APP4 = 0xE4
    APP5 = 0xE5
    APP6 = 0xE6
    APP7 = 0xE7
    APP8 = 0xE8
    APP9 = 0xE9
    APP10 = 0xEA
    APP11 = 0xEB
    APP12 = 0xEC
    APP13 = 0xED
    APP14 = 0xEE
    APP15 = 0xEF

    # Misc Markers
    JPG0 = 0xF0
    JPG1 = 0xF1
    JPG2 = 0xF2
    JPG3 = 0xF3
    JPG4 = 0xF4
    JPG5 = 0xF5
    JPG6 = 0xF6
    JPG7 = 0xF7
    JPG8 = 0xF8
    JPG9 = 0xF9
    JPG10 = 0xFA
    JPG11 = 0xFB
    JPG12 = 0xFC
    JPG13 = 0xFD
    COM = 0xFE
    TEM = 0x01

def declList(_class, n, arg = None):
    return [(_class() if arg is None else _class(arg)) for _ in range(n)]

class QuantizationTable:
    table: list = declList(int, 64, 0)
    set: bool = False

class HuffmanTable:
    offsets: list = declList(int, 17, 0)
    symbols: list = declList(int, 176, 0)
    codes: list = declList(int, 176, 0)
    set: bool = False

class ColorComponent:
    horizontalSamplingFactor: int = 0
    verticalSamplingFactor: int = 0
    quantizationTableID: int = 0
    huffmanDCTableID: int = 0
    huffmanACTableID: int = 0
    usedInFrame: bool = False
    usedInScan: bool = False

class Block:
    y_r: list = declList(int, 64, 0)
    cb_g: list = declList(int, 64, 0)
    cr_b: list = declList(int, 64, 0)

    def get(self, i):
        assert i in [0, 1, 2]
        if i == 0:
            return self.y_r
        if i == 1:
            return self.cb_g
        if i == 2:
            return self.cr_b
        
    def set(self, i, l: list):
        assert i in [0, 1, 2]
        if i == 0:
            self.y_r = l.copy()
        if i == 1:
            self.cb_g = l.copy()
        if i == 2:
            self.cr_b = l.copy()

class JPGImage:
    quantizationTables: list = declList(QuantizationTable, 4)
    huffmanDCTables: list = declList(HuffmanTable, 4)
    huffmanACTables: list = declList(HuffmanTable, 4)
    colorComponents: list = declList(ColorComponent, 4)

    frameType: int = 0
    height: int = 0
    width: int = 0
    numComponents: int = 0
    zeroBased: bool = False

    componentsInScan: int = 0
    startOfSelection: int = 0
    endOfSelection: int = 0
    successiveApproximationHigh: int = 0
    successiveApproximationLow: int = 0

    restartInterval: int = 0

    blocks: list = []

    valid: bool = True

    blockHeight: int = 0
    blockWidth: int = 0
    blockHeightReal: int = 0
    blockWidthReal: int = 0

    horizontalSamplingFactor: int = 0
    verticalSamplingFactor: int = 0


zigZagMap = [
    0,   1,  8, 16,  9,  2,  3, 10,
    17, 24, 32, 25, 18, 11,  4,  5,
    12, 19, 26, 33, 40, 48, 41, 34,
    27, 20, 13,  6,  7, 14, 21, 28,
    35, 42, 49, 56, 57, 50, 43, 36,
    29, 22, 15, 23, 30, 37, 44, 51,
    58, 59, 52, 45, 38, 31, 39, 46,
    53, 60, 61, 54, 47, 55, 62, 63
]

import math

m0 = 2.0 * math.cos(1.0 / 16.0 * 2.0 * math.pi)
m1 = 2.0 * math.cos(2.0 / 16.0 * 2.0 * math.pi)
m3 = 2.0 * math.cos(2.0 / 16.0 * 2.0 * math.pi)
m5 = 2.0 * math.cos(3.0 / 16.0 * 2.0 * math.pi)
m2 = m0 - m5
m4 = m0 + m5

s0 = math.cos(0.0 / 16.0 * math.pi) / math.sqrt(8)
s1 = math.cos(1.0 / 16.0 * math.pi) / 2.0
s2 = math.cos(2.0 / 16.0 * math.pi) / 2.0
s3 = math.cos(3.0 / 16.0 * math.pi) / 2.0
s4 = math.cos(4.0 / 16.0 * math.pi) / 2.0
s5 = math.cos(5.0 / 16.0 * math.pi) / 2.0
s6 = math.cos(6.0 / 16.0 * math.pi) / 2.0
s7 = math.cos(7.0 / 16.0 * math.pi) / 2.0