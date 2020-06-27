import socket
import pickle


class Network():
    def __init__(self, game_type, options):
        self.server = "192.168.15.81"
        self.port = 9090
        self.addr = (self.server, self.port)
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.options = options

        self.status = self.connect(game_type)

        self.game = None
        self.player_id = None
        if self.status == "CONNECTED":
            self.game = self.send("GET")
            self.player_id = self.game["player_id"]
            print("Connected")

        print("NETWORK STATUS: ",self.status)


    def connect(self, game_type):
        print("Conecting to server...")
        try:
            self.client.connect(self.addr)
        except:
            print("Could not connect to server...")
            return "ERROR"

        self.client.send(str.encode(game_type, encoding="UTF-8"))
        type_status = self.client.recv(1024).decode(encoding="UTF-8")
        if type_status == "RECEIVED":
            if game_type == "CREATE":
                self.client.send(pickle.dumps(self.options))
            elif game_type == "ENTER":
                self.client.send(str.encode(self.options.game_id))
            else:
                return "ERROR"
        else:
            self.connect()

        return self.client.recv(1024).decode(encoding="UTF-8")


    def send(self, data):
        self.client.send(str.encode(data))
        return pickle.loads(self.client.recv(1024*10))


    def send_options(self, data):
        self.client.send(pickle.dumps(data))
