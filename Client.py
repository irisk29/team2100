from Design import *
from scapy.all import *
import signal
import tty, termios, sys
import curses

class Client:

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(13) # if the server doesn't respond(taking too long) the client will drop the connection and move on
        self.sockUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sockUDP.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sockUDP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.magic_cookie = 0xfeedbeef
        self.msg_type = 0x2
        self.recv_size = 2048
        self.sockUDP.bind(('', 13117)) 
    
    def play(self):
        print("Client started, listening for offer requests...")
        broadcastMsg,serverAddr = self.sockUDP.recvfrom(self.recv_size)
        pck = None
        try:
            pck = struct.unpack('!IBH', broadcastMsg)
        except:
            return
        if pck[0] == self.magic_cookie and pck[1] == self.msg_type:
            print("Received offer from " + serverAddr[0] + ", attempting to connect...")
            try:
                self.sock.connect((serverAddr[0], pck[2]))    # pck[2] = server port over TCP connection
            except:
                print(fg.red + "Warning - could not connect to server via TCP" + colors.reset)   
                self.sockUDP.close()
                return 
            name = "It Burns When IP\n"
            try:
                self.sock.send(str.encode(name))
                welcomeMsg = self.sock.recv(self.recv_size)
                print(welcomeMsg.decode("utf-8"))
            except:
                print(fg.red + "Warning - Could not reach the server!" + colors.reset)
            oldtime = time.time()
            try:
                while not self.ten_seconds_passed(oldtime):     # the client will enter chars for 10 seconds
                    inp = self.stdinWait("You have 10 seconds to type text ", "[no text]", int(10 - (time.time() - oldtime)), "Aw man! You ran out of time!!")
                    if not timeout:
                        self.sock.sendall(str.encode(inp))
                    else:
                        return
            except Exception as err:
                print(err)

    def getchar(self):
        #Returns a single character from standard input
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
            if printInterrupt:
                print(fg.red + "Warning - Keyboard interrupt!" + colors.reset)
            timeout = True # so we won't get input when there is none
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

    def ten_seconds_passed(self,oldtime):
        return time.time() - oldtime >= 10

    def end_connection(self):
        timeout = False 
        try:
            finishMsg = self.sock.recv(self.recv_size)
            print(finishMsg.decode("utf-8"))
            print("Server disconnected, listening for offer requests...")
            self.sock.close()
            self.sockUDP.close()
        except:
            print(fg.red + "Warning - Could not reach the server!" + colors.reset)
            self.sock.close()
            self.sockUDP.close()

    def client_action(self):
        self.play()
        self.end_connection()

if __name__ == "__main__":
    while True:
        c = Client()
        c.client_action()
