from network import Network
from math import sin, cos, radians, pi, ceil
import pygame
from game import Game, encode_game, game_thread
from time import time as new_time
from _thread import start_new_thread

pygame.font.init()

width = 1000
height = 700
win = pygame.display.set_mode((width, height))
pygame.display.set_caption("Asteroids")

wave_text_x_vel = 2.5
draw_colision_circles = False

rock_color = (255, 167, 25)
heart_radius = 11

wave_font = pygame.font.Font("assets/fonts/press_start_2p.ttf", 50)



all_images = {
    "single_player_image": pygame.image.load("./assets/images/singleplayer.png"),
    "two_players_image": pygame.image.load("./assets/images/two_players.png"),
    "four_players_image": pygame.image.load("./assets/images/four_players.png"),
}

def encode_options(options):
    return {
        "difficulty": options.difficulty,
        "type": options.type,
        "game_id": options.game_id,
        "max_players": options.max_players,
    }

class Options:
    def __init__(self, game_type="SINGLEPLAYER", difficulty="NORMAL", max_players=1):
        self.difficulty = difficulty
        self.type = game_type
        self.game_id = 0
        self.max_players = max_players

    def change_type(self, *args):
        new_type = args[0][0]
        if new_type == "SINGLEPLAYER":
            self.type = new_type
            self.max_players = 1
        elif new_type == "MULTIPLAYER":
            self.type = new_type
            self.max_players = 2

        new_game((self,))

    def change_max_players(self, *args):
        if self.max_players == 2:
            self.max_players = 4
        elif self.max_players == 4:
            self.max_players = 2

        new_game((self,))
    
    def change_difficulty(self, *args):
        new_difficulty = args[0][0]
        if new_difficulty == "EASY" or new_difficulty == "NORMAL":
            self.difficulty = new_difficulty
        elif new_difficulty == "HARD" or new_difficulty == "INSANE":
            self.difficulty = new_difficulty
        new_game((self,))

default_options = Options()


class Button:
    def __init__(self, x, y, width, height, font_size, text, border, color, hover_color, func=None, *args):
        self.x = ceil(x)
        self.y = ceil(y)
        self.width = ceil(width)
        self.height = ceil(height)
        self.font_size = font_size
        self.text = text
        self.border = border
        self.color = color
        self.hover_color = hover_color
        self.mouse_up = False
        self.clicked = func
        self.args = args

    def check_mouse_up(self, x, y):
        if self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height:
            self.mouse_up = True
        else:
            self.mouse_up = False


class Text:
    def __init__(self, x, y, font_size, font, text, color):

        font_pygame = pygame.font.Font("assets/fonts/"+font+".ttf", font_size)
        text_pygame = font_pygame.render(text, True, color)
        self.text = text_pygame

        self.x = ceil(x - self.text.get_width()/2)
        self.y = ceil(y - self.text.get_height()/2)


class Image:
    def __init__(self, x, y, image_index):
        self.x = ceil(x)
        self.y = ceil(y)
        self.index = image_index


def get_player_lines(player):
    cosine = cos(radians(player["angle"]))
    sine = sin(radians(player["angle"]))
    return (
        (int(player["x"] + 4 / 3 * player["radius"] * cosine),
         int(player["y"] - 4 / 3 * player["radius"] * sine)),
        (int(player["x"] - player["radius"] * (2 / 3 * cosine + sine)),
         int(player["y"] + player["radius"] * (2 / 3 * sine - cosine))),
        (int(player["x"] - player["radius"] * (2 / 3 * cosine - sine)),
         int(player["y"] + player["radius"] * (2 / 3 * sine + cosine))),
        (int(player["x"] + 4 / 3 * player["radius"] * cosine),
         int(player["y"] - 4 / 3 * player["radius"] * sine)),
    )


def get_rock_lines(rock):
    lines = []

    for j in range(rock["vert"]):
        lines.append((
            round(rock["x"] + rock["radius"] * rock["offs"][j] *
                  cos(rock["angle"] + j * pi * 2 / rock["vert"])),
            round(rock["y"] + rock["radius"] * rock["offs"][j] *
                  sin(rock["angle"] + j * pi * 2 / rock["vert"]))
        ))
    return lines


