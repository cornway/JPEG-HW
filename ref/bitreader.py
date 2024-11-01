from collections import deque
from jpg import JPG

class Bitreader:
    def __init__(self, fpath) -> None:
        with open(fpath, 'rb') as f:
            bytes = f.read()
            self.bq = deque()
            self.bq.extend(bytes)
            f.close()

            self.nextBit = 0
            self.nextByte = 0

    def hasBits(self):
        return not (not self.bq)
    
    def readByte(self):
        assert self.hasBits()
        b = self.bq.popleft()
        #print(f'Bitreader.readByte: {hex(b)}')
        return b
    
    def peekByte(self):
        assert self.hasBits()
        return self.bq[0]

    def readWord(self):
        return (self.readByte() << 8) | self.readByte()
    
    def readBit(self):
        if (self.nextBit == 0):
            self.nextByte = self.readByte()
            while self.nextByte == 0xff:

                marker = self.peekByte()
                while marker == 0xff:
                    marker = self.readByte()

                if marker == 0x00:
                    self.readByte()
                    break

                assert marker >= JPG.RST0 and marker <= JPG.RST7, f'Error - Invalid marker: {marker}'

                self.readByte()
                self.nextByte = self.readByte()


        bit = (self.nextByte >> (7 - self.nextBit)) & 1
        self.nextBit = (self.nextBit + 1) % 8

        return bit
    
    def readBits(self, n):
        bits = 0
        for _ in range(n):
            bit = self.readBit()
            bits = (bits << 1) | bit
        return bits

    def align(self):
        self.nextBit = 0