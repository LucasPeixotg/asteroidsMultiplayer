from math import sin, cos, radians, pi, floor
from random import randint, random
from time import time

# Game constants
ship_acceleration = .02
speed_limit = 8
ship_friction = .99
ship_radius = 15
rotate_vel = 5
shot_vel = 10
shot_radius = 2
maximum_shots = 3
teleport_shots = False
dead_time = 5
imunity_time = 10
player_lifes = 3
min_rock_radius = 60
max_rock_radius = 100
max_rock_vel = 1
min_rock_vel = .1
initial_rocks = 2
min_new_rocks = 2
max_new_rocks = 3
rock_jaggedness = .1
rock_vert = 10
width = 1000
height = 700
rocks_per_wave = 7
max_rocks_on_screen = 5
wave_delay = 13
dropable_vel = .5
new_life_chance = .1
revive_friend_chance = .05
heart_radius = 15
revive_radius = 12
easy_mult = .5
normal_mult = .7
hard_mult = 1
insane_mult = 1.2

colors = [
    (3, 211, 252),
    (219, 3, 252),
    (252, 128, 3),
    (53, 252, 3),
]

def distance_between(x1, y1, x2, y2):
    return ((x2-x1)**2 + (y2-y1)**2)**(1/2)


def get_difficulty_multiplier(difficulty):
    mult = 0
    if difficulty == "EASY":
        mult = easy_mult
    elif difficulty == "NORMAL":
        mult = normal_mult
    elif difficulty == "HARD":
        mult = hard_mult
    elif difficulty == "INSANE":
        mult = insane_mult
    return mult


class DropableItem:
    def __init__(self, x, y, drop_type):
        self.x = x
        self.y = y
        self.type = drop_type

        direction = [1, -1]
        self.x_vel = dropable_vel * direction[randint(0, 1)] / 2
        self.y_vel = sin(radians(self.x)) * dropable_vel

        if self.type == "LIFE":
            self.radius = heart_radius
        else:
            self.radius = revive_radius

    def update(self):
        self.x += self.x_vel
        self.y -= self.y_vel

        self.y_vel = sin(radians(self.x)) * dropable_vel


class Shot:
    def __init__(self, x, y, x_vel, y_vel):
        self.x = x
        self.y = y
        self.x_vel = x_vel
        self.y_vel = y_vel

    def move(self, game_speed):
        self.x += self.x_vel * game_speed
        self.y -= self.y_vel * game_speed


class Player:
    def __init__(self, player_id):
        self.x = round(width/2)
        self.y = round(height/2)
        self.shots = []
        self.vel = 0
        self.acceleration = ship_acceleration
        self.radius = ship_radius
        self.angle = 180
        self.destroyed_rocks = 0
        self.lifes = player_lifes
        self.dead = False
        self.accelerating = False
        self.imunity = False
        self.id = player_id
        self.imunity_time = 0
        self.death_time = 0
        self.game_over = False
        self.color = colors[player_id % 4]

    def movement(self, move):
        if move == "RIGHT":
            self.angle -= rotate_vel
        elif move == "LEFT":
            self.angle += rotate_vel
        elif move == "SHOOT":
            self.shot()
        elif move == "ACCELERATE":
            self.accelerating = True
        elif move == "STOP_ACCELERATE":
            self.accelerating = False

    def shot(self):
        if not len(self.shots) >= maximum_shots:
            x = self.x + 4 / 3 * self.radius * cos(radians(self.angle))
            y = self.y - 4 / 3 * self.radius * sin(radians(self.angle))
            x_vel = cos(radians(self.angle)) * shot_vel
            y_vel = sin(radians(self.angle)) * shot_vel
            self.shots.append(Shot(x, y, x_vel, y_vel))

    def reset(self):
        self.dead = False
        self.x = width/2
        self.y = height/2
        self.angle = 180
        self.imunity = True
        self.vel = 0

    def update(self, game_speed, width, height):
        if not self.accelerating:
            self.vel *= ship_friction
        elif self.vel <= speed_limit:
            self.vel += self.acceleration
            if self.vel > speed_limit:
                self.vel = speed_limit

        self.x += cos(radians(self.angle)) * \
            self.vel * game_speed
        self.y -= sin(radians(self.angle)) * \
            self.vel * game_speed

        if self.x > width + self.radius/1.5:
            self.x = -self.radius/1.5
        elif self.x < -self.radius/1.5:
            self.x = width + self.radius/1.5
        elif self.y > height + self.radius/1.5:
            self.y = -self.radius/1.5
        elif self.y < -self.radius/1.5:
            self.y = height + self.radius/1.5


