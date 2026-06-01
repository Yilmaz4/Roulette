# /// script
# dependencies = [
#  "numpy",
#  "pathlib",
#  "platformdirs",
# ]
# ///

__title__ = "Roulette"
__version__ = "1.0.0"
__credits__ = ["Yilmaz", "Leonard"]

# Fix scaling issues under Wayland, not relevant for Windows
import os
if os.environ.get("XDG_SESSION_TYPE") == "wayland" or "WAYLAND_DISPLAY" in os.environ:
    os.environ["SDL_VIDEODRIVER"] = "wayland"
    os.environ["SDL_VIDEO_WAYLAND_SCALE_TO_DISPLAY"] = "1"

import math, random, asyncio,shadows, pygame, pathlib, platformdirs

# Click spots for each bet
coords = {
    "0": (361, 133),
    "1": (404, 192),
    "2": (405, 134),
    "3": (406, 74),
    "4": (442, 192),
    "5": (443, 132),
    "6": (443, 75),
    "7": (480, 192),
    "8": (479, 133),
    "9": (479, 73),
    "10": (521, 195),
    "11": (518, 132),
    "12": (518, 74),
    "13": (557, 195),
    "14": (556, 129),
    "15": (554, 73),
    "16": (593, 192),
    "17": (594, 134),
    "18": (596, 72),
    "19": (632, 193),
    "20": (628, 135),
    "21": (634, 78),
    "22": (672, 193),
    "23": (671, 131),
    "24": (670, 73),
    "25": (708, 191),
    "26": (708, 132),
    "27": (709, 74),
    "28": (746, 194),
    "29": (745, 131),
    "30": (744, 76),
    "31": (782, 190),
    "32": (784, 130),
    "33": (780, 78),
    "34": (825, 193),
    "35": (821, 133),
    "36": (821, 75),
    "1st 12": (463, 245),
    "2nd 12": (613, 244),
    "3rd 12": (764, 244),
    "1st row": (860, 195),
    "2nd row": (860, 133),
    "3rd row": (859, 75),
    "1 to 18": (423, 293),
    "19 to 36": (801, 293),
    "even": (500, 291),
    "odd": (727, 291),
    "red": (575, 292),
    "black": (652, 290),
}

red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
black_numbers = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]

# The angle of the wheel's rotation at which each number is at the top of the wheel
angles = {
    0: 0.0,
    32: 9.7,
    15: 19.4,
    19: 29.1,
    4: 38.8,
    21: 48.5,
    2: 58.2,
    25: 67.9,
    17: 77.6,
    34: 87.3,
    6: 97.0,
    27: 106.7,
    13: 116.4,
    36: 126.1,
    11: 135.8,
    30: 145.5,
    8: 155.2,
    23: 164.9,
    10: 174.6,
    5: 184.3,
    24: 194.0,
    16: 203.7,
    33: 213.4,
    1: 223.1,
    20: 232.8,
    14: 242.5,
    31: 252.2,
    9: 261.9,
    22: 271.6,
    18: 281.3,
    29: 290.0,
    7: 300.7,
    28: 310.4,
    12: 320.1,
    35: 329.8,
    3: 339.5,
    26: 349.2,
}

top_left_corner = (341, 44)  # Top left corner of the clickable area for placing bets
bottom_right_corner = (880, 314)  # Bottom right corner   "   "   "  "    "  "

wheel_center = (171, 180)  # Center coordinates of the wheel


