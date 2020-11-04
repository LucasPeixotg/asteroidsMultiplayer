import socket
from _thread import start_new_thread
from game import Game, encode_game
import pickle
from pygame import time as py_time
from time import time as new_time
from math import ceil
import os
os.system('cls' if os.name == 'nt' else 'clear')

games = {}
connected_games = [[],]
games_per_page = 6

actual_game_id = 0
actual_player_id = 0

tick_time = 150

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


hostname = socket.gethostname()
server = socket.gethostbyname(hostname)
port = 9090

try:
    s.bind((server,port))
except socket.error as e:
    print(e)
    quit()



s.listen()
print("\n")
print('''\033[93m


   _____            __                      .__    .___         __________________________________   _________________________ 
  /  _  \\   _______/  |_  ___________  ____ |__| __| _/______  /   _____/\\_   _____/\\______   \\   \\ /   /\\_   _____/\\______   \\
 /  /_\\  \\ /  ___/\\   __\\/ __ \\_  __ \\/  _ \\|  |/ __ |/  ___/  \\_____  \\  |    __)_  |       _/\\   Y   /  |    __)_  |       _/
/    |    \\___  \\  |  | \\  ___/|  | \\(  <_> )  / /_/ |\\___ \\   /        \\ |        \\ |    |   \\ \\     /   |        \\ |    |   \\
\\____|__  /____  > |__|  \\___  >__|   \\____/|__\\____ /____  > /_______  //_______  / |____|_  /  \\___/   /_______  / |____|_  /
        \\/     \\/            \\/                     \\/    \\/          \\/         \\/         \\/                   \\/         \\S/ 


\033[0m
''')
print("Server started (press \"ctrl + break\" to stop it). \nHOSTING AT IP: \033[92m"+server+":"+str(port)+"\033[0m\nWaiting for connection...")


def game_thread(game_id):
    global connected_games, games
    print("Game started.")
    clock = py_time.Clock()
    while True:
        try:
            dead_players = 0
            for p in games[game_id].players.values():
                if p.game_over:
                    dead_players += 1
                if p.dead:
                    games[game_id].game_speed = .1
                    if new_time() - p.death_time >= games[game_id].player_dead_time:
                        if p.lifes <= 0:
                            p.game_over = True
                        p.reset()
                        p.imunity_time = new_time()
                        games[game_id].game_speed = 1
                elif p.imunity:
                    if new_time() - p.imunity_time >= games[game_id].player_imunity_time:
                        p.imunity = False
                if games[game_id].wave_change:
                    if new_time() - games[game_id].start_time >= games[game_id].wave_delay_time:
                        games[game_id].create_rocks()
                        games[game_id].wave_change = False
                else:
                    games[game_id].start_time = new_time()

            clock.tick(tick_time)

            if dead_players == len(games[game_id].players):
                games[game_id].game_over = True
 
            games[game_id].update_game()


            if not games[game_id].players:
                new_list = connected_games.copy()
                for page_id in range(len(new_list)):
                    if game_id in connected_games[page_id]:
                        new_list[page_id].pop(new_list[page_id].index(game_id))
                    if not page_id == len(new_list)-1:
                        while True:
                            if len(new_list[page_id]) >= games_per_page:
                                break
                            new_list[page_id].append(new_list[page_id+1][0])
                            new_list[page_id+1].pop(0)
                    elif len(new_list[page_id]) == 0:
                        new_list.pop(page_id)

                connected_games = new_list
                del games[game_id]
                break
        except KeyError:
            break

    print("Game finished: ",game_id)


def threaded_client(conn, addr, player_id, game_id):
    clock = py_time.Clock()
    while True:
        try:
            clock.tick(tick_time)

            data = conn.recv(1024).decode().upper()
            if not data == "GET":
                if not games[game_id].players[player_id].game_over  and not games[game_id].players[player_id].dead:
                    games[game_id].players[player_id].movement(data)
                else:
                    games[game_id].players[player_id].movement("STOP_ACCELERATE")

                conn.send(pickle.dumps(encode_game(games[game_id], player_id)))
            elif data == "GET":
                conn.send(pickle.dumps(encode_game(games[game_id], player_id)))

        except socket.error:
            break

    del games[game_id].players[player_id]

    print("Delete finished...")
    print("Connection lost: ",addr)



