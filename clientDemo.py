from scapy.all import *

def main():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('', 13117))

    # Receive and print data
    data, serverAdrr = udp_socket.recvfrom(512)
    print(data)
    print(serverAdrr)

if __name__ == '__main__':
    for i in range(20):
        main()    