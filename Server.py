from scapy.all import *
from Design import *
import multiprocessing 

class Server:
    
    def __init__(self):
        self.manager = multiprocessing.Manager()
        self.ip = get_if_addr('eth1')
        self.broadcastIP = "0"
        self.ip_mode()
        self.sockUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sockUDP.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sockUDP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sockUDP.bind((self.ip, 0))
        self.sockTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sockTCP.settimeout(1)  # stop looking for clients after 1 seconds so accept won't block the broadcast msg
        self.port = 13117
        self.tcpPort = 2100
        self.sockTCP.bind((self.ip, self.tcpPort))
        self.sockTCP.listen(5) # the max num of clients that can connect to the game
        self.group1 = []
        self.group2 = []
        self.clientsCounter = 0
        self.group1Score = self.manager.Value("g1",0)
        self.group2Score = self.manager.Value("g2",0)
        self.threadPool = []
        self.clientConnection = []
        self.charDict = self.manager.dict()  # bonus
        self.bestTeam = ([], -1)  # bonus
        self.broadcast = '255'
        self.recv_size = 2048
        self.magic_cookie = 0xfeedbeef
        self.msg_type = 0x2
        self.duration_of_game = 10
        
    def ip_mode(self):
        c = input("Is it grading mode? (y/n):")
        if c == "y":
            self.ip = get_if_addr("eth2")
            self.broadcastIP = self.calculate_broadcast_ip(self.ip)
        else:
            self.broadcastIP = self.calculate_broadcast_ip(self.ip)

    def calculate_broadcast_ip(self, serverIP):
        broadcastIP = serverIP.split('.')
        broadcastIP[3] = self.broadcast
        broadcastIP[2] = self.broadcast
        return '.'.join(broadcastIP)

    def talkToClient(self, clientName, connectionSocket):
        msg = self.create_client_start_msg()
        try:
            connectionSocket.send(str.encode(msg))
            oldtime = time.time()
            while not self.ten_seconds_passed(oldtime): # the client has 10 sec to play
                char, clientAddr = connectionSocket.recvfrom(self.recv_size) # receiving the char from client
                char = char.decode("utf-8")
                self.increase_group_score(clientName)
                self.collect_chars(char) # the bonus method
        except ConnectionResetError:
            print(fg.red + "The client " + clientName + " disconnected" + colors.reset)
            return
        except:
            return

    def ten_seconds_passed(self, oldtime):
        return time.time() - oldtime >= self.duration_of_game

    def broadcastToClients(self):
        try:
            msg = struct.pack('!IBH', self.magic_cookie, self.msg_type, self.tcpPort)
            self.sockUDP.sendto(msg, (self.broadcastIP, self.port))
        except:
            print(fg.red + "Couldn't send a broadcast msg" + colors.reset)

    def create_client_start_msg(self):
        msg = "Welcome to Keyboard Spamming Battle Royal.\nGroup 1:\n==\n"
        for cName in self.group1:
            msg = msg + cName + "\n"
        msg = msg + "Group 2:\n==\n"
        for cName in self.group2:
            msg = msg + cName + "\n"
        msg = msg + "\nStart pressing keys on your keyboard as fast as you can!!"
        return msg

    def increase_group_score(self, clientName):
        for name in self.group1:
            if name == clientName:
                self.group1Score.value = self.group1Score.value + 1  
                return
        for name in self.group2:
            if name == clientName:
                self.group2Score.value = self.group2Score.value + 1 
                return

    def collect_chars(self, char): # will collect all the chars from the clients in the current game for the statistic function
        if char in self.charDict:
            oldCount = self.charDict[char]
            self.charDict[char] = oldCount + 1
        elif char == '':
             return
        else:
            self.charDict[char] = 1

    def run_game(self):
        for t in self.threadPool:
            t.start()
        for t in self.threadPool:
            t.join(10)  # wait for the clients to finish the game - 10 seconds
        
        winner = "Group 1"
        group = self.group1
        if self.group2Score.value > self.group1Score.value:
            winner = "Group 2"
            group = self.group2    
        msg = "Game over!\nGroup 1 typed in " + str(self.group1Score.value) + "  characters. Group 2 typed in "
        msg = msg + str(self.group2Score.value) + "  characters.\n" + winner + " wins!\n\nCongratulations to the winners:\n"
        msg = msg + "==\n" + '\n'.join(group)
        for conn in self.clientConnection:
            try:
                conn.send(str.encode(msg))
            except:
                print(fg.red + "Some client disconnected..." + colors.reset)
        return winner

    def check_best_team(self, winner):
        if winner == "Group 1":
            if self.bestTeam[1] < self.group1Score.value:
                self.bestTeam = (self.group1, self.group1Score.value)
        else:
            if self.bestTeam[1] < self.group2Score.value:
                self.bestTeam = (self.group2, self.group2Score.value)

    def clear_data(self):
        for t in self.threadPool:
            if t.is_alive():
                t.terminate() #after the join the process might be still alive - for the new game there should be no process running
        self.group1 = []
        self.group2 = []
        self.clientsCounter = 0
        self.group1Score = self.manager.Value("g1",0)
        self.group2Score = self.manager.Value("g2",0)
        self.threadPool = []
        for conn in self.clientConnection:
            conn.close()
        self.clientConnection = []
        self.charDict = self.manager.dict()

    def show_statistics(self):
        commChar = ""
        max = 0
        for c in self.charDict:
            if self.charDict[c] > max:
                commChar = c
                max = self.charDict[c]
        print(fg.orange + colors.bold + colors.underline + "And here some statistics: " + colors.reset)
        print(colors.bold + "The most commonly typed character is: " + commChar + " and it was typed: "
              + str(max) + " times" + colors.reset,
              end="\n")
        print(colors.bold + "Currently the best team is: " + colors.underline + ','.join(self.bestTeam[0]) + colors.reset)

    def listen_clients(self):
        while True:
            oldtime = time.time()
            timer = None
            while not (self.ten_seconds_passed(oldtime)):
                try:
                    self.broadcastToClients()  # sending broadcast msg every second
                    connectionSocket, addr = self.sockTCP.accept()
                    connection.settimeout(self.duration_of_game) #if the server won't receive group name from the client in the max time(10 sec) the server should drop the connection
                    clientName, clientAddr = connectionSocket.recvfrom(self.recv_size)
                    clientName = clientName.decode("utf-8")  # turns bytes to string
                    if self.clientsCounter % 2 == 0:
                        self.group1.append(clientName)
                    else:
                        self.group2.append(clientName)
                    self.clientsCounter = self.clientsCounter + 1
                    self.clientConnection.append(connectionSocket)
                    t = multiprocessing.Process(target=self.talkToClient, args=(clientName, connectionSocket,))
                    self.threadPool.append(t)
                except Exception as e:
                    print(e)
                    
            print(fg.darkgrey + "10 seconds has passed - the game shall begin!" + colors.reset)  # after 10 seconds the game need to start - no more broadcast msg
            winner = self.run_game()
            self.check_best_team(winner)
            print("Game over, sending out offer requests...")
            self.show_statistics()
            self.clear_data()


if __name__ == '__main__':
    b = Server()
    print('Server started, listening on IP address ' + str(b.ip))
    b.listen_clients()
