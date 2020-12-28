from scapy.all import *
from Design import *
import multiprocessing 

class Server:
    
    def __init__(self):
        self.manager = multiprocessing.Manager()
        self.ip = "0"
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
        self.lock = multiprocessing.Lock()

    def ip_mode(self):
        print("Is it grading mode?(y/n)")
        c = sys.stdin.read(1)
        if c.__eq__("y\n"):
            self.ip = get_if_addr('eth1')
            ip = get_if_addr("eth2")
            self.broadcastIP = self.calculate_broadcast_ip(ip)
        else:
            self.ip = get_if_addr('eth1')
            self.broadcastIP = self.calculate_broadcast_ip(self.ip)

    def calculate_broadcast_ip(self, serverIP):
        broadcastIP = serverIP.split('.')
        broadcastIP[3] = '255'
        broadcastIP[2] = '255'
        return '.'.join(broadcastIP)

    def talkToClient(self, clientName, connectionSocket):
        msg = self.create_client_start_msg()
        try:
            connectionSocket.send(str.encode(msg))
            oldtime = time.time()
            while not self.ten_seconds_passed(oldtime):
                print(fg.blue + "before" + colors.reset)
                char, clientAddr = connectionSocket.recvfrom(1024)
                print(fg.blue + "after" + colors.reset)
                char = char.decode("utf-8")
                print(fg.green + "received: " + char + colors.reset)
                self.increase_group_score(clientName)
                self.collect_chars(char)
                print(fg.blue + "the score in talk: " + str(self.group1Score.value) + colors.reset)
        except ConnectionResetError:
            print(fg.red + "The client " + clientName + " disconnected" + colors.reset)
            print(fg.blue + "the score in c except: " + str(self.group1Score.value) + colors.reset)
            return
        except:
            print(fg.blue + "the score in except: " + str(self.group1Score.value) + colors.reset)
            return

    def ten_seconds_passed(self, oldtime):
        return time.time() - oldtime >= 10

    def broadcastToClients(self):
        try:
            msg = struct.pack('!IBH', 0xfeedbeef, 0x2, self.tcpPort)
            self.sockUDP.sendto(msg, (self.broadcastIP, self.port))
            print(fg.pink + "sent broadcast" + colors.reset)
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
                print(fg.yellow + "inc before" + colors.reset) 
                #self.lock.acquire()
                self.group1Score.value = self.group1Score.value + 1
                print(fg.pink + "new score: " + str(self.group1Score.value) + colors.reset)
                #self.lock.release()
                print(fg.yellow + "inc after" + colors.reset)    
                return
        for name in self.group2:
            if name == clientName:
                #self.lock.acquire()
                self.group2Score.value = self.group2Score.value + 1
                #self.lock.release()    
                return

    def collect_chars(self, char):
        if len(str(char)) > 1:
            return
        print(fg.purple + "collect before" + colors.reset)    
        #self.lock.acquire()
        if char in self.charDict:
            oldCount = self.charDict[char]
            self.charDict[char] = oldCount + 1
        elif char == '':
             return
        else:
            self.charDict[char] = 1
        #self.lock.release()
        print(fg.purple + "collect after" + colors.reset) 
        print(fg.blue + "the score: " + str(self.group1Score.value) + colors.reset)

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
        print("at the end the score is: " + str(self.group1Score.value))    
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
                print(fg.cyan + "still alive and killing it" + colors.reset)
                t.terminate()
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
            #m, firstClientAddr = self.sockUDP.recvfrom(2048)
            oldtime = time.time()
            timer = None
            while not (self.ten_seconds_passed(oldtime)):
                try:
                    self.broadcastToClients()  # sending broadcast msg every second
                    connectionSocket, addr = self.sockTCP.accept()
                    clientName, clientAddr = connectionSocket.recvfrom(1024)
                    clientName = clientName.decode("utf-8")  # turns bytes to string
                    if self.clientsCounter % 2 == 0:
                        self.group1.append(clientName)
                    else:
                        self.group2.append(clientName)
                    self.clientsCounter = self.clientsCounter + 1
                    self.clientConnection.append(connectionSocket)
                    t = multiprocessing.Process(target=self.talkToClient, args=(clientName, connectionSocket,))
                    self.threadPool.append(t)
                except:
                    x = 0
                    
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