def draw_heart(win, radius, main_color, secondary_color, x, y):

    first_circle = (
        ceil(x - radius/2),
        ceil(y)
    )
    second_circle = (
        ceil(x + radius/2),
        ceil(y)
    )

    pygame.draw.circle(win, main_color, first_circle, ceil(radius/2))
    pygame.draw.circle(win, main_color, second_circle, ceil(radius/2))
    pygame.draw.circle(win, secondary_color, first_circle, ceil(radius/2), 1)
    pygame.draw.circle(win, secondary_color, second_circle, ceil(radius/2), 1)

    pygame.draw.polygon(win, main_color, [
        (
            round(x - radius),
            round(y )
        ), (
            round(x + radius),
            round(y)
        ), (
            round(x),
            round(y + radius)
        ), (
            round(x - radius),
            round(y)
        )])


def redraw_window(win, game, wave_text_x):
    global wave_font
    win.fill((26, 28, 31))

    for rock in game["rocks"]:
        pygame.draw.polygon(win, rock_color, get_rock_lines(rock), 1)

        if draw_colision_circles:
            pygame.draw.circle(win, (255, 0, 0), (round(
                rock["x"]), round(rock["y"])), round(rock["radius"]), 1)

    for player in game["players"]:
        if not player["dead"]:
            if player["imunity"]:
                pygame.draw.polygon(
                    win, player["color"], get_player_lines(player), 1)
            else:
                pygame.draw.polygon(
                    win, player["color"], get_player_lines(player))
        else:
            pygame.draw.circle(win, (255, 17, 0), (round(
                player["x"]), round(player["y"])), round(player["radius"]))
            pygame.draw.circle(win, (255, 115, 0), (round(player["x"]), round(
                player["y"])), round(2*player["radius"]/3))
            pygame.draw.circle(win, (255, 221, 0), (round(
                player["x"]), round(player["y"])), round(player["radius"]/3))
        for shot in player["shots"]:
            pygame.draw.circle(win, player["color"], (round(
                shot["x"]), round(shot["y"])), round(player["shot_radius"]))

        if draw_colision_circles:
            pygame.draw.circle(win, (255, 0, 0), (round(
                player["x"]), round(player["y"])), player["radius"], 1)

    for i in range(1, game["lifes"]+1):
        main_color = (191, 63, 54)
        secondary_color = (227, 62, 50)
        if i > game["current_lifes"]:
            main_color = (210, 210, 210)
            secondary_color = (180, 180, 180)
        radius = heart_radius

        x = i * radius/2 + i * 2 * radius - radius   
        y = heart_radius * 1.5
        draw_heart(win, radius, main_color, secondary_color, x, y)

    for drop in game["drops"]:
        if drop["type"] == "LIFE":
            main_color = (200, 53, 44)
            secondary_color = (255, 52, 40)
        else:
            main_color = (0, 152, 186)
            secondary_color = (0, 190, 245)

        if draw_colision_circles:
            pygame.draw.circle(win, (255, 0, 0), (round(drop["x"]), round(drop["y"])), drop["radius"], 1) 
        draw_heart(win, drop["radius"], main_color, secondary_color, drop["x"], drop["y"])


    if game["wave_change"]:
        text = wave_font.render("WAVE "+ str(game["wave"]), True, (247, 247, 247))
        win.blit(text, (round(wave_text_x), round(height/2 - text.get_height())))

    score = Text(width/2, 20, 30, "press_start_2p", str(game["score"]),(200, 200, 200))
    win.blit(score.text, (
            score.x,
            score.y,
        ))
    
    pygame.display.update()


def multiplayer_main(game_type, options):
    net = Network()
    if not net.status == "ERROR":
        net.connect_to_game(game_type, encode_options(options))
    print("Connection status: ", net.status)

    if not net.status == "ERROR":
        wave_text_x = -400
        game = net.game

        run = True
        clock = pygame.time.Clock()

        while run:
            try:
                clock.tick(60)
                redraw_window(win, game, wave_text_x)
                

                keys = pygame.key.get_pressed()
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    game = net.send("LEFT")
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    game = net.send("RIGHT")
                if keys[pygame.K_UP] or keys[pygame.K_w]:
                    game = net.send("ACCELERATE")
                else:
                    game = net.send("STOP_ACCELERATE")
                
                game = net.send("GET")

                if game["game_over"]:
                    break
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            game = net.send("SHOOT")
                        if event.key == pygame.K_ESCAPE:
                            run = False
                    elif event.type == pygame.QUIT:
                        quit()

                if not game["wave_change"]:
                    wave_text_x = -400
                else:
                    wave_text_x += wave_text_x_vel
            except:
                print("Game closed")
                run = False
        try:
            net.client.close()
        except socket.error:
            pass
        try:
            if game["game_over"]:
                game_over_menu(game["wave"], game["score"])
        except KeyError:
            pass
        game_menu()
    else:
        game_menu()