class Rock:
    def __init__(self, x, y, radius, x_vel, y_vel):
        self.x_vel = x_vel
        self.y_vel = y_vel
        self.vert = floor(random() * (rock_vert + 1) + rock_vert / 2)
        self.offs = []
        self.x = x
        self.y = y
        self.angle = random() * pi * 2
        self.radius = radius

        for _ in range(0, self.vert):
            self.offs.append(random() * rock_jaggedness *
                             2 + 1 - rock_jaggedness)

    def update(self, game_speed, width, height):
        if self.x > width + 3 * self.radius:
            self.x = - 2 * self.radius
        elif self.x < -3 * self.radius:
            self.x = width + 2 * self.radius
        elif self.y > height + 3 * self.radius:
            self.y = - 2 * self.radius
        elif self.y < -3 * self.radius:
            self.y = height + 2 * self.radius

        self.x += self.x_vel * game_speed
        self.y += self.y_vel * game_speed


class Game:
    def __init__(self, options, game_id):
        self.id = game_id
        try:
            self.difficulty = options["difficulty"]
        except:
            self.difficulty = "NORMAL"
        self.difficulty_multiplier = get_difficulty_multiplier(self.difficulty)
        self.player_dead_time = dead_time
        self.player_imunity_time = imunity_time
        self.wave_delay_time = wave_delay
        self.start_time = time()
        self.width = width
        self.height = height
        self.score = 0
        self.initial_rocks = initial_rocks
        self.shot_radius = shot_radius
        self.player_lifes = player_lifes
        self.game_speed = 1
        self.wave = 1
        self.wave_change = True
        self.initial_rocks = initial_rocks
        self.rocks_per_wave = rocks_per_wave
        self.max_rocks_on_screen = max_rocks_on_screen
        self.max_rock_vel = max_rock_vel * self.difficulty_multiplier
        self.min_rock_vel = min_rock_vel * self.difficulty_multiplier
        self.rocks_created = 0
        self.min_rock_radius = min_rock_radius
        self.max_rock_radius = round(max_rock_radius)
        self.min_new_rocks = round(min_new_rocks * self.difficulty_multiplier)
        self.max_new_rocks = round(max_new_rocks * self.difficulty_multiplier)
        self.players = {}
        self.rocks = []
        self.drops = []
        try:
            if options["max_players"] == 2:
                self.max_players = 2
            else:
                self.max_players = 4
        except:
            self.max_players = 4
        self.game_over = False

    def add_new_player(self, player_id):
        self.players[player_id] = Player(player_id)

    def add_new_rock(self, x=None, y=None, radius=None):
        if not radius:
            r = randint(self.min_rock_radius, self.max_rock_radius)
        else:
            r = radius

        if not x:
            x = randint(0, 1) * self.width
            if x < self.width/2:
                x -= r
            else:
                x += r

        if not y:
            y = randint(0, 1) * self.height
            if y < self.height/2:
                y -= r
            else:
                y += r

        direction = [1, -1]
        x_v = (random() * (self.max_rock_vel - self.min_rock_vel) +
               self.min_rock_vel) * direction[randint(0, 1)]
        y_v = (random() * (self.max_rock_vel - self.min_rock_vel) +
               self.min_rock_vel) * direction[randint(0, 1)]

        self.rocks.append(Rock(x, y, r, x_v, y_v))

    def create_rocks(self):
        for _ in range(self.initial_rocks):
            self.add_new_rock()

    def update_rocks(self):
        for rock in self.rocks:
            rock.update(self.game_speed, self.width, self.height)

    def update_players(self):
        for player in self.players.values():
            player.update(self.game_speed, self.width, self.height)

            for drop in self.drops:
                min_dist = drop.radius + player.radius
                distance = distance_between(drop.x, drop.y, player.x, player.y)
                coliding = distance <= min_dist
                if coliding and not player.dead:
                    self.drops.pop(self.drops.index(drop))
                    if drop.type == "LIFE" and not player.lifes >= self.player_lifes:
                        player.lifes += 1
                    elif drop.type == "REVIVE":
                        for other_p in self.players.values():
                            if other_p.game_over:
                                other_p.lifes += 1
                                other_p.reset()
                                other_p.imunity_time = time()
                                other_p.game_over = False
                                break

            for rock in self.rocks:
                min_dist = rock.radius + player.radius
                distance = distance_between(rock.x, rock.y, player.x, player.y)
                coliding = distance <= min_dist
                if coliding and not (player.dead or player.imunity):

                    self.rocks.pop(self.rocks.index(rock))
                    for _ in range(self.min_new_rocks, self.max_new_rocks):
                        if self.rocks_created <= self.rocks_per_wave:
                            if rock.radius/2 > self.min_rock_radius/2:
                                self.rocks_created += 1
                                self.add_new_rock(
                                    rock.x, rock.y, rock.radius/2)
                            else:
                                self.add_new_rock()
                                self.rocks_created += 1

                    player.death_time = time()
                    player.dead = True
                    player.lifes -= 1

                for shot in player.shots:
                    min_dist = rock.radius + self.shot_radius
                    distance = distance_between(rock.x, rock.y, shot.x, shot.y)
                    if distance <= min_dist:
                        player.shots.pop(player.shots.index(shot))
                        self.rocks.pop(self.rocks.index(rock))
                        player.destroyed_rocks += 1
                        self.score += 1

                        if random() <= new_life_chance:
                            self.drops.append(DropableItem(rock.x, rock.y, "LIFE"))
                        if random() <= revive_friend_chance and len(self.players) > 1:
                            self.drops.append(DropableItem(rock.x, rock.y, "REVIVE"))

                        for _ in range(randint(min_new_rocks, max_new_rocks)):
                            wave_finished = self.rocks_created >= self.rocks_per_wave
                            screen_full = len(
                                self.rocks) >= self.max_rocks_on_screen
                            if not wave_finished and not screen_full:
                                if rock.radius/2 > min_rock_radius/2:
                                    self.rocks_created += 1
                                    self.add_new_rock(
                                        rock.x, rock.y, rock.radius/2)
                                else:
                                    self.add_new_rock()
                                    self.rocks_created += 1

            for shot in player.shots:
                if shot.x > self.width + 2 * self.shot_radius:
                    if teleport_shots:
                        shot.x = -self.shot_radius
                    else:
                        player.shots.pop(player.shots.index(shot))
                elif shot.x < -2 * self.shot_radius:
                    if teleport_shots:
                        shot.x = self.width + shot_radius
                    else:
                        player.shots.pop(player.shots.index(shot))
                elif shot.y > self.height + 2*self.shot_radius:
                    if teleport_shots:
                        shot.y = -self.shot_radius
                    else:
                        player.shots.pop(player.shots.index(shot))
                elif shot.y < -2 * self.shot_radius:
                    if teleport_shots:
                        shot.y = self.height + self.shot_radius
                    else:
                        player.shots.pop(player.shots.index(shot))
                shot.move(self.game_speed)

    def update_drops(self):
        for drop in self.drops:
            if drop.x >= self.width + drop.radius or drop.x <= -drop.radius:
                self.drops.pop(self.drops.index(drop))
            elif drop.y >= self.height + drop.radius or drop.y <= -drop.radius:
                self.drops.pop(self.drops.index(drop))

            drop.update()

    def update_game(self):
        if not self.rocks and not self.wave_change:
            self.wave_change = True
            self.wave += 1
            self.rocks_created = 0

            self.initial_rocks = initial_rocks + self.wave
            self.max_rocks_on_screen = round(max_rocks_on_screen + self.wave*2 * self.difficulty_multiplier)
            self.max_rock_vel = max_rock_vel + self.wave * self.difficulty_multiplier/1000
            self.min_rock_vel = min_rock_vel + self.wave * self.difficulty_multiplier/1000
            self.rocks_per_wave += self.wave
            self.min_rock_radius = min_rock_radius
            self.max_rock_radius = max_rock_radius
            self.min_new_rocks = min_new_rocks
            self.max_new_rocks = max_new_rocks
            self.start_time = time()
            

        else:
            self.update_rocks()

        self.update_drops()
        self.update_players()