# We use a class instead of having everything in the global scope so that we don't have to use the "global" keyword for every variable in each function
class Roulette:
    wheel_rotation_speed = 0.0  # The amount wheel_rotation_angle increases per game tick
    wheel_rotation_angle = 0.0  # Rotation angle of the wheel in radians

    ball_rotation_speed = 0.0  # The amount ball_rotation_angle increases per game tick
    ball_rotation_angle = 0.0  # Polar angle of the ball relative to the wheel center, in radians
    ball_distance = 135.0  # Polar distance of the ball
    ball_on_number = -1  # The number that the ball has fallen onto, -1 if it's still rolling
    ball_num_bounces = 0  # Number of times the ball has bounced so far
    ball_bounce_timestamp = 0  # Last time the ball bounced

    quit_counter = 0  # Increments every time user tries to quit, only exits when == 3
    quit_timestamp = -500  # Used to fade out the cat png when user tries to quit while the wheel is spinning

    last_bet_place_timestamp = 0  # Used for adding bets while holding down the mouse button

    game_over_timestamp = 0  # Used to fade in the end screen

    win_timestamp = -1500  # Used to fade out the win screen
    lose_timestamp = -1000  # Used to make the text red when money is lost

    bets: dict[str, int] = {}  # Stores the amount of money bet on each position on the board
    bank_account = 1000  # Amount of money player has
    highscore = 0  # High-score, only saved when the player quits the game, and half of it becomes the starting bank account when the game loads next time

    _xp = 0  # Current XP
    _xp_interpolate = 0  # The amount of XP displayed on the XP bar, used for animating the bar when XP increases

    def __init__(self):
        pygame.init()
        pygame.font.init()

        self.clock = pygame.time.Clock()

        self.screen = pygame.display.set_mode([1000, 360], 0, 32)  # 1000 pixels wide, 360 pixels tall, no flags, 32 bits
        pygame.display.set_caption("Roulette")  # Set window title

        self.font = pygame.font.Font(None, 30)

        self.table_png = pygame.image.load("assets/table-base.png")
        self.coin_png = pygame.image.load("assets/coin.png")
        self.wheel_png = pygame.image.load("assets/wheel.png")
        self.ball_png = pygame.image.load("assets/ball-img.png")
        self.quit_screen_1_png = pygame.image.load("assets/screens/quit.png")
        self.quit_screen_2_png = pygame.image.load("assets/screens/quit2.png")
        self.quit_screen_3_png = pygame.image.load("assets/screens/quit3.png")
        self.quit_during_game_screen_png = pygame.image.load("assets/screens/quit-during-game.png")

        pygame.display.set_icon(self.ball_png)

        self.end_screens = [
            pygame.image.load("assets/screens/joever.png"),
            pygame.image.load("assets/screens/joever2.png"),
            pygame.image.load("assets/screens/joever3.png"),
        ]

        self.win_screens = [
            pygame.image.load("assets/screens/win.png"),
            pygame.image.load("assets/screens/win2.png"),
            pygame.image.load("assets/screens/win3.png"),
            pygame.image.load("assets/screens/win4.png"),
            pygame.image.load("assets/screens/win5.png"),
            pygame.image.load("assets/screens/win6.png"),
        ]
        self.win_screen = self.win_screens[0]

        self.ambient_music = pygame.mixer.music.load(
            random.choice(["assets/sounds/ambient.mp3", "assets/sounds/ambient2.mp3"])
        )
        pygame.mixer.music.play()
        pygame.mixer.music.set_volume(0.2)

        self.place_bet_sounds = [
            pygame.mixer.Sound("assets/sounds/place1.mp3"),
            pygame.mixer.Sound("assets/sounds/place2.mp3"),
            pygame.mixer.Sound("assets/sounds/place3.mp3"),
            pygame.mixer.Sound("assets/sounds/place4.mp3"),
            pygame.mixer.Sound("assets/sounds/place5.mp3"),
            pygame.mixer.Sound("assets/sounds/place6.mp3"),
            pygame.mixer.Sound("assets/sounds/place7.mp3"),
        ]
        self.place_all_sound = pygame.mixer.Sound("assets/sounds/place_all.mp3")
        self.place_bets_please_sounds = [
            pygame.mixer.Sound("assets/sounds/please1.mp3"),
            pygame.mixer.Sound("assets/sounds/please2.mp3"),
            pygame.mixer.Sound("assets/sounds/please3.mp3"),
            pygame.mixer.Sound("assets/sounds/please4.mp3"),
            pygame.mixer.Sound("assets/sounds/please5.mp3"),
            pygame.mixer.Sound("assets/sounds/please6.mp3"),
        ]
        self.wheel_rotate_sound = pygame.mixer.Sound("assets/sounds/wheel.mp3")

        self.ball_bounce_sounds = [
            pygame.mixer.Sound("assets/sounds/bounce.mp3"),
            pygame.mixer.Sound("assets/sounds/bounce2.mp3"),
            pygame.mixer.Sound("assets/sounds/bounce3.mp3"),
            pygame.mixer.Sound("assets/sounds/bounce4.mp3"),
        ]
        self.ball_land_sound = pygame.mixer.Sound("assets/sounds/ball_land.mp3")
        self.win_sound = pygame.mixer.Sound("assets/sounds/win.mp3")

        for s in self.place_bet_sounds:
            s.set_volume(0.3)
        self.place_all_sound.set_volume(0.3)
        for s in self.place_bets_please_sounds:
            s.set_volume(0.3)
        self.wheel_rotate_sound.set_volume(0.5)
        self.win_sound.set_volume(0.5)

        self.highscore = self.storeHighscore()
        if self.highscore // 2 > self.bank_account:
            self.bank_account = self.highscore // 2

    # Getter method for XP, returns the time-interpolated value in order to animate the XP bar when the XP increases
    @property
    def xp(self):
        t = max(0.0, min(1.0, (pygame.time.get_ticks() - self.win_timestamp) / 2500))
        if t == 1.0:
            self._xp_interpolate = self._xp
            return self._xp_interpolate
        return self._xp_interpolate + (self._xp - self._xp_interpolate) * (1 - (1 - t) ** 3)

    # Setter method for XP
    @xp.setter
    def xp(self, val):
        self._xp = val

    # Getter method for the level of the player based on xp
    @property
    def level(self):
        return int(self.xp // 1076)

    # Getter method for the percent of bonus added to each net-profit based on level
    @property
    def bonus_percent(self):
        return int((self.level * 10) ** (1 / 5) * 10)

    # Static method for rendering an image rotated around its center, credit: https://stackoverflow.com/a/54714144 (modified)
    @staticmethod
    def blitRotateCenter(surf: pygame.Surface, image: pygame.Surface, topleft: list[int], angle: float):
        rotated_image = pygame.transform.rotozoom(image, -math.degrees(angle), 1.0)
        new_rect = rotated_image.get_rect(center=image.get_rect(topleft=topleft).center)

        surf.blit(rotated_image, new_rect)

    # Static method for mapping radians to the [0, 2*PI) interval
    @staticmethod
    def simplifyAngle(theta: float):
        return theta % (2 * math.pi)

    # Static method for computing the difference between two angles in radians
    @staticmethod
    def angleDifference(alpha: float, beta: float):
        return abs(Roulette.simplifyAngle(alpha) - Roulette.simplifyAngle(beta))

    # Static method for interpolating between two colors a and b, t=0 gives a, t=1 gives b
    @staticmethod
    def interpolateColor(a: list[int], b: list[int], t: float):
        return [max(min(int(x + (y - x) * t), 255), 0) for x, y in zip(a, b)]

    # Writes the high-score to a file in AppData and returns the value
    def storeHighscore(self):
        data_dir = pathlib.Path(platformdirs.user_data_dir("Roulette"))
        data_dir.mkdir(parents=True, exist_ok=True)
        file = data_dir / "highscore.txt"

        highscore = 0
        if file.exists():
            highscore = int(file.read_text().strip())
        if self.bank_account > highscore:
            file.write_text(str(self.bank_account))
        return int(max(self.bank_account, highscore))

    def getClosestBet(self, pos: tuple[int, int]):
        closest_bet = ""
        min_dist = float("inf")
        for bet, coord in coords.items():
            dist = math.dist(pos, coord)
            if dist < min_dist:
                closest_bet = bet
                min_dist = dist
        return closest_bet

    # Add money on the specified bet
    def addBet(self, bet: str):
        amount_to_add = 10  # Default bet amount
        amount_max = self.bank_account - sum(self.bets.values())  # The money we have left to bet with

        if bet not in self.bets:  # The dictionary is empty by default so we need to create the key-value pair first
            self.bets[bet] = 0
        if self.bets[bet] > 10:  # If there's already bets for this bet
            amount_to_add = 10 ** math.floor(math.log10(self.bets[bet]))  # Exponential increase
        if amount_to_add > amount_max:  # If it exceeds the total money left
            amount_to_add = amount_max
        if amount_to_add == 0:  # If player has no money left to bet with
            return

        self.bets[bet] += amount_to_add
        if amount_to_add == amount_max:
            self.place_all_sound.play()  # Special sound effect for going all-in
        else:
            random.choice(self.place_bet_sounds).play()

    # Method for processing the outcome of the game
    def processBets(self, now: int):
        prev_amount = self.bank_account

        self.bank_account -= sum(self.bets.values())  # Subtract the amount bet from the bank account
        amount_won = 0

        # Check all bets and add the winnings to the amount_won variable
        for bet, amount in self.bets.items():
            if bet.isdigit() and int(bet) == self.ball_on_number:
                amount_won += 36 * amount
                continue

            match bet:
                case "1st 12" if 1 <= self.ball_on_number <= 12:
                    amount_won += 3 * amount
                case "2nd 12" if 13 <= self.ball_on_number <= 24:
                    amount_won += 3 * amount
                case "3rd 12" if 25 <= self.ball_on_number <= 36:
                    amount_won += 3 * amount

                case "1st row" if (self.ball_on_number + 2) % 3 == 0:
                    amount_won += 3 * amount
                case "2nd row" if (self.ball_on_number + 1) % 3 == 0:
                    amount_won += 3 * amount
                case "3rd row" if (self.ball_on_number + 0) % 3 == 0:
                    amount_won += 3 * amount

                case "1 to 18" if 1 <= self.ball_on_number <= 18:
                    amount_won += 2 * amount
                case "19 to 36" if 19 <= self.ball_on_number <= 36:
                    amount_won += 2 * amount

                case "even" if self.ball_on_number % 2 == 0 and self.ball_on_number != 0:
                    amount_won += 2 * amount
                case "odd" if self.ball_on_number % 2 != 0:
                    amount_won += 2 * amount

                case "red" if self.ball_on_number in red_numbers:
                    amount_won += 2 * amount
                case "black" if self.ball_on_number in black_numbers:
                    amount_won += 2 * amount

        self.bets.clear()

        self.bank_account += amount_won  # Add the winnings to the bank account

        if self.bank_account > prev_amount:  # If there's a net profit
            # We only add the bonus to the net profit to prevent farming bonus by betting the same amount to contradictory bets
            self.bank_account += (self.bank_account - prev_amount) * self.bonus_percent // 100
            self.xp += self.bank_account - prev_amount

            self.win_sound.play()
            self.win_timestamp = now
            self.win_screen = random.choice(self.win_screens)

        elif self.bank_account < prev_amount:  # If there's a net loss
            self.lose_timestamp = now

    # Method for processing window events such as quitting or pressing mouse buttons
    def processEvents(self, now: int):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if self.wheel_rotation_speed != 0:  # Ignore if the wheel is spinning
                    self.quit_timestamp = now
                    return
                if self.bank_account == 0:  # Ignore if the game is about to end
                    return
                if self.quit_counter != 3:  # Ignore if the user hasn't pressed quit 3 times yet
                    self.quit_counter += 1
                    return

                self.storeHighscore()  # Only store the high-score if the player willingly quits the game

                pygame.quit()
                raise SystemExit

            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.quit_counter > 0:
                    self.quit_counter = 0  # Disable the quit screen and go back to the game
                    return

                if self.wheel_rotation_speed != 0.0:  # No interaction while the wheel is spinning
                    return

                # Did the user click within the bets area
                if (
                    top_left_corner[0] <= event.pos[0] <= bottom_right_corner[0]
                    and top_left_corner[1] <= event.pos[1] <= bottom_right_corner[1]
                ):
                    closest_bet = self.getClosestBet(event.pos)

                    if event.button == 1:  # Left mouse button clicked
                        self.addBet(closest_bet)
                        self.last_bet_place_timestamp = now + 500

                    elif event.button == 3:  # Right mouse button clicked
                        self.bets[closest_bet] = 0  # Remove all bets from this bet

                # Did the user click on the middle of the wheel
                elif math.dist(event.pos, wheel_center) < 15:
                    if sum(self.bets.values()):  # Has the user placed any bets
                        # Reset all parameters, spin up the wheel and roll the ball
                        self.wheel_rotation_speed = random.uniform(0.2, 0.3)
                        self.ball_rotation_speed = -random.uniform(0.4, 0.5)
                        self.ball_rotation_angle = 0.0
                        self.ball_distance = 135
                        self.ball_on_number = -1
                        self.ball_num_bounces = 0

                        self.wheel_rotate_sound.play()
                    else:
                        random.choice(self.place_bets_please_sounds).play()  # Some woman saying "place your bets please"

        if pygame.mouse.get_pressed()[0]:
            mouse_pos = pygame.mouse.get_pos()
            if (
                now - self.last_bet_place_timestamp > 100
                and top_left_corner[0] <= mouse_pos[0] <= bottom_right_corner[0]
                and top_left_corner[1] <= mouse_pos[1] <= bottom_right_corner[1]
            ):
                closest_bet = self.getClosestBet(mouse_pos)
                self.addBet(closest_bet)
                self.last_bet_place_timestamp = now

    # Method for making things move and generating the outcome of each run
    def processPhysics(self, now: int):
        self.wheel_rotation_angle += self.wheel_rotation_speed
        self.wheel_rotation_speed /= 1.006  # Wheel slows down due to friction

        if self.wheel_rotation_speed != 0 and self.wheel_rotation_speed < 0.002:  # Has the wheel come to a stop?
            self.wheel_rotation_speed = 0.0
            self.processBets(now)

        self.ball_rotation_angle += self.ball_rotation_speed
        self.ball_rotation_speed /= 1.01  # Ball slows down due to friction

        if self.ball_rotation_speed != 0:
            if self.ball_distance <= 76.0:  # Wait for the ball to fall towards the wheel
                # Make the ball bounce a maximum number of 4 times
                if (
                    now - self.ball_bounce_timestamp > random.randrange(200, 400)
                    and self.ball_num_bounces < 3
                    and abs(self.ball_rotation_speed - self.wheel_rotation_speed) > 0.01
                ):
                    self.ball_rotation_speed = -(self.ball_rotation_speed - self.wheel_rotation_speed) * 0.85  # Bounce the ball
                    self.ball_num_bounces += 1
                    self.ball_bounce_sounds[self.ball_num_bounces].play()
                    self.ball_bounce_timestamp = now
                    return

                if (
                    abs(self.ball_rotation_speed - self.wheel_rotation_speed) > 0.01
                ):  # Only let the ball land on a number once it's slow enough
                    return

                # Calculate the coordinates of the ball
                ball_pos_x = wheel_center[0] + self.ball_distance * math.cos(self.ball_rotation_angle)
                ball_pos_y = wheel_center[1] + self.ball_distance * math.sin(self.ball_rotation_angle)

                closest_num = -1
                smallest_dist = 360.0

                # Find the number on the wheel closest to the ball
                for num, angle in angles.items():
                    num_pos_x = wheel_center[0] + 100 * math.cos(self.wheel_rotation_angle - math.pi / 2 + (angle * math.pi / 180))
                    num_pos_y = wheel_center[1] + 100 * math.sin(self.wheel_rotation_angle - math.pi / 2 + (angle * math.pi / 180))

                    dist = math.dist([ball_pos_x, ball_pos_y], [num_pos_x, num_pos_y])

                    if dist < smallest_dist:
                        smallest_dist = dist
                        closest_num = num

                delta_angle = self.angleDifference(
                    self.ball_rotation_angle, self.wheel_rotation_angle - math.pi / 2 + (angles[closest_num] * math.pi / 180)
                )
                if delta_angle < 0.005:  # Only accept if the angle difference is small enough to make it look smooth
                    self.ball_on_number = closest_num
                    self.ball_rotation_speed = 0
                    self.ball_land_sound.play()
            else:
                self.ball_distance -= 0.25

        # If the ball has landed on a number, keep it stuck to the number while the wheel comes to a stop
        if self.ball_on_number != -1:
            self.ball_rotation_angle = self.wheel_rotation_angle - math.pi / 2 + (angles[self.ball_on_number] * math.pi / 180)
            self.ball_distance = 75

    def renderTable(self, now: int):
        self.screen.blit(self.table_png, [0, 0])  # Render the main roulette table

        # Rotate the wheel with self.wheel_rotation_angle and render it
        self.blitRotateCenter(
            self.screen, self.wheel_png, [sum(x) for x in zip(wheel_center, (-100, -100))], self.wheel_rotation_angle
        )

        # Calculate the coordinates of the ball from its polar coordinates and render it
        self.screen.blit(
            self.ball_png,
            [
                wheel_center[0] - 7 + self.ball_distance * math.cos(self.ball_rotation_angle),
                wheel_center[1] - 7 + self.ball_distance * math.sin(self.ball_rotation_angle),
            ],
        )

        # Render the bet coins and optionally the text on top of them
        for bet, amount in self.bets.items():
            if amount > 0:
                self.screen.blit(self.coin_png, [sum(x) for x in zip(coords[bet], (-27.5, -27.5))])
                if amount > 10:
                    text = shadows.add_shadow(self.font.render(str(amount), True, (255, 255, 255), None), (0, 0), 1.1, 0.2)
                    textSize = text.get_size()
                    self.screen.blit(text, [sum(x) for x in zip(coords[bet], (-textSize[0] / 2, -textSize[1] / 2))])

        # Display the amount of money in the bank account
        color = self.interpolateColor([255, 0, 0], [255, 255, 255], (now - self.lose_timestamp) / 1500)
        text = shadows.add_shadow(self.font.render(f"Bank: ${str(self.bank_account)}", True, color, None), (2, 2), 1.0, 0.2)
        self.screen.blit(text, [340, 12])

        # Display the amount that has been bet
        prev_length = text.get_size()[0]  # Offset by the length of the previous text
        text = shadows.add_shadow(
            self.font.render(f"Amount bet: ${str(sum(self.bets.values()))}", True, [255, 255, 255], None), (2, 2), 1.0, 0.2
        )
        self.screen.blit(text, [340 + prev_length + 10, 12])

        # Display the high-score
        text = shadows.add_shadow(
            self.font.render(f"High-score: ${str(self.highscore)}", True, [255, 255, 255], None), (2, 2), 1.0, 0.2
        )
        self.screen.blit(text, [882 - text.get_size()[0], 12])

        # Display the level bar and bonus percent
        pygame.draw.rect(self.screen, (200, 200, 200), (894, 45, 15, 269))

        remaining_xp = (self.xp / 4) % 269
        pygame.draw.rect(self.screen, (255, 0, 0), (894, 45 + (269 - remaining_xp), 15, remaining_xp))

        text = shadows.add_shadow(self.font.render(f"LVL {self.level}", True, [255, 255, 255], None), (2, 2), 1.0, 0.2)
        self.screen.blit(text, [920, 45])

        text = shadows.add_shadow(self.font.render(f"{self.bonus_percent}%", True, [255, 255, 255], None), (2, 2), 1.0, 0.2)
        self.screen.blit(text, [920, 45 + 274 - text.get_size()[1] * 2])
        text = shadows.add_shadow(self.font.render("Bonus", True, [255, 255, 255], None), (2, 2), 1.0, 0.2)
        self.screen.blit(text, [920, 45 + 274 - text.get_size()[1]])

        # Display the win screen and fade it out in 1.5 seconds
        if now - self.win_timestamp < 1500:
            image = self.win_screen.copy()
            image.set_alpha(255 - int((now - self.win_timestamp) * 255 / 1500))
            self.screen.blit(image, [0, 0])

        # Display the cat saying nuh uh if user tries quitting while the wheel is spinning
        if now - self.quit_timestamp < 500:
            image = self.quit_during_game_screen_png.copy()
            image.set_alpha(255 - int((now - self.quit_timestamp) * 255 / 500))
            self.screen.blit(image, [0, 0])

    async def gameloop(self):
        while True:
            now = pygame.time.get_ticks()  # Milliseconds since the start of the game

            self.processEvents(now)
            self.processPhysics(now)

            if self.quit_counter > 0:
                match self.quit_counter:  # Display the quit screens
                    case 1:
                        self.screen.blit(self.quit_screen_1_png, [0, 0])
                    case 2:
                        self.screen.blit(self.quit_screen_2_png, [0, 0])
                    case 3:
                        self.screen.blit(self.quit_screen_3_png, [0, 0])
            else:
                self.renderTable(now)  # Render everything

                if self.bank_account == 0:  # Is the game over?
                    if self.game_over_timestamp == 0:
                        self.game_over_timestamp = (
                            now + 2000
                        )  # We add 2000 so that it waits 2 seconds before starting to show the end screen
                        self.game_over_screen = random.choice(self.end_screens)
                        pygame.mixer.music.fadeout(4000)

                    # Fade the display screen in for 3 seconds
                    image = self.game_over_screen.copy()
                    image.set_alpha(int((now - self.game_over_timestamp) * 255 / 3000))
                    self.screen.blit(image, [0, 0])

                    # Close the game 2 + 4 = 6 seconds after the player has run out of money
                    if (now - self.game_over_timestamp) > 4000:
                        pygame.quit()
                        raise SystemExit

            pygame.display.update()  # Updates the contents of the window

            self.clock.tick(60)  # Lock the game to 60 FPS

            await asyncio.sleep(0)  # Required for pygbag


async def main():
    game = Roulette()
    await game.gameloop()


asyncio.run(main())
