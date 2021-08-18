class PacketLengthRange:
    __MTU = 1514
    def __init__(self, rangeString:str):
        """
        :param rangeString: [minLength, maxLength] or \
                            [minlength: maxLength] or \
                            [minlength-maxLength]
        """
        self.minLength = 0
        self.maxLength = 0
        self.rangeString = rangeString.replace(',','-').replace(':','-')

        rangeList = self.rangeString.replace('[', '')\
                                    .replace(']', '')\
                                    .split('-')

        if len(rangeList[0]) != 0 and rangeList[0].isdigit():
            self.minLength = int(rangeList[0])
        else:
            self.minLength = 0

        if len(rangeList[1]) != 0 and rangeList[1].isdigit():
            self.maxLength = int(rangeList[1])
        else:
            self.maxLength = self.__MTU

    def isInRange(self, length:int):
        return self.minLength <= length <= self.maxLength





