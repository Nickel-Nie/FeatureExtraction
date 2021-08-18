import sys
import getopt
import logging
import os

from pathlib import Path
from FileHandler import FileHandler
from PcapFileParser import PcapFileParser
from PacketLengthRange import PacketLengthRange
from FeatureHandler import FeatureHandler

logging.basicConfig(level=logging.DEBUG,
                    filename=os.path.join(os.path.split(os.path.realpath(__file__))[0], 'FeatureExractionLog.log'),
                    format='%(asctime)s %(filename)s %(levelname)s %(message)s',
                    datefmt='%d %b %Y %H:%M:%S')

logger = logging.getLogger('FeatureExractionLog')

def main(args):
    try:
        opts,args = getopt.getopt(args, "hi:r:m:n:x:")
    except getopt.GetoptError:
        print('ModuleTest.py -i <input filepath> -r <packet length range> -m <lte m packets> -n <first n bytes> -x <x features>' )
        sys.exit()

    inputFilepath = ""
    rangeString = ""
    firstmPackets = 0
    firstnBytes = 0
    featureNumbers = 0

    for opt, arg in opts:
        if opt == '-h':
            print("ModuleTest.py -i <input filepath> -r <packet length range> -m <lte m packets> -n <first n bytes> -x <x features>\n"
                  "input filepath: 待处理目录\n"
                  "packet length range: 用于限定报文长度范围，e.g. [100:200]\n"
                  "lte m packets: 得到前m个报文\n"
                  "first n bytes: 每个报文业务载荷中的前n个字节用于计算特征值\n"
                  "x features: 每个文件获取x个特征值\n")
            sys.exit()
        elif opt == '-i':
            inputFilepath = arg
        elif opt == '-r':
            rangeString = arg
        elif opt == '-m':
            firstmPackets = int(arg)
        elif opt == '-n':
            firstnBytes = int(arg)
        elif opt == '-x':
            featureNumbers = int(arg)

    for iRange in rangeString.split('+'):
        # 报文范围处理
        r1 = PacketLengthRange(iRange)

        # 目录处理
        fileHandler = FileHandler(inputFilepath)
        pcapFiles = fileHandler.getAllPcapFilename()

        # 存放md5值的路径
        md5path = fileHandler.createDirectory(inputFilepath,  f"{r1.rangeString}-{firstnBytes}-All_MD5")
        featurePath = fileHandler.createDirectory(inputFilepath,  f"{r1.rangeString}-{firstnBytes}-All_FEATURE")

        # 目录下的所有pcap和pcapng文件处理
        if len(pcapFiles['pcap']) != 0:
            for pcapFile in pcapFiles['pcap']:
                parser = PcapFileParser(inputFilepath, pcapFile, firstmPackets, firstnBytes, r1, md5path)
                parser.parseFile()
        if len(pcapFiles['pcapng']) != 0:
            for pcapngFile in pcapFiles['pcapng']:
                parser = PcapFileParser(inputFilepath, pcapngFile, firstmPackets, firstnBytes, r1, md5path)
                parser.parseFile()

        # json文件已存盘，现在处理特征值
        featureHandler = FeatureHandler(md5path, featurePath, featureNumbers)
        featureHandler.handle()


if __name__ == '__main__':
    main(sys.argv[1:])
    # content = "485454502f312e3120323030204f4b0d0a436f6e74656e742d547970653a20746578742f6a6176617363726970743b20636861727365743d5554462d380d0a436f6e74656e742d4c656e6774683a20370d0a43616368652d436f6e74726f6c3a206e6f2d63616368650d0a4163636573732d436f6e74726f6c2d416c6c6f772d4f726967696e3a2a0d0a0d0a6528223122293b"
    # md5hash = hashlib.md5(content.encode())
    # md5 = md5hash.hexdigest()
    # print(md5)
    # print(type(md5))
    # print(json.dumps([{1:2,3:4}, {3:4,5:6}]))

