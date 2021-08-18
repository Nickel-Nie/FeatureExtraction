import re
import sys,getopt
import socket
import os
from pathlib import Path

filterStr = ''
bytesSeq = ''
infile = ''
outfile = ''
extractStr = ''

class content_range:
    start = 0
    end = 0
    len = 0
    def __init__(self,data):
        data = data.replace('[','')
        data = data.replace(']','')
        data = data.replace(',',':')
        mydata = data.split(':')
        self.start = 0
        self.end = 0
        if len(mydata) <= 1 :
            if mydata[0].isdigit() :
                self.start = self.end = int(mydata[0])
            else:
                self.start = self.end = 0
        else :
            if mydata[0].isdigit() :
                self.start = int(mydata[0])
            else:
                self.start = 0
            if mydata[1].isdigit():
                self.end = int(mydata[1])
            else :
                self.end = -1
        if(self.end != -1):
            self.len = self.end - self.start + 1
        else:
            self.len = 0
    def extract(self,line):
        if(self.start >= len(line)):
            return ('')
        
        if(self.end != -1):
            return (line[self.start:self.end + 1])
        else:
            self.len = len(line)-self.start
            return (line[self.start:])
#提取范围参数中的多个范围，范围之间用+号间隔，返回范围列表
def getRangeArray(rangStr):
    contentRanges = []
    ranges=rangStr.split('+')

    for rangeTmp in ranges:
        contentRanges.append(content_range(rangeTmp))
    return contentRanges

def isCheck(line,term):
    global bytesSeq
    #term是逻辑判断式,左操作数是范围，右操作数是目标
    tempList = re.split('>=|==|<=|>|<|!=',term)
    if(len(tempList) != 2):
        return False
    #取左操作数，并从line取得子串,按字节序转成数值
    leftRange = content_range(tempList[0])
    leftStr = leftRange.extract(line)
    if(leftStr == ''):
        return False
    left = int(leftStr,16)
    if(bytesSeq != 'B'):
        if(leftRange.len == 4):
            left = socket.htons(left)
        elif(leftRange.len > 4):
            left = socket.htonl(left)

    #取右操作数，转成数值
    right = int(tempList[1],16)

    if(term.find('==') != -1):
        #全字匹配
        if (leftStr == tempList[1]):
            return True
        else:
            return False
    elif(term.find('>=') != -1):
        #判断大小
        if(left >= right):
            return True
        else:
            return False
    elif(term.find('<=') != -1):
        #判断大小
        if(left <= right):
            return True
        else:
            return False
    elif(term.find('<') != -1):
        #判断大小
        if(left < right):
            return True
        else:
            return False
    elif(term.find('>') != -1):
        #判断大小
        if(left > right):
            return True
        else:
            return False
    elif(term.find('!=') != -1):
        #全字匹配
        if (leftStr == tempList[1]):
            return False
        else:
            return True


def is_satisfied(line,fStr):
    #目标是将当前表达式分解为多个式，分别记录下逻辑符号和每个项
    #逐个计算每个项的结果，如果该项还包含子项，递归，否则计算出结果，记录到结果列表里
    #按逻辑顺序计算总结果，返回
    fStr = fStr.replace(' ','')
    if(fStr =='all'):
        return True
    logicSymbs = []
    Results = []
    terms = []
    tempTerms = []
    tempTerms2 = []
    #按逻辑符号分项，每个括号算一项，递归调用
    tempTerms = re.split('([()]|and|or)',fStr)
    flag = 0;
    #重整理要件序列
    for term in tempTerms :
        if(len(term) == 0):
            continue
        else:
            tempTerms2.append(term)

    brace = 0
    #根据要件重整多项式
    tempTerm = ''
    for term in tempTerms2:
        if(brace == 0):
            #没有括号时，按逻辑运算符号划分多项
            if(term == "and" or term == "or"):
                logicSymbs.append(term)
                
            elif(term == '('):
                brace = 1
                #第一个左括号不要
            elif(term == ')'):
                #比较奇怪，多出的有括号不要
                pass
            else:
                terms.append(term)
        else:
            #有括号，组装括号
            if(term == '('):
                brace = brace + 1
                tempTerm = tempTerm+term
            elif(term == ')'):
                brace = brace - 1
                if(brace == 0):
                    #最后一个右括号不要,tempTerm组装完毕
                    terms.append(tempTerm)
                else:
                    tempTerm = tempTerm+term
            else:
                tempTerm = tempTerm+term
    #开始计算，如果不止一项，则递归，即项中包含逻辑运算符
    logicIndex = 0
    tempResult = True
    for term in terms:
        if(term.find('and') != -1 or term.find('or') != -1):
            result = is_satisfied(line,term)
        else:
            result = isCheck(line,term)
        tempResult = tempResult & result
        if(logicIndex >= len(logicSymbs)):
            #最后一项了，算总结果
            Results.append(tempResult)
            break
        if(logicSymbs[logicIndex] == 'or'):
            Results.append(tempResult)
            tempResult = True
        else:
            pass
        logicIndex = logicIndex + 1
    #算总结果，Results中全部是或的结果，遍历只要有一个真就返回真
    final = False
    for result in Results:
        final = final | result
    return (final)
