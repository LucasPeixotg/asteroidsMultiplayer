import socket
import pickle

class Network():
    def __init__(self, server_ip, port):
        self.server = server_ip
        self.port = port
        self.addr = (self.server, self.port)
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.status = self.connect_to_network()
        self.game = None
        self.player_id = None

    def connect_to_network(self):
        print("Conecting to server...")
        try:
            self.client.connect(self.addr)
        except socket.error:
            print("Could not connect to server...")
            return "ERROR"
        else:
            return "CONNECTED"

    def get_games_list(self, page):
        try:
            self.client.send(str.encode("GET_LIST", encoding="UTF-8"))
            conn_status = self.client.recv(1024).decode(encoding="UTF-8")
            if conn_status == "RECEIVED":
                self.client.send(str.encode(str(page)))
                games_data= {}
                games_data["game_list"] = []
                games_data["page"] = 1
                while True:
                    try:
                        stt = self.client.recv(2048).decode(encoding="UTF-8")
                    except socket.error:
                        print("Could not receive data...")
                        self.client.close()
                        self.status = "ERROR"
                        break
                    else:
                        if stt == "GAME":
                            try:
                                self.client.send(str.encode("SEND", encoding="UTF-8"))
                                game = self.client.recv(2048)
                                game = pickle.loads(game)
                                self.client.send(str.encode("SEND", encoding="UTF-8"))
                            except UnicodeDecodeError:
                                print("Could not decode data")
                                self.status = "ERROR"
                                self.client.close()
                                break
                            except socket.error:
                                print("Could not receive data")
                                self.status = "ERROR"
                                self.client.close()
                                break
                            else:
                                
                                games_data["game_list"].append(game)
                        elif stt == "PAGE":
                            try:
                                self.client.send(str.encode("SEND", encoding="UTF-8"))
                                page = self.client.recv(1024).decode(encoding="UTF-8")
                                self.client.send(str.encode("SEND", encoding="UTF-8"))
                            except UnicodeDecodeError:
                                print("Could not decode data")
                                self.status = "ERROR"
                                self.client.close()
                                break
                            except socket.error:
                                print("Could not receive data")
                                self.status = "ERROR"
                                self.client.close()
                                break
                            else:
                                games_data["page"] = page
                        elif stt == "FINISH":
                            print("Game list got successfully")
                            return games_data
                        else:
                            print("Error while receiving game list...")
                            self.status = "ERROR"
                            break
                return {"game_list": [],}
                            
            else:
                print("Server has detected an invalid data package...")
                self.status = "ERROR"
                return {"game_list": [],}
        except UnicodeDecodeError:
            print("Could not decode data...")
            self.status = "ERROR"
        except socket.error:
            print("Could not receive data...")
            self.client.close()
            self.status = "ERROR"
        return {"game_list": [],}

    def connect_to_game(self, game_type, options):
        try:
            self.client.send(str.encode(game_type, encoding="UTF-8"))
            conn_status = self.client.recv(1024).decode(encoding="UTF-8")
        except UnicodeDecodeError:
            print("Could not decode data...")
            self.client.close()
            self.status == "ERROR"
            return
        except socket.error:
            print("Could not receive data...")
            self.client.close()
            self.status = "ERROR"
            return

        if conn_status == "RECEIVED":
            if game_type == "CREATE":
                try:
                    self.client.send(pickle.dumps(options))
                except UnicodeDecodeError:
                    print("Could not decode data...")
                    self.status = "ERROR"
                except socket.error:
                    print("Could not receive data...")
                    self.status = "ERROR"
            elif game_type == "ENTER":
                try:
                    print("Entering game: ",options["game_id"])
                    self.client.send(str.encode(str(options["game_id"])))
                except UnicodeDecodeError:
                    print("Could not decode data...")
                    self.status = "ERROR"
                except socket.error:
                    print("Could not receive data...")
                    self.status == "ERROR"
            else:
                self.status = "ERROR"
        else:
            print("Connection status: ", type_status)
            print("Trying to connect...")
            self.status == "ERROR"

        if not self.status == "ERROR":
            try:
                self.status = self.client.recv(1024).decode(encoding="UTF-8")
            except UnicodeDecodeError:
                print("Could not decode data...")
                self.status = "ERROR"
            except socket.error:
                print("Could not receive data...")
                self.status = "ERROR"

            if self.status == "CONNECTED":
                try:
                    self.game = self.send("GET")
                    self.player_id = self.game["player_id"]
                except:
                    print("Could not connect")
                    self.status = "ERROR"
                    self.client.close()
                    return

                print("Connected")
        else:
            print("Could not connect")
            self.client.close()
            return


    def send(self, data):
        self.client.send(str.encode(data))
        try:
            received_package = pickle.loads(self.client.recv(1024*10))
        except UnicodeDecodeError:
            print("Could not decode data...")
            self.status = "ERROR"
            return {}
        except socket.error:
            print("Could not receive data...")
            self.status = "ERROR"
            return {}
        else:
            return received_package
