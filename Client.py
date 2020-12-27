from Design import *
from scapy.all import *
import keyboard
import signal

class Client:

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sockUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sockUDP.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sockUDP.bind(('localhost', 13117))
        #self.ip = "192.168.1.175" - no need for that: the client can know the address of the server from the udp broadcast request

    def play(self):
        print("Client started, listening for offer requests...")
        #self.sockUDP.sendto(str.encode("a"),(get_if_addr('eth1'),13117))
        broadcastMsg,serverAddr = self.sockUDP.recvfrom(4096)
        pck = None
        try:
            pck = struct.unpack('!IBH', broadcastMsg)
        except:
            print(fg.red + "Wrong message format!" + colors.reset)
            return
        if pck[0] == 0xfeedbeef and pck[1] == 0x2:
            print("Received offer from " + serverAddr[0] + ", attempting to connect...")
            print(str(pck[2]))
            print(serverAddr)
            try:
                self.sock.connect(('172.1.0.100', pck[2]))    # pck[2] = server port over TCP connection
            except:
                print(fg.red + "Warning - could not connect to server via TCP" + colors.reset)   
                self.sockUDP.close()
                return 
            #name = input("Please enter your group name:")
            #name = name + '\n'
            name = "It Burns When IP\n"
            try:
                self.sock.send(str.encode(name))
                welcomeMsg = self.sock.recv(2048)
                print(welcomeMsg.decode("utf-8"))
            except:
                print(fg.red + "Warning - Could not reach the server!" + colors.reset)
            oldtime = time.time()
            try:
                #keyboard.add_hotkey("a", lambda: self.sock.sendall(str.encode(key.char)))
                #listener = keyboard.on_press(self.on_press)
                #listener.start()  # start to listen on a separate thread
                #listener.join()
                #keyboardListener = threading.Thread(target=self.on_press,args=(oldtime,))
                #keyboardListener.start()
                #keyboardListener.join(10.0)
                while not self.ten_seconds_passed(oldtime):     # the client will enter chars for 10 seconds
                    inp = self.stdinWait("You have 5 seconds to type text and press <Enter>... ", "[no text]", int(10 - (time.time() - oldtime)), "Aw man! You ran out of time!!")
                    if not timeout:
                        #print( "You entered " +  inp)
                        self.sock.sendall(str.encode(inp))
                    else:
                        return
                    
                #keyboard.unhook_all()
            except Exception as err:
                print(err)

  # def on_press(self,key):
     #   try:
      #      k = key.char  # single-char keys
       #     self.sock.sendall(str.encode(k))
       # except:
        #    return False
    def getchar(self):
        #Returns a single character from standard input
        import tty, termios, sys
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    def stdinWait(self,text, default, time, timeoutDisplay = None, **kwargs):
        signal.signal(signal.SIGALRM, self.interrupt)
        signal.alarm(time) # sets timeout
        global timeout
        try:
            inp = self.getchar()
            signal.alarm(0)
            timeout = False
        except (KeyboardInterrupt):
            printInterrupt = kwargs.get("printInterrupt", True)
            #if printInterrupt:
            #    print(fg.red + "Warning - Keyboard interrupt!" + colors.reset)
            timeout = True # Do this so you don't mistakenly get input when there is none
            inp = default
        except:
            timeout = True
            if not timeoutDisplay is None:
                print(fg.red + "Can't enter any more chars - the game is OVER!" + colors.reset)
            signal.alarm(0)
            inp = default
        return inp

    def interrupt(self, signum, frame):
        raise Exception("")

    def on_press(self,oldtime):
        try:
            k = sys.stdin.read(1)  # single-char keys
            self.sock.sendall(str.encode(k))
        except Exception as e:
           print(e)

    def ten_seconds_passed(self,oldtime):
        return time.time() - oldtime >= 10

    def end_connection(self):
        try:
            finishMsg = self.sock.recv(1024)
            print(finishMsg.decode("utf-8"))
            print("Server disconnected, listening for offer requests...")
            self.sock.close()
            self.sockUDP.close()
        except:
            print(fg.red + "Warning - Could not reach the server!" + colors.reset)

    def client_action(self):
        self.play()
        self.end_connection()

if __name__ == "__main__":
    while True:
        c = Client()
        c.client_action()
