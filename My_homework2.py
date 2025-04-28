import socket
import os
import threading
import time

class FileTransfer:
    def __init__(self, host='0.0.0.0', port=65432, save_dir='./received_files'):
        self.host = host
        self.port = port
        self.save_dir = save_dir
        self.running = False
        
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
    
    def start_server(self):
        """启动接收文件的服务端"""
        self.running = True
        server_thread = threading.Thread(target=self._run_server)
        server_thread.daemon = True
        server_thread.start()
        print(f"文件接收服务已启动，监听端口 {self.port}")
    
    def _run_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            while self.running:
                conn, addr = s.accept()
                client_thread = threading.Thread(target=self._handle_client, args=(conn, addr))
                client_thread.start()
    
    def _handle_client(self, conn, addr):
        with conn:
            print(f"已连接: {addr}")
            
            # 接收文件信息
            file_info = conn.recv(1024).decode()
            if '|' not in file_info:
                print("无效的文件信息格式")
                return
                
            filename, filesize = file_info.split('|')
            filesize = int(filesize)
            
            # 确认接收
            conn.sendall(b"READY")
            
            # 接收文件内容
            save_path = os.path.join(self.save_dir, filename)
            with open(save_path, 'wb') as f:
                received = 0
                while received < filesize:
                    data = conn.recv(4096)
                    if not data:
                        break
                    f.write(data)
                    received += len(data)
            print(f"文件接收完成: {filename} ({received}/{filesize} bytes)")
    
    def send_file(self, filename, target_ip):
        """发送文件到目标IP"""
        if not os.path.exists(filename):
            print(f"文件不存在: {filename}")
            return
            
        filesize = os.path.getsize(filename)
        basename = os.path.basename(filename)
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((target_ip, self.port))
                # 发送文件信息
                s.sendall(f"{basename}|{filesize}".encode())
                
                # 等待接收方确认
                response = s.recv(1024)
                if response != b"READY":
                    print("接收方未准备好")
                    return
                
                # 发送文件内容
                with open(filename, 'rb') as f:
                    sent = 0
                    while sent < filesize:
                        data = f.read(4096)
                        s.sendall(data)
                        sent += len(data)
                print(f"文件发送完成: {basename} ({sent}/{filesize} bytes)")
            except ConnectionRefusedError:
                print(f"无法连接到 {target_ip}:{self.port}，请确认对方已启动接收服务")
            except Exception as e:
                print(f"发送文件时出错: {e}")
    
    def stop(self):
        self.running = False

def get_local_ip():
    """获取本地IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def main():
    local_ip = get_local_ip()
    print(f"本机IP地址: {local_ip}")
    
    transfer = FileTransfer()
    transfer.start_server()
    
    try:
        while True:
            print("\n操作选项:")
            print("1. 发送文件")
            print("2. 退出")
            choice = input("请选择操作: ")
            
            if choice == '1':
                filepath = input("输入要发送的文件路径: ").strip('"')
                target_ip = input("输入目标IP地址: ")
                transfer.send_file(filepath, target_ip)
            elif choice == '2':
                break
            else:
                print("无效选择")
    finally:
        transfer.stop()
        print("程序已退出")

if __name__ == "__main__":
    main()