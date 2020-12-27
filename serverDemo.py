from scapy.all import *

def main():
    searcher_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    searcher_socket.bind(('172.1.0.100', 0)) # 192.168.1.11 is my computer ip address
    searcher_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    searcher_socket.sendto(str.encode("Hey"), ("172.1.255.255", 13117))
    print("yo")

if __name__ == '__main__':
    main()