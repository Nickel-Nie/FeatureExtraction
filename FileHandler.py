import logging
import os
from pathlib import Path

logger = logging.getLogger('FeatureExractionLog')

class FileHandler:

    def __init__(self, inputPath):
        path = Path(inputPath)
        if not path.is_dir():  # 不是目录，直接失败
            raise Exception("请传入目录，而不是文件")

        self.absolutePath = path.resolve()

    def getAllPcapFilename(self) -> dict:
        dict = {}
        dict['pcapng'] = [ pcapngFile.name for pcapngFile in self.absolutePath.glob('*.pcapng')]
        dict['pcap'] = [ pcapFile.name for pcapFile in self.absolutePath.glob('*.pcap')]
        return dict

    @ classmethod
    def createDirectory(cls, path, directoryName) -> Path:

        if isinstance(path, str):
            path = Path(path)

        outputPath = path.joinpath(directoryName)

        if outputPath.exists():
            logger.info(f"{directoryName}目录已存在")
        else:
            outputPath.mkdir()
            logger.info(f"创建目录：{directoryName}")
        return outputPath

    # def createOutputPath(self, *args):
    #     for arg in args:
    #         tempPath = self.absolutePath.joinpath(arg)
    #         if tempPath.exists():
    #             print(tempPath.name + "目录已存在")
    #             continue
    #
    #         tempPath.mkdir()

    @classmethod
    def getFilenamesByType(cls, path, type) -> list:
        if isinstance(path, str):
            path = Path(path)
        return [file.name for file in path.glob(f'*.{type}')]

    @classmethod
    def getFilenamesByPattern(cls, path, pattern) -> list:
        if isinstance(path, str):
            path = Path(path)
        return [file.name for file in path.glob(pattern)]


# def test():
#     filepath = r"C:\Users\a9241\Desktop\Learning materials\研究生\抓包任务20210611\FacebookCapture\App_Facebook_Post_01"
#     # fileHandler = FileHandler(filepath)
#     # print(fileHandler.getAllPcapFilename())
#     #
#     # fileHandler.createOutputPath('md5', 'feature')
#     # fileHandler.createOutputPath('md5', 'feature')
#
#     # print(FileHandler.getFilenamesByType(filepath, 'pcapng'))
#     # print(FileHandler.getFilenamesByPattern(filepath, '*PH*.pcapng'))
#
# if __name__ == '__main__':
#     test()