def singleplayer_main(*args):
    print("Game started.")

    wave_text_x = -400

    run = True
    clock = pygame.time.Clock()
    player_id = 0 

    game = Game(player_id, args[0])
    start_new_thread(game_thread, (game,))

    while run:
        clock.tick(40)
        redraw_window(win, encode_game(game, player_id), wave_text_x)

        keys = pygame.key.get_pressed()
        if not game.player.dead:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                game.player.movement("LEFT")
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                game.player.movement("RIGHT")
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                game.player.movement("ACCELERATE")
            else:
                game.player.movement("STOP_ACCELERATE")

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    game.player.movement("SHOOT")
                if event.key == pygame.K_ESCAPE:
                    run = False
            elif event.type == pygame.QUIT:
                run = False
                quit()

        if not game.wave_change:
            wave_text_x = -400
        else:
            wave_text_x += wave_text_x_vel

        if game.player.game_over:
            run = False
            game_over_menu(game.wave, game.score)

    print("Game main finished.")
    main_menu()

def menu(buttons=[], texts=[], images=[], font_name="press_start_2p"):
    while True:
        win.fill((26, 28, 31))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for button in buttons:
                    if button.mouse_up and button.clicked:
                        button.clicked(button.args)

        for button in buttons:
            mouse_pos = pygame.mouse.get_pos()

            button.check_mouse_up(mouse_pos[0], mouse_pos[1])
            color = button.color
            if button.mouse_up:
                color = button.hover_color

            pygame.draw.rect(win, color, (button.x, button.y, button.width, button.height), button.border)

            font = pygame.font.Font("assets/fonts/"+font_name+".ttf", button.font_size)
            text = font.render(button.text, True, color)
            win.blit(text, (
                    ceil(button.x + button.width/2 - text.get_width()/2),
                    ceil(button.y + button.height/2 - text.get_height()/2)
                ))

        for text in texts:
            win.blit(text.text, (
                    text.x,
                    text.y
                ))

        for image in images:
            win.blit(all_images[image.index], (image.x, image.y))

        pygame.display.update()


def main_menu(*args):
    buttons_width = 250
    buttons_height = 90

    buttons = [
        Button(width/2 - buttons_width/2, height/2 - buttons_height/2, buttons_width, buttons_height, 30, "PLAY", -1, (50, 50, 50), (100, 100, 100), game_menu),
    ]

    texts = [
        Text(width/2, 210, 75, "press_start_2p", "ASTEROIDS", (255, 255, 255)),
    ]

    images = []

    menu(buttons, texts, images, "press_start_2p")


def game_menu(*args):
    buttons_width = 250
    buttons_height = 90

    buttons = [
        Button(0, 0, 50, 50, 40, "<", -1, (50, 50, 50), (100, 100, 100), main_menu),
        Button(width/2 - buttons_width/2, height/2 - buttons_height/2, buttons_width, buttons_height, 20, "NEW GAME", 1, (50, 50, 50), (100, 100, 100), new_game, default_options),
        Button(width/2 - buttons_width/2, height/2 + 55, buttons_width, buttons_height, 20, "ROOMS", 1, (50, 50, 50), (100, 100, 100), list_room_menu, 1),        
    ]

    texts = [
        Text(width/2, 100, 40, "press_start_2p", "ASTEROIDS", (245, 245, 245)),
    ]

    menu(buttons, texts)


def create_game(*args):
    options = args[0][0]
    if options.type == "SINGLEPLAYER":
        print("SINGLEPLAYER")
        singleplayer_main(options)
    elif options.type == "MULTIPLAYER":
        print("MULTIPLAYER")
        multiplayer_main("CREATE", options)
    elif options.type == "ENTER":
        print("MULTIPLAYER")
        print("OPTIONS ID: ",options.game_id)
        multiplayer_main("ENTER", options)
    else:
        print("Could not create the game...")
        main_menu()

