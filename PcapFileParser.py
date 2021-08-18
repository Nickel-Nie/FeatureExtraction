import json
import logging
from pathlib import Path
from PacketLengthRange import PacketLengthRange
from FileHandler import FileHandler

import hashlib

logger = logging.getLogger('FeatureExractionLog')

class PcapFileParser:

    def __init__(self, filepath: str,
                 filename: str,
                 firstmPakcets:int,
                 firstnBytes:int,
                 packetLengthRange: PacketLengthRange,
                 md5path: Path):
        """
        每个文件一个对象进行处理
        :param filepath: 目录
        :param filename: 文件名
        :param packetLengthRanges: 多个范围
        """
        if filename.split('.')[1] != 'pcap' and filename.split('.')[1] != 'pcapng':
            raise Exception("请传入pcap或者pcapng文件")

        self.filepath = Path(filepath)
        self.filename = filename

        self.inputFile = self.filepath.joinpath(filename).open('rb')
        self.packetLengthRange = packetLengthRange
        self.firstnBytes = firstnBytes
        self.firstmPakcets = firstmPakcets

        # 创建目录
        # self.md5Path = FileHandler.createDirectory(self.filepath, f"{self.packetLengthRange.rangeString}-{self.firstnBytes}-All_MD5")
        # self.featurePath = FileHandler.createDirectory(self.filepath, f"{self.packetLengthRange.rangeString}-{self.firstnBytes}-特征值")
        self.md5path = md5path

    def parseFile(self):
        packetsCount = 0
        availablePacketsCount = 0
        blocksCount = 0
        infoList = []
        # 每个循环处理一个Block
        while True:
            blockTypeBytes = self.inputFile.read(4)
            if len(blockTypeBytes) == 0:
                # print(f"文件读取完毕, 共处理{blocksCount}个块，其中包含{packetsCount}个报文。")
                break

            blocksCount += 1
            blockLengthBytes = self.inputFile.read(4)
            blockType = int.from_bytes(blockTypeBytes, "little", signed=False)
            blockLength = int.from_bytes(blockLengthBytes, "little", signed=False)

            if not self.__isDataBlock(blockType):
                # 不是报文块,直接跳过
                self.inputFile.seek(blockLength - 8, 1)
                continue
            # 处理报文块
            packetsCount += 1
            blockBodyBytes = self.inputFile.read(blockLength - 8 - 4)

            # print(f'No.{packetsCount}: ', end='')
            packetDataBytes = self.__extractPacketsData(blockType, blockBodyBytes)

            #进行长度判断+报文数量判断(前m个范围内的报文)，通过后才进行业务负载的提取
            if availablePacketsCount < self.firstmPakcets and self.__isInRange(packetDataBytes):
                servicePayload = self.__extractServicePayload(packetDataBytes)
                # print(servicePayload)
                md5 = self.__calculateMd5(servicePayload)
                if len(md5) != 0:
                    # 如果长度为0说明负载长度不足n字节
                    availablePacketsCount += 1
                    infoList.append(dict(packetNo=packetsCount,
                                         packetLength=len(packetDataBytes),
                                         firstNbytes=servicePayload[:self.firstnBytes * 2],
                                         md5=md5,
                                         isFeature = 0  # -1表示不是特征，0表示暂未判断，1表示是特征
                                         ))
                else:
                    pass
                    # print(f"负载长度不足{self.firstnBytes}字节")
            elif availablePacketsCount >= self.firstmPakcets:
                # print(f"已获取满足条件的{self.firstmPakcets}个报文，该报文略去")
                pass
            elif not self.__isInRange(packetDataBytes):
                pass
                # print(f"报文长度不在{self.packetLengthRange.rangeString}内")
            else:
                logger.critical("未知错误")

            self.inputFile.seek(4, 1)  # 跳过最后的块长度，进行下一个块的处理

        logger.debug(f"{self.filename}文件处理完成，共包含{blocksCount}个Block,{packetsCount}个packet。其中有{availablePacketsCount}个packet满足条件，并写入文件中")
        # print("="*50)
        self.__saveMd5File(infoList, availablePacketsCount)
        self.inputFile.close()

    def __calculateMd5(self, servicePayload:str) -> str:
        if len(servicePayload) < self.firstnBytes:
            return ""
        # 这里servicePayload已经是16进制字符串的形式，即一个16进制字符占一个字节。
        # N代表的意思是payload中前N个字节，此时是以16进制数表示的，即两个16十六进制数占一个字节
        # 所以这里应该取2N个16进制
        md5hash = hashlib.md5(servicePayload[ : self.firstnBytes * 2].encode())
        md5str = md5hash.hexdigest()
        return md5str

    def __saveMd5File(self, infoList:list, availablePacketsCount:int):
        filename = self.filename.split('.')[0] + '.json'
        outputFile = self.md5path.joinpath(filename).open('w')
        outputFile.write(json.dumps(dict(name = filename.split('.')[0],
                                         availablePacketsCount=availablePacketsCount,
                                         featureCount = 0,
                                         packetsData=infoList)))
        outputFile.close()

    def __saveFeatureFile(self):
        pass

    def __isInRange(self, packetDataBytes: bytes) -> bool:
        packetLength = len(packetDataBytes)
        # 满足一个范围即可
        # for packetLengthRange in self.packetLengthRanges:
        if self.packetLengthRange.minLength <= packetLength <= self.packetLengthRange.maxLength:
            return True

        return False

    def __extractServicePayload(self, frameBytes:bytes) -> str:
        """
        处理报文字节流，获取业务负载字节流，即获取TCP以及UDP，并排除DNS(通过端口号53进行排除)
        返回
        :param frameBytes:
        :return:业务负载，以16进制字符流返回
        """
        MAC_destination = frameBytes[0:6].hex()
        MAC_source = frameBytes[6:12].hex()
        MAC_type = frameBytes[12:14].hex()

        IP_dataOffset = 14
        _TCP = 6
        _UDP = 17

        IP_headerLength = (frameBytes[IP_dataOffset] & 0x0f) * 4
        IP_totalLength = int.from_bytes(frameBytes[IP_dataOffset+2:IP_dataOffset+4], "big", signed=False)
        IP_protocol = frameBytes[IP_dataOffset+9]  #传输层协议：6为TCP，17为UDP，其余均过滤

        # Transport Layer
        TL_dataOffset = IP_dataOffset + IP_headerLength
        TL_sourcePort = frameBytes[TL_dataOffset: TL_dataOffset+2]
        TL_destinationPort = frameBytes[TL_dataOffset+2: TL_dataOffset+4]

        if IP_protocol == _TCP:
            # TCP头部长度
            TL_headerLength = ((frameBytes[TL_dataOffset+12] & 0xf0) >> 4) * 4
            servicePayloadOffset = TL_dataOffset + TL_headerLength
        elif IP_protocol == _UDP:
            # UDP头部长度恒为8，故不计算头部长度
            TL_headerLength = 8
            servicePayloadOffset = TL_dataOffset + 8
        else:
            return ''

        if TL_sourcePort==53 or TL_destinationPort==53:
            return ''

        # 分片不能使用-1，否则负载似乎不正确
        # servicePayload = frameBytes[servicePayloadOffset:-1]

        payloadLength = IP_totalLength - IP_headerLength - TL_headerLength
        servicePayload = frameBytes[servicePayloadOffset: servicePayloadOffset + payloadLength]
        # print(f'payloadLength={payloadLength}, servicePayload=', end='')
        return servicePayload.hex()

    def __extractPacketsData(self, blockType:int, blockBodyBytes:bytes) -> bytes:
        """
        返回数据包对应的字节流，以便后续处理业务负载
        :param blockType:
        :param blockBodyBytes:
        :return:
        """
        if blockType == 0x6:  # 增强分组块 Enhanced Packet Block
            # interfaceIdBytes = blockBodyBytes[0:4]
            # highTimestampBytes = blockBodyBytes[4:8]
            # lowTimestampBytes = blockBodyBytes[8:12]
            # capturedLengthBytes = blockBodyBytes[12:16]
            packetLengthOffset = 16
        elif blockType == 0x3:  # 简单分组块 Simple Packet Block
            packetLengthOffset = 0
        elif blockType == 0x2:  # 分组块 Packet Block(已过时)
            # interfaceIdBytes = blockBodyBytes[0:2]
            # dropsCount = blockBodyBytes[2:4]
            # highTimestampBytes = blockBodyBytes[4:8]
            # lowTimestampBytes = blockBodyBytes[8:12]
            # capturedLengthBytes = blockBodyBytes[12:16]
            packetLengthOffset = 16
        else:
            return b''

        packetDataOffset = packetLengthOffset + 4
        packetLengthBytes = blockBodyBytes[packetLengthOffset: packetDataOffset]
        packetLength = int.from_bytes(packetLengthBytes, "little", signed=False)
        packetDataBytes = blockBodyBytes[packetDataOffset: packetDataOffset + packetLength]
        # print(packetData.hex())  # 目前还只是frame

        return packetDataBytes

    def __isDataBlock(self, blockType: int) -> bool:
        if blockType == 0x6:
            return True
        elif blockType == 0x3:
            return True
        elif blockType == 0x2:
            return True
        return False



# def test():
#     filepath = r"C:\Users\a9241\Desktop\Learning materials\研究生\抓包任务20210611\FacebookCapture\App_Facebook_Post_01"
#     filename = r"App_Facebook_Post_01_PH4.pcapng"
#
#     r1 = PacketLengthRange("[100:200]")
#
#     PcapFileParser(filepath, filename, 20, 32, r1).parseFile()
#     # print(PcapFileParser(filepath, filename, [r1,r2,r3]).isInRange(b"1"*40))
#
#
#
# if __name__ == '__main__':
#     test()