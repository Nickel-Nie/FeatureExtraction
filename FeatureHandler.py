import json
import logging

from FileHandler import FileHandler
from pathlib import Path

logger = logging.getLogger('FeatureExractionLog')

class FeatureHandler:
    def __init__(self, md5path, featurePath, x:int):
        if not isinstance(md5path,Path):
            self.md5path = Path(md5path)
        else:
            self.md5path = md5path

        if not isinstance(featurePath, Path):
            self.featurePath = Path(featurePath)
        else:
            self.featurePath = featurePath

        self.jsonFiles = FileHandler.getFilenamesByType(md5path, 'json')
        logger.debug(f"{md5path}目录下的json文件有：{self.jsonFiles}")
        self.jsonList = self.__getDataFromJson()
        self.featureNumbers = x

    def handle(self):
        for i in range(self.featureNumbers):

            for currentJsonData in self.jsonList:
                currentFilename = currentJsonData.get('name')
                currentPacketsDataList = currentJsonData.get('packetsData')

                if currentPacketsDataList is None:
                    # 该文件内没有符合要求的报文，处理下一个文件，
                    continue

                for currentPacketData in currentPacketsDataList:
                    if currentPacketData.get('isFeature') != 0:
                        continue

                    currentMd5 = currentPacketData.get('md5')
                    isFeature = True  # 内部循环开始判断是否为特征

                    for jsonData in self.jsonList:
                        if jsonData.get('name') == currentFilename or jsonData.get('packetsData') is None:
                            # 相同文件，不需要比较，跳过
                            # 或者说不存在报文数据
                            continue

                        for packetData in jsonData.get('packetsData'):
                            if currentMd5 == packetData.get('md5'):
                                # 非特征
                                currentPacketData['isFeature'] = -1
                                currentPacketData['samePacket'] = dict(name=jsonData.get('name'),
                                                                       targetNo=packetData.get('packetNo'))

                                packetData['isFeature'] = -1
                                packetData['samePacket'] = dict(name=currentFilename,
                                                                targetNo = currentPacketData.get('packetNo'))
                                isFeature = False

                                logger.debug(f"{currentFilename}文件中No.{currentPacketData.get('packetNo')}与{jsonData.get('name')}文件中No.{packetData.get('packetNo')}md5值相同")

                        if not isFeature:
                            # 后续文件不需要再判断，此时已经存在相同的md5了
                            break

                    if isFeature:
                        # 所有文件判断下来后都不存在相同的值，说明是特征，则继续下个文件的特征值判断
                        currentPacketData['isFeature'] = 1
                        currentJsonData['featureCount'] += 1
                        break

        # 修改完数据后，存盘
        self.__saveJsonFiles()
        self.__saveTextFiles()

        # 判断是否所有文件都存在特征值
        if not self.__HaveFeature():
            raise Exception("存在特征数量为0的文件，程序退出。")

        # print(f"{self.md5path}目录处理完成")

    def __HaveFeature(self) -> bool:
        haveFeature = True
        for jsonData in self.jsonList:
            if int(jsonData.get("featureCount")) == 0:
                print(f"{jsonData.get('name')}文件中特征数量为0")
                haveFeature = False
        return haveFeature

    def __saveTextFiles(self):
        for jsonData in self.jsonList:
            filename = jsonData.get('name') + '.txt'
            f = self.featurePath.joinpath(filename).open('w')
            f.write(f'FeatureNumbers: {jsonData.get("featureCount")}\n')
            f.write('='*100 + '\n')
            i = 1
            for packetData in jsonData.get('packetsData'):
                if packetData.get('isFeature') == 1:
                    f.write(f'Feature {i}:\n')
                    f.write(f'PacketNo: {packetData.get("packetNo")}\n')
                    f.write(f'FeatureString: {packetData.get("firstNbytes")}\n')
                    f.write('=' * 100 + '\n')
                    i += 1
            f.close()

        logger.info(f"{self.featurePath.name}目录处理完成")

    def __saveJsonFiles(self):
        for jsonData in self.jsonList:
            filename = jsonData.get('name') + '.json'
            f = self.md5path.joinpath(filename).open('w')
            f.write(json.dumps(jsonData))
            f.close()

        logger.info(f"{self.md5path.name}目录处理完成")

    def __getDataFromJson(self):
        dataList = []
        for jsonFile in self.jsonFiles:
            f = self.md5path.joinpath(jsonFile).open('r')
            dataList.append(json.loads(f.read()))
            f.close()
        return dataList

def main():
    md5path = r"C:\Users\a9241\Desktop\Learning materials\研究生\抓包任务20210611\FacebookCapture\App_Facebook_Post_01\[100-200]-32-All_MD5"
    x = 1
    featureHandler = FeatureHandler(md5path, x)
    featureHandler.handle()

if __name__ == '__main__':
    main()