def new_game(*args):
    options = args[0][0]

    difficulty_easy_color = (152, 162, 166)
    difficulty_normal_color = (194, 194, 194)
    difficulty_hard_color = (194, 112, 112)
    difficulty_insane_color = (140, 0, 0)

    if options.difficulty == "EASY":
        difficulty_easy_color = (209, 224, 230)
        indicator_difficulty_x =  (width - 100)/4 - width/4 + 200
        indicator_color = (209, 224, 230)
    elif options.difficulty == "NORMAL":
        difficulty_normal_color = (232, 232, 232)
        indicator_difficulty_x =  2 * (width - 100)/4 - width/4 + 200
        indicator_color = (232, 232, 232)
    elif options.difficulty == "HARD":
        difficulty_hard_color = (227, 77, 77)
        indicator_difficulty_x =  3 * (width - 100)/4 - width/4 + 200
        indicator_color = (227, 77, 77)
    else:
        difficulty_insane_color = (201, 0, 0)
        indicator_difficulty_x =  4 * (width - 100)/4 - width/4 + 200
        indicator_color = (201, 0, 0)


    if options.type == "SINGLEPLAYER":
        single_text_color = (200, 200, 200)
        multi_text_color = (100, 100, 100)
    else:
        single_text_color = (100, 100, 100)
        multi_text_color = (200, 200, 200)


    buttons = [
        Button(0, 0, 50, 50, 40, "<", -1, (50, 50, 50), (100, 100, 100), game_menu),
        Button(880, height-90, 120, 80, 40, ">", -1, (50, 50, 50), (100, 100, 100), create_game, options),
        Button(width/2 - 230, height/2 - 170, 220, 50, 17, "SINGLEPLAYER",1, single_text_color, (200, 200, 200), options.change_type, "SINGLEPLAYER"),
        Button(width/2 + 5, height/2 - 170, 220, 50, 17, "MULTIPLAYER",1, multi_text_color, (200, 200, 200), options.change_type, "MULTIPLAYER"),

        Button((width - 100)/4 - width/4 + 100,   height-150, 200, 50, 15, "EASY", 1, difficulty_easy_color, (209, 224, 230), options.change_difficulty, "EASY"),
        Button(2*(width - 100)/4 - width/4 + 100, height-150, 200, 50, 15, "NORMAL", 1, difficulty_normal_color, (232, 232, 232), options.change_difficulty, "NORMAL"),
        Button(3*(width - 100)/4 - width/4 + 100, height-150, 200, 50, 15, "HARD", 1, difficulty_hard_color, (227, 77, 77), options.change_difficulty, "HARD"),
        Button(4*(width - 100)/4 - width/4 + 100, height-150, 200, 50, 15, "INSANE", 1, difficulty_insane_color, (201, 0, 0), options.change_difficulty, "INSANE"),
    ]

    texts = [
        Text(width/2, 100, 40, "press_start_2p", "NEW GAME", (245, 245, 245)),
        Text(indicator_difficulty_x, height - 75, 35, "krona_one", "^", indicator_color),
    ]

    images = []

    if options.type == "SINGLEPLAYER":
        images.append(Image(width/2 - 100, height/2 - 75, "single_player_image"))
        buttons.append(
                Button(width/2 - 105, height/2 - 80, 210, 210, 10, "", 0, (255, 255, 255), (255, 255, 255),)
            )
    else:
        images.append(Image(width/2 - 210, height/2 - 75, "two_players_image"))
        images.append(Image(width/2 + 10, height/2 - 75, "four_players_image"))
        two_button_color = (26, 28, 31)
        four_button_color = (26, 28, 31)

        if options.max_players == 2:
            two_button_color = (255, 255, 255)
        elif options.max_players == 4:
            four_button_color = (255, 255, 255)

        buttons.append(
                Button(width/2 - 215, height/2 - 80, 210, 210, 10, "", 0, two_button_color, (255, 255, 255), options.change_max_players)
            )
        buttons.append(
                Button(width/2 + 5, height/2 - 80, 210, 210, 10, "", 0, four_button_color, (255, 255, 255), options.change_max_players)
            )

    menu(buttons, texts, images)


