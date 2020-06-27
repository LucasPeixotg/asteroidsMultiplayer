import socket
from _thread import start_new_thread
from game import Game, encode_game
import pickle
from pygame import time as py_time
from time import time as new_time

games = {}
actual_game_id = 0
actual_player_id = 0

tick_time = 150

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server = "192.168.15.81"
port = 9090

try:
    s.bind((server,port))
except socket.error as e:
    print(e)
    quit()


s.listen()
print("Server started. Waiting for connection...")


def game_thread(game_id):
    print("Game started.")
    clock = py_time.Clock()
    while True:
        try:
            for p in games[game_id].players.values():
                if p.dead:
                    games[game_id].game_speed = .1
                    if new_time() - games[game_id].start_time >= games[game_id].player_dead_time:
                        if p.lifes <= 0:
                            p.game_over = True
                        p.reset()
                        games[game_id].start_time = new_time()
                        games[game_id].game_speed = 1
                elif p.imunity:
                    if new_time() - games[game_id].start_time >= games[game_id].player_imunity_time:
                        p.imunity = False
                if games[game_id].wave_change:
                    if new_time() - games[game_id].start_time >= games[game_id].wave_delay_time:
                        games[game_id].create_rocks()
                        games[game_id].wave_change = False

            clock.tick(tick_time)
            games[game_id].update_game()
            if not games[game_id].players:
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
            if not data == "GET" and not games[game_id].players[player_id].dead:
                if not games[game_id].players[player_id].game_over:
                    games[game_id].players[player_id].movement(data)
                else:
                    games[game_id].players[player_id].movement("STOP_ACCELERATE")
                conn.send(pickle.dumps(encode_game(games[game_id], player_id)))
            elif data == "GET":
                conn.send(pickle.dumps(encode_game(games[game_id], player_id)))

        except socket.error:
            break

    del games[game_id].players[player_id]
    if len(games[game_id].players) <= 0:
        games.pop(game_id)

    print("Connection lost: ",addr)



def listen():
    global actual_game_id, games, actual_player_id
    while True:
        conn, addr = s.accept()
        print("Connected to: ", addr)

        try:
            game_type = conn.recv(1024).decode()
            print("RECEIVED: ", game_type)
            conn.send(str.encode("RECEIVED", encoding="UTF-8"))
        except socket.error as e:
            print("Connection lost: ",addr)
            conn.send(str.encode("ERROR"))
            conn.close()
        except UnicodeDecodeError as e:
            print("DECODE ERROR")
            conn.send(str.encode("ERROR"))
            conn.close()
        else:
            if game_type == "CREATE":
                try:
                    options = pickle.loads(conn.recv(2048))
                    game = Game(options)
                except:
                    conn.send(str.encode("ERROR"))
                    print("Connection lost: ",addr)
                    conn.close()
                else: 
                    games[actual_game_id] = game
                    games[actual_game_id].add_new_player(actual_player_id)
                    conn.send(str.encode("CONNECTED", encoding="UTF-8"))
                    start_new_thread(game_thread, (actual_game_id,))
                    start_new_thread(threaded_client, (conn, addr, actual_player_id, actual_game_id))
                    actual_game_id += 1
                    actual_player_id += 1

            elif game_type == "ENTER":
                try:
                    game_id = int(conn.recv(2048).decode())
                    if games[game_id] and not len(games[game_id].players) >= games[game_id].max_players:
                        games[game_id].add_new_player(actual_player_id)
                        start_new_thread(threaded_client, (conn, addr, actual_player_id, game_id))
                        conn.send(str.encode("CONNECTED"))
                        actual_player_id += 1
                    else:
                        conn.send(str.encode("ERROR"))
                        print("Connection lost: ",addr)
                        conn.close()
                except:
                    conn.send(str.encode("ERROR"))
                    print("Connection lost: ",addr)
                    conn.close
            else:
                conn.send(str.encode("ERROR"))
                print("Connection lost: ",addr)
                conn.close()

listen()