def encode_game(game, player_id):
    encoded = {}

    encoded["lifes"] = game.player_lifes
    encoded["player_id"] = player_id
    encoded["current_lifes"] = game.players[player_id].lifes
    encoded["wave_change"] = game.wave_change
    encoded["heart_radius"] = 11
    encoded["wave"] = game.wave
    encoded["game_over"] = game.game_over

    encoded["players"] = []
    encoded["rocks"] = []
    encoded["drops"] = []
    encoded["score"] = game.score

    for drop in game.drops:
        encoded["drops"].append({
            "x": drop.x,
            "y": drop.y,
            "radius": drop.radius,
            "type": drop.type,
        })

    for player in game.players.values():
        if player.game_over:
            continue
        
        enc_p = {
            "x": player.x,
            "y": player.y,
            "angle": player.angle,
            "color": player.color,
            "shots": [],
            "radius": player.radius,
            "shot_radius": game.shot_radius,
            "dead": player.dead,
            "imunity": player.imunity,
        }

        for shot in player.shots:
            enc_p["shots"].append({
                "x": shot.x,
                "y": shot.y,
            })

        encoded["players"].append(enc_p)

    for rock in game.rocks:
        encoded["rocks"].append({
            "x": rock.x,
            "y": rock.y,
            "radius": rock.radius,
            "angle": rock.angle,
            "vert": rock.vert,
            "offs": rock.offs,
        })
    return encoded