def dealFile(inputfile,outputfile):
    print('reading file:'+inputfile)
    print('writing file:'+outputfile)
    f = open(inputfile,"rt")
    w = open(outputfile,"wt")
    lines = f.readlines()
    count = 0
    for line in lines:
        #过滤
        count = count + 1
        line = line.replace('\n','')
        if( is_satisfied(line,filterStr) == False):
            continue
        lineNo='No.'+str(count)+'\n'
        w.write(lineNo)
        #提取
        if(extractStr == 'all'):
            w.write(line)
        else:
            for rangeTmp in contRanges:
                exLine = rangeTmp.extract(line)
                #写入
                if(exLine != ''):
                    w.write(exLine)
                    w.write('\t')
        w.write('\n')
    w.close()
    f.close()
    return
def main(argv):
    global filterStr
    global bytesSeq
    global infile
    global outfile
    global extractStr
    global contRanges

    extractStr = ''
    infile = ''
    outfile = ''
    #filterStr = '[2:3]==10 || [8:11]<2b  &&([:3]>1 || [12:]>=ff01 )'
    #filterStr = filterStr.replace(' ','')
    #is_satisfied("0010ab1c5678ff01",filterStr)

    try:
        opts,args = getopt.getopt(argv,"hf:e:i:o:b:",["filter=","extract=","input=","output=","byteseq="])
    except getopt.GetoptError:
        print ('ContentExtract.py -f "filterFunction" -e [extract range] -i <inputfile> -o <outputfile> -b <B or L>')
        sys.exit()
    for opt,arg in opts:
        if opt == '-h':
            print ('ContentExtract.py -f "filterFunction" -e [extract ranges] -i <inputfile> -o <outputfileAppend> -b <B or L>')
            print ('filterFunction: ex. [:1]==01and[2:5]>=4 ,all 表示不过滤，参数中的数值都是16进制,and，or不要有空格')
            print ('extact ranges: ex. [4:7]+[10:],可以用+同时提取多个字段')
            print ('bytes seq: ex. B,样本中的数值是按大端B，或小端L顺序保存')

            sys.exit()
        elif opt in ("-f","--filter"):
            filterStr = arg
        elif opt in ("-e","--extract"):
            extractStr = arg
        elif opt in ("-i","--inputfile"):
            infile = arg
        elif opt in ("-o","--outputfile"):
            outfile = arg
        elif opt in ("-b","--byteseq"):
            bytesSeq = arg
    print("输入文件："+infile)
    print ('过滤器：'+filterStr)
    if (extractStr != 'all'):
        contRanges = getRangeArray(extractStr)
    print ("取出字段："+extractStr)
    print ("输出文件："+outfile)
    print ("数字字节序"+bytesSeq)
    #获取字段位置
    #打开文件
    #将infile转成绝对路径
    #infile = Path(infile).parent.joinpath()
    #检查infile是文件还是目录
    if (os.path.isdir(infile)):
        #生成目标目录
        OutPath = infile+outfile
        if(os.path.isdir(OutPath) == False):
            os.makedirs(OutPath)
        #逐个读出目录下文件
        files=os.listdir(infile)
        for tmpFile in files:    
            if (Path(infile).joinpath(tmpFile).is_file() == True):
                #生成目标文件名
                tmpOutFileName = Path(tmpFile).stem+outfile+Path(tmpFile).suffix
                tmpOutFile = Path(OutPath).joinpath(tmpOutFileName)
                dealFile(str(Path(infile).joinpath(tmpFile)),str(tmpOutFile))
    else:
        #单个文件的方法
        tmpOutFile = Path(infile).parent.joinpath(Path(infile).stem+outfile+Path(infile).suffix)
        outfile=Path(tmpOutFile).name
        dealFile(infile,outfile)
    print('done')
if __name__ == "__main__":
    main(sys.argv[1:])
