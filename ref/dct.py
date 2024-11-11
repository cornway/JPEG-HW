

import math

from jpg import *

class Dct:

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

    def __init__(self) -> None:
        pass

    def inverseDCTBlockComponent(self, component: list):

        intermediate: list = [0.0] * 64

        for i in range(8):
            g0 = component[0 * 8 + i] * self.s0
            g1 = component[4 * 8 + i] * self.s4
            g2 = component[2 * 8 + i] * self.s2
            g3 = component[6 * 8 + i] * self.s6
            g4 = component[5 * 8 + i] * self.s5
            g5 = component[1 * 8 + i] * self.s1
            g6 = component[7 * 8 + i] * self.s7
            g7 = component[3 * 8 + i] * self.s3

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
            d2 = e2 * self.m1
            d3 = e3
            d4 = e4 * self.m2
            d5 = e5 * self.m3
            d6 = e6 * self.m4
            d7 = e7
            d8 = e8 * self.m5

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
            g0 = intermediate[i * 8 + 0] * self.s0
            g1 = intermediate[i * 8 + 4] * self.s4
            g2 = intermediate[i * 8 + 2] * self.s2
            g3 = intermediate[i * 8 + 6] * self.s6
            g4 = intermediate[i * 8 + 5] * self.s5
            g5 = intermediate[i * 8 + 1] * self.s1
            g6 = intermediate[i * 8 + 7] * self.s7
            g7 = intermediate[i * 8 + 3] * self.s3

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
            d2 = e2 * self.m1
            d3 = e3
            d4 = e4 * self.m2
            d5 = e5 * self.m3
            d6 = e6 * self.m4
            d7 = e7
            d8 = e8 * self.m5

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

    def inverseDCT(self, image: JPGImage):
        vSamp = image.verticalSamplingFactor
        hSamp = image.horizontalSamplingFactor

        if vSamp != 1 or hSamp != 1:
            assert False, 'Not supported'
            self.inverseDCTSample(image)
        else:
            self.inverseDCTNoSample(image)

    def inverseDCTSample(self, image: JPGImage):
        for y in range(0, image.blockHeight, image.verticalSamplingFactor):
            for x in range(0, image.blockWidth, image.horizontalSamplingFactor):
                for i in range(image.numComponents):
                    component: ColorComponent = image.colorComponents[i]
                    for v in range(component.verticalSamplingFactor):
                        for h in range(component.horizontalSamplingFactor):
                            block = image.blocks[(y + v) * image.blockWidthReal + (x + h)][i]
                            self.inverseDCTBlockComponent(block)
                            image.blocks[(y + v) * image.blockWidthReal + (x + h)][i] = block


    def inverseDCTNoSample(self, image: JPGImage):
        for block in image.blocks:
            for i in range(image.numComponents):
                self.inverseDCTBlockComponent(block[i])