def game_over_menu(wave, score):
    buttons = [
        Button(width-201, height-41, 200, 40, 20, "MAIN MENU", 1, (36, 38, 41), (136, 138, 141), main_menu),
    ]
    texts = [
        Text(width/2, height/2 - 100, 60, "press_start_2p", "GAME OVER", (189, 13, 0)),
        Text(width/2, height/2, 30, "press_start_2p", "LAST WAVE: "+str(wave), (100, 100, 100)),
        Text(width/2, height/2+100, 40, "press_start_2p", "SCORE: "+str(score), (100, 100, 100)),
    ]


    menu(buttons, texts)

def list_room_menu(*args):
    page = args[0][0]

    net = Network()
    print("PAGE: ", page)
    games_data = net.get_games_list(page)

    buttons = [
        Button(0, 0, 50, 50, 40, "<", -1, (50, 50, 50), (100, 100, 100), game_menu),
    ]

    texts = [
        Text(width/2, 100, 40, "press_start_2p", "ROOMS", (245, 245, 245)),
    ]

    if not games_data["game_list"] or net.status == "ERROR":
        texts.append(Text(width/2-35, height/2-20, 200, "krona_one", ":", (36, 38, 41)))
        texts.append(Text(width/2+35, height/2, 200, "krona_one", "(", (36, 38, 41)))
        texts.append(Text(width/2, height/2, 20, "press_start_2p", "No matches found", (150,150,150)))
    else:
        buttons.append(Button(
                width/2 - 105, 
                height - 90,
                40,
                40,
                20,
                "<",
                1,
                (100, 100, 100),
                (200, 200, 200),
                list_room_menu,
                int(games_data["page"]) - 1,
            ))   
        buttons.append(Button(
                width/2 + 75, 
                height - 90,
                40,
                40,
                20,
                ">",
                1,
                (100, 100, 100),
                (200, 200, 200),
                list_room_menu,
                int(games_data["page"]) + 1,
            ))
        texts.append(Text(
                width/2,
                height - 75,
                40,
                "krona_one",
                games_data["page"],
                (230, 230, 230),
            ))


        button_height = (height/2)/ceil(len(games_data["game_list"])/2)
        card_num = 0
        row_num = 0
        for game in games_data["game_list"]:
            options = Options("ENTER")
            options.game_id = game["id"]
            
            button_x = width/2 + 10
            button_y = height/4+button_height*row_num+(row_num*20)
            if card_num%2==0:
                if card_num+1 >= len(games_data["game_list"]):
                    button_x = width/2 - width/8
                else:
                    button_x = width/2 - width/4 - 10
            else:
                row_num += 1

            card_num += 1
            buttons.append(Button(
                    button_x, button_y,
                    width/4, button_height,
                    1,
                    "",
                    1, 
                    (31, 33, 36),
                    (230,230,230), 
                    create_game, 
                    options
                ))
            if game["players_playing"] == game["max_players"]:
                online_color = (171, 14, 0)
            else:
                online_color = (54, 255, 90)
            texts.append(Text(
                    button_x + width/4 - 40,
                    button_y + 30,
                    10,
                    "krona_one",
                    str(game["players_playing"])+"/"+str(game["max_players"]),
                    online_color,
                ))
            texts.append(Text(
                    button_x + 30,
                    button_y + 30,
                    10,
                    "krona_one",
                    str(game["id"]),
                    (50, 50, 50),
                ))
            texts.append(Text(
                    button_x + width/8,
                    button_y + button_height - 7,
                    10,
                    "krona_one",
                    "WAVE: "+str(game["wave"]),
                    (100, 100, 100),
                ))
            if game["difficulty"] == "EASY":
                difficulty_color = (209, 224, 230)
                difficulty_font_size =  18
            elif game["difficulty"] == "NORMAL":
                difficulty_color = (232, 232, 232)
                difficulty_font_size =  21
            elif game["difficulty"] == "HARD":
                difficulty_color = (227, 77, 77)
                difficulty_font_size =  24
            else:
                difficulty_color = (201, 0, 0)
                difficulty_font_size =  28

            texts.append(Text(
                    button_x + width/8,
                    button_y + button_height/2,
                    difficulty_font_size,
                    "krona_one",
                    str(game["difficulty"]),
                    difficulty_color,
                ))

    menu(buttons, texts)


main_menu()