def listen():
    global actual_game_id, games, actual_player_id, connected_games
    while True:
        conn, addr = s.accept()
        print("Connected to: ", addr)

        try:
            request_type = conn.recv(1024).decode()
            print("RECEIVED: ", request_type)
        except socket.error as e:
            print("Connection lost: ",addr)
            conn.send(str.encode("ERROR"))
            conn.close()
        except UnicodeDecodeError as e:
            print("ERROR: Could not decode data")
            conn.send(str.encode("ERROR"))
            conn.close()
        else:
            conn.send(str.encode("RECEIVED", encoding="UTF-8"))
            if request_type == "CREATE":
                try:
                    options = pickle.loads(conn.recv(2048))
                    game = Game(options, actual_game_id)
                except:
                    try:
                        conn.send(str.encode("ERROR", encoding="UTF-8"))
                    except:
                        pass
                    print("Connection lost: ",addr)
                    conn.close()
                else: 
                    games[actual_game_id] = game
                    games[actual_game_id].add_new_player(actual_player_id)
                    try:
                        conn.send(str.encode("CONNECTED", encoding="UTF-8"))
                    except socket.error:
                        print("Connection lost: ",addr)
                        conn.close()
                    else:
                        if not connected_games:
                            connected_games.append([])
                        if len(connected_games[-1]) >= games_per_page:
                            connected_games.append([])
                        connected_games[-1].append(actual_game_id)
                        start_new_thread(game_thread, (actual_game_id,))
                        start_new_thread(threaded_client, (conn, addr, actual_player_id, actual_game_id))
                        actual_game_id += 1
                        actual_player_id += 1
            elif request_type == "ENTER":
                try:
                    game_id = int(conn.recv(2048).decode())
                    if games[game_id] and not len(games[game_id].players) >= games[game_id].max_players:
                        games[game_id].add_new_player(actual_player_id)
                        start_new_thread(threaded_client, (conn, addr, actual_player_id, game_id))
                        conn.send(str.encode("CONNECTED"))
                        actual_player_id += 1
                    else:
                        try:
                            conn.send(str.encode("ERROR", encoding="UTF-8"))
                        except:
                            pass
                        print("Connection lost: ",addr)
                        conn.close()
                except:
                    conn.send(str.encode("ERROR"))
                    print("Connection lost: ",addr)
                    conn.close
            elif request_type == "GET_LIST":
                try:
                    page = int(conn.recv(1024).decode(encoding="UTF-8")) - 1
                    print("PAGE: ",page)
                except socket.error:
                    print("Connection lost: ",addr)
                    conn.close()
                except UnicodeDecodeError:
                    print("ERROR: Could not decode data")
                    conn.close()
                else:
                    try:
                        if page >= len(connected_games):
                            page = 0
                        elif page < 0:
                            page = len(connected_games)-1
                        for game_id in connected_games[page]:
                            try:
                                games[game_id]
                            except KeyError:
                                continue
                            try:
                                conn.send(str.encode("GAME", encoding="UTF-8"))
                                conn.recv(1024)
                                conn.send(pickle.dumps({
                                    "id": game_id,
                                    "difficulty": games[game_id].difficulty,
                                    "players_playing": len(games[game_id].players),
                                    "max_players": games[game_id].max_players,
                                    "wave": games[game_id].wave,
                                }))
                                conn.recv(1024)
                            except:
                                try:
                                    conn.send(str.encode("ERROR", encoding="UTF-8"))
                                except:
                                    pass
                                print("Connection lost: ",addr)
                                conn.close()
                    except:
                        try:
                            conn.send(str.encode("ERROR", encoding="UTF-8"))
                        except:
                            pass
                        print("Connection lost: ",addr)
                        conn.close()
                    try:
                        conn.send(str.encode("PAGE", encoding="UTF-8"))
                        conn.recv(1024)
                        conn.send(str.encode(str(page+1), encoding="UTF-8"))
                        conn.recv(1024)
                        conn.send(str.encode("FINISH", encoding="UTF-8"))
                    except:
                        try:
                            conn.send(str.encode("ERROR", encoding="UTF-8"))
                        except:
                            pass
                        print("Connection lost: ",addr)
                        conn.close()
            else:
                try:
                    conn.send(str.encode("ERROR", encoding="UTF-8"))
                except:
                    pass
                print("Connection lost: ",addr)
                conn.close()


listen()