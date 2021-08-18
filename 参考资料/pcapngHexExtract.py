import re
import sys,getopt
import socket

def extractHexLine(blockType,blockLength,file):
    if(blockType == 0x6):
        file.seek(16,1)
        length = file.read(4)
        lenInt = int.from_bytes(length,'little',signed = False)
        rawLine = file.read(lenInt)
        hexLine = rawLine.hex()
        #读完剩下的
        file.seek(blockLength - 8 - 16 - 4 - lenInt,1)
    elif(blockType == 0x3):
        length = file.read(4)
        lenInt = int.from_bytes(length,'little',signed = False)
        rawLine = file.read(lenInt)
        hexLine = rawLine.hex()
        #读完剩下的
        file.seek(blockLength - 8 - 4 - lenInt,1)

    elif(blockType == 0x2):
        file.seek(16,1)
        length = file.read(4)
        lenInt = int.from_bytes(length,'little',signed = False)
        rawLine = file.read(lenInt)
        hexLine = rawLine.hex()
        #读完剩下的
        file.seek(blockLength - 8 - 16 - 4 - lenInt,1)

    return hexLine

def is_dataBlock(blockType):
    if(blockType == 0x6):
        return True
    elif(blockType == 0x3):
        return True
    elif(blockType == 0x2):
        return True
    return False

def main(argv):

    infile = ''
    outfile = ''
    #should be
    #filterStr = filterStr.replace(' ','')
    #is_satisfied("0010ab1c5678ff01",filterStr)

    try:
        opts,args = getopt.getopt(argv,"hi:o:",["input=","output="])
    except getopt.GetoptError:
        print ('ContentExtract.py -f "filterFunction" -e [extract range] -i <inputfile> -o <outputfile>')
        sys.exit()
    for opt,arg in opts:
        if opt == '-h':
            print ('pcapngHexExtract.py -i <inputfile> -o <outputfile>')
            sys.exit()
        elif opt in ("-i","--inputfile"):
            infile = arg
        elif opt in ("-o","--outputfile"):
            outfile = arg
    #infile = "闲时流量1过滤4.pcapng"
    #outfile = "haha.txt"
    print("输入文件："+infile)
    print ("输出文件："+outfile)
    #获取字段位置
    #打开文件
    f = open(infile,"rb")
    w = open(outfile,"w")

    while True:
        #读一个Block的头部
        typeBytes = f.read(4)
        if(len(typeBytes) == 0):
            print('读完了')
            break
        lengthBytes = f.read(4)
        typeInt = int.from_bytes(typeBytes,'little',signed = False)
        lengthInt = int.from_bytes(lengthBytes,'little',signed = False)
        if( is_dataBlock(typeInt) == False):
            #跳过内容,从当前位置开始算
            f.seek(lengthInt-8,1)
            continue
        #提取
        exHexLine = extractHexLine(typeInt,lengthInt,f)
        print (exHexLine)
        #写入
        w.write(exHexLine)
        w.write('\n')
    w.close()
    f.close()
if __name__ == "__main__":
    main(sys.argv[1:])

