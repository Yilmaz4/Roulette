# /// script
# dependencies = [
#  "numpy",
#  "pathlib",
#  "platformdirs",
# ]
# ///

__title__ = "Roulette"
__version__ = "1.0.1"
__credits__ = ["Yilmaz", "Leonard"]

import os

# Behebt Skalierungsprobleme unter Wayland, für Windows nicht relevant
if os.environ.get("XDG_SESSION_TYPE") == "wayland" or "WAYLAND_DISPLAY" in os.environ:
    os.environ["SDL_VIDEODRIVER"] = "wayland"
    os.environ["SDL_VIDEO_WAYLAND_SCALE_TO_DISPLAY"] = "1"

import math, random, asyncio, shadows, pygame, pathlib, platformdirs, sys


# Klickpositionen für jeden Einsatz
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

# Der Rotationswinkel des Kessels, bei dem sich jede Zahl oben am Rad befindet
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
    29: 291.5,
    7: 300.7,
    28: 311,
    12: 320.1,
    35: 329.8,
    3: 339.5,
    26: 349.2,
}

top_left_corner = (341, 44)  # Obere linke Ecke des anklickbaren Bereichs zum Platzieren von Einsätzen
bottom_right_corner = (880, 314)  # Untere rechte Ecke des anklickbaren Bereichs zum Platzieren von Einsätzen

wheel_center = (171, 180)  # Mittelpunkt des Roulettekessels

# Wir verwenden eine Klasse statt alles im globalen Namensraum abzulegen,
# damit wir nicht in jeder Funktion für jede Variable das Schlüsselwort "global" verwenden müssen
class Roulette:
    wheel_rotation_speed = 0.0  # Um wie viel sich wheel_rotation_angle pro Spieltick erhöht
    wheel_rotation_angle = 0.0  # Rotationswinkel des Kessels in Radiant

    ball_rotation_speed = 0.0  # Um wie viel sich ball_rotation_angle pro Spieltick erhöht
    ball_rotation_angle = 0.0  # Polarwinkel der Kugel relativ zum Mittelpunkt des Kessels in Radiant
    ball_distance = 135.0  # Polarabstand der Kugel
    ball_on_number = -1  # Die Zahl, auf die die Kugel gefallen ist; -1 wenn sie noch rollt
    ball_num_bounces = 0  # Anzahl der bisherigen Abpraller der Kugel
    ball_bounce_timestamp = 0  # Zeitpunkt des letzten Abprallers

    in_progress = False

    prev_timestamp = 0

    quit_counter = 0  # Wird erhöht, wenn der Nutzer versucht zu beenden; beendet erst bei == 3
    quit_timestamp = -500  # Wird verwendet, um das Katzenbild auszublenden, wenn während des Drehens beendet werden soll

    last_bet_place_timestamp = 0  # Wird verwendet, um Einsätze beim Gedrückthalten der Maustaste hinzuzufügen

    game_over_timestamp = 0  # Wird verwendet, um den Endbildschirm einzublenden

    win_timestamp = -1500  # Wird verwendet, um den Gewinnbildschirm auszublenden
    lose_timestamp = -1000  # Wird verwendet, um den Text bei Geldverlust rot einzufärben

    bets: dict[str, int] = {}  # Speichert den Einsatzbetrag für jede Position auf dem Tisch
    bank_account = 1000  # Geldbetrag des Spielers
    highscore = 0  # Höchststand; wird nur beim freiwilligen Beenden gespeichert und zur Hälfte als Startkapital beim nächsten Start verwendet

    _xp = 0  # Aktuelle XP
    _xp_interpolate = 0  # Auf der XP-Leiste angezeigte XP; wird für die Animation bei XP-Gewinn verwendet

    def __init__(self):
        pygame.init()
        pygame.font.init()

        self.clock = pygame.time.Clock()

        self.screen = pygame.display.set_mode([1000, 360], 0, 32)  # 1000 Pixel breit, 360 Pixel hoch, keine Flags, 32-bit Farben
        pygame.display.set_caption("Roulette")  # Fenstertitel setzen

        self.font = pygame.font.Font(None, 30)  # Die Standardschriftart mit der Größe 30 laden

        self.table_png = pygame.image.load("assets/table-base.png")
        self.coin_png = pygame.image.load("assets/coin.png")
        self.wheel_png = pygame.image.load("assets/wheel.png")
        self.ball_png = pygame.image.load("assets/ball-img.png")
        self.quit_screen_1_png = pygame.image.load("assets/screens/quit.png")
        self.quit_screen_2_png = pygame.image.load("assets/screens/quit2.png")
        self.quit_screen_3_png = pygame.image.load("assets/screens/quit3.png")
        self.quit_during_game_screen_png = pygame.image.load("assets/screens/quit-during-game.png")
        self.quit_button_png = pygame.image.load("assets/quit-icon.png")

        pygame.display.set_icon(self.ball_png)  # Fenster-Icon festlegen

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
        self.win_screen = self.win_screens[0]  # Wird bei jedem Gewinn zufällig ausgewählt

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

    def quit(self, now: int):
        if self.in_progress:  # Ignorieren, wenn sich das Rad dreht
            self.quit_timestamp = now
            return
        if self.bank_account == 0:  # Ignorieren, wenn das Spiel gleich endet
            return
        if self.quit_counter != 3:  # Ignorieren, solange nicht 3-mal beendet wurde
            self.quit_counter += 1
            return

        self.storeHighscore()  # Höchststand nur speichern, wenn der Spieler freiwillig beendet

        pygame.quit()
        raise SystemExit

    # Getter-Methode für XP; gibt einen zeitlich interpolierten Wert zurück,
    # um die XP-Leiste beim XP-Anstieg zu animieren
    @property
    def xp(self):
        t = max(0.0, min(1.0, (pygame.time.get_ticks() - self.win_timestamp) / 2500))
        if t == 1.0:
            self._xp_interpolate = self._xp
            return self._xp_interpolate
        return self._xp_interpolate + (self._xp - self._xp_interpolate) * (1 - (1 - t) ** 3)

    # Setter-Methode für XP
    @xp.setter
    def xp(self, val):
        self._xp = val

    # Getter-Methode für das Spielerlevel basierend auf den XP
    @property
    def level(self):
        return int(self.xp // 1076)

    # Getter-Methode für den Bonusprozentsatz auf jeden Nettogewinn basierend auf dem Level
    @property
    def bonus_percent(self):
        return int((self.level * 10) ** (1 / 5) * 10)

    # Statische Methode zum Rendern eines Bildes, das um seinen Mittelpunkt rotiert wird
    # Quelle: https://stackoverflow.com/a/54714144 (modifiziert)
    @staticmethod
    def blitRotateCenter(surf: pygame.Surface, image: pygame.Surface, topleft: list[int], angle: float):
        rotated_image = pygame.transform.rotozoom(image, -math.degrees(angle), 1.0)
        new_rect = rotated_image.get_rect(center=image.get_rect(topleft=topleft).center)

        surf.blit(rotated_image, new_rect)

    # Statische Methode zur Abbildung von Radiantwerten in das Intervall [0, 2*PI)
    @staticmethod
    def simplifyAngle(theta: float):
        return theta % (2 * math.pi)

    # Statische Methode zur Berechnung der Differenz zwischen zwei Winkeln in Radiant
    @staticmethod
    def angleDifference(alpha: float, beta: float):
        return Roulette.simplifyAngle(alpha) - Roulette.simplifyAngle(beta)

    # Statische Methode zur Interpolation zwischen zwei Farben a und b;
    # t=0 ergibt a, t=1 ergibt b
    @staticmethod
    def interpolateColor(a: list[int], b: list[int], t: float):
        return [max(min(int(x + (y - x) * t), 255), 0) for x, y in zip(a, b)]

    # Schreibt den Höchststand in eine Datei im AppData-Verzeichnis und gibt den Wert zurück
    def storeHighscore(self):
        highscore = 0

        if sys.platform == "emscripten":
            import platform
            saved_data = platform.window.localStorage.getItem("roulette_highscore")
            if saved_data is not None:
                highscore = int(saved_data)
            if self.bank_account > highscore:
                platform.window.localStorage.setItem("roulette_highscore", str(self.bank_account))
        else:
            data_dir = pathlib.Path(platformdirs.user_data_dir("Roulette"))
            data_dir.mkdir(parents=True, exist_ok=True)
            file = data_dir / "highscore.txt"

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

    # Geld auf den angegebenen Einsatz setzen
    def addBet(self, bet: str):
        amount_to_add = 10  # Standard-Einsatzbetrag
        amount_max = self.bank_account - sum(self.bets.values())  # Verbleibendes Geld zum Setzen

        if bet not in self.bets:  # Das Dictionary ist anfangs leer, daher muss das Schlüssel-Wert-Paar zuerst erstellt werden
            self.bets[bet] = 0
        if self.bets[bet] > 10:  # Wenn bereits Einsätze auf diesem Feld liegen
            amount_to_add = 10 ** math.floor(math.log10(self.bets[bet]))  # Exponentielle Erhöhung
        if amount_to_add > amount_max:  # Wenn der Betrag das verbleibende Geld übersteigt
            amount_to_add = amount_max
        if amount_to_add == 0:  # Wenn kein Geld mehr zum Setzen vorhanden ist
            return

        self.bets[bet] += amount_to_add
        if amount_to_add == amount_max:
            self.place_all_sound.play()  # Spezieller Soundeffekt für All-In
        else:
            random.choice(self.place_bet_sounds).play()

    # Methode zur Verarbeitung des Spielergebnisses
    def processBets(self, now: int):
        prev_amount = self.bank_account

        self.bank_account -= sum(self.bets.values())  # Einsatz vom Kontostand abziehen
        amount_won = 0

        # Alle Einsätze prüfen und Gewinne in amount_won aufsummieren
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

        self.bank_account += amount_won  # Gewinn zum Kontostand hinzufügen

        if self.bank_account > prev_amount:  # Wenn ein Nettogewinn erzielt wurde
            # Bonus wird nur auf den Nettogewinn angerechnet, damit man ihn
            # nicht durch gleichzeitige Gegenwetten ausnutzen kann
            self.bank_account += (self.bank_account - prev_amount) * self.bonus_percent // 100
            self.xp += self.bank_account - prev_amount

            self.win_sound.play()
            self.win_timestamp = now
            self.win_screen = random.choice(self.win_screens)

        elif self.bank_account < prev_amount:  # Wenn ein Nettoverlust entstanden ist
            self.lose_timestamp = now

    # Methode zur Verarbeitung von Fensterereignissen wie Beenden oder Mausklicks
    def processEvents(self, now: int, dt: float):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit(now)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if math.dist(event.pos, [30, 30]) < 20:
                    self.quit(now)
                    return

                if self.quit_counter > 0:
                    self.quit_counter = 0  # Disable the quit screen and go back to the game
                    return
                
                if self.in_progress:  # Keine Interaktion während der Drehung
                    return

                if top_left_corner[0] <= event.pos[0] <= bottom_right_corner[0] and top_left_corner[1] <= event.pos[1] <= bottom_right_corner[1]:  # Hat der Nutzer innerhalb des Einsatzbereichs geklickt?
                    closest_bet = self.getClosestBet(event.pos)

                    if event.button == 1:  # Linke Maustaste
                        self.addBet(closest_bet)
                        self.last_bet_place_timestamp = now + 500

                    elif event.button == 3:  # Rechte Maustaste
                        self.bets[closest_bet] = 0  # Alle Einsätze auf diesem Feld entfernen

                if math.dist(event.pos, wheel_center) < 15:
                    if sum(self.bets.values()) == 0:
                        random.choice(self.place_bets_please_sounds).play()  # Eine Stimme sagt "place your bets please"
                    elif self.ball_distance != 135:
                        self.ball_rotation_speed = 0.0
                        self.ball_rotation_angle = 0.0
                        self.ball_distance = 135
                        self.ball_on_number = -1
                        self.ball_land_sound.play()

            elif event.type == pygame.MOUSEBUTTONUP:
                if not self.in_progress and math.dist(event.pos, wheel_center) < 15 and self.wheel_rotation_speed > 0.2:
                    # Alle Parameter zurücksetzen, das Rad starten und die Kugel rollen lassen
                    self.in_progress = True
                    self.ball_rotation_speed = -random.uniform(0.4, 0.5)
                    self.ball_num_bounces = 0
                    self.wheel_rotate_sound.play()
                    self.ball_land_sound.play()

        if pygame.mouse.get_pressed()[0]:  # Ist die linke Maustaste gedrückt gehalten
            mouse_pos = pygame.mouse.get_pos()
            if (
                now - self.last_bet_place_timestamp > 100  # 100ms Wiederholungsverzögerung
                and top_left_corner[0] <= mouse_pos[0] <= bottom_right_corner[0]
                and top_left_corner[1] <= mouse_pos[1] <= bottom_right_corner[1]
                and not self.in_progress  # Rad steht still?
            ):
                closest_bet = self.getClosestBet(mouse_pos)
                self.addBet(closest_bet)
                self.last_bet_place_timestamp = now

            if math.dist(mouse_pos, wheel_center) < 15 and self.ball_distance == 135 and not self.in_progress:
                if sum(self.bets.values()):  # Hat der Nutzer bereits Einsätze platziert?
                    self.wheel_rotation_speed += 0.004 * dt

    # Methode zum Bewegen der Spielphysik und Erzeugen des Ergebnisses jedes Durchlaufs
    def processPhysics(self, now: int, dt: float):
        self.wheel_rotation_angle += self.wheel_rotation_speed * dt
        self.wheel_rotation_speed *= math.pow(0.99502, dt)  # Rad verlangsamt sich durch Reibung

        if self.in_progress and self.ball_on_number != -1 and self.wheel_rotation_speed < 0.006:  # Ist das Rad zum Stillstand gekommen?
            self.in_progress = False
            self.processBets(now)

        self.ball_rotation_angle += self.ball_rotation_speed * dt
        if self.ball_distance > 100.0:
            self.ball_rotation_speed *= math.pow(0.9901, dt)  # Kugel verlangsamt sich durch Reibung
        elif self.ball_distance > 80.0:
            self.ball_rotation_speed += (self.wheel_rotation_speed - self.ball_rotation_speed) * (1 - math.pow(1 - 0.002, dt))
        elif self.ball_on_number == -1:
            self.ball_rotation_speed += (self.wheel_rotation_speed - self.ball_rotation_speed) * (1 - math.pow(1 - 0.06, dt))

        if self.ball_rotation_speed != 0:
            if self.ball_distance > 75.0:
                self.ball_distance -= 0.25 * dt
            if self.ball_distance <= 80.0:  # Warten, bis die Kugel in das Rad fällt
                # Kugel maximal 3-mal abprallen lassen
                if (
                    now - self.ball_bounce_timestamp > random.randrange(200, 400)
                    and self.ball_num_bounces < 4
                    and abs(self.ball_rotation_speed - self.wheel_rotation_speed) > 0.01
                ):
                    self.ball_rotation_speed = -(self.ball_rotation_speed - self.wheel_rotation_speed) # Kugel abprallen lassen
                    self.ball_bounce_sounds[self.ball_num_bounces].play()
                    self.ball_num_bounces += 1
                    self.ball_bounce_timestamp = now
                    return

                if abs(self.ball_rotation_speed - self.wheel_rotation_speed) > 0.04:  # Kugel erst landen lassen, wenn sie langsam genug ist
                    return

                # Koordinaten der Kugel berechnen
                ball_pos_x = wheel_center[0] + self.ball_distance * math.cos(self.ball_rotation_angle)
                ball_pos_y = wheel_center[1] + self.ball_distance * math.sin(self.ball_rotation_angle)

                closest_num = -1
                smallest_dist = 360.0

                # Zahl auf dem Rad finden, die der Kugel am nächsten liegt
                for num, angle in angles.items():
                    num_pos_x = wheel_center[0] + 100 * math.cos(self.wheel_rotation_angle - math.pi / 2 + (angle * math.pi / 180))
                    num_pos_y = wheel_center[1] + 100 * math.sin(self.wheel_rotation_angle - math.pi / 2 + (angle * math.pi / 180))

                    dist = math.dist([ball_pos_x, ball_pos_y], [num_pos_x, num_pos_y])

                    if dist < smallest_dist:
                        smallest_dist = dist
                        closest_num = num

                delta_angle = self.angleDifference(self.ball_rotation_angle, self.wheel_rotation_angle - math.pi / 2 + (angles[closest_num] * math.pi / 180) )
                if abs(delta_angle) < 0.003 and self.ball_distance < 77.0:  # Ist die Kugel nahe genug am Zentrum der Zahl?
                    self.ball_on_number = closest_num
                    self.ball_rotation_speed = 0.0
                    self.ball_land_sound.play()
                elif abs(delta_angle) < 0.01:
                    self.ball_rotation_speed -= delta_angle * 0.04 * dt

        # Wenn die Kugel auf einer Zahl gelandet ist, bleibt sie daran haften, bis das Rad stoppt
        if self.ball_on_number != -1:
            self.ball_rotation_angle = self.wheel_rotation_angle - math.pi / 2 + (angles[self.ball_on_number] * math.pi / 180)
            self.ball_distance = 75

    def renderTable(self, now: int):
        self.screen.blit(self.table_png, [0, 0])  # Haupt-Roulette-Tisch rendern

        # Rad mit self.wheel_rotation_angle rotieren und rendern
        self.blitRotateCenter(self.screen, self.wheel_png, [sum(x) for x in zip(wheel_center, (-100, -100))], self.wheel_rotation_angle)

        # Koordinaten der Kugel aus ihren Polarkoordinaten berechnen und rendern
        virtual = pygame.Surface((1000 * 3, 360 * 3), pygame.SRCALPHA)
        x = (wheel_center[0] - 7 + self.ball_distance * math.cos(self.ball_rotation_angle)) * 3
        y = (wheel_center[1] - 7 + self.ball_distance * math.sin(self.ball_rotation_angle)) * 3
        virtual.blit(pygame.transform.smoothscale(self.ball_png, (self.ball_png.get_width() * 3, self.ball_png.get_height() * 3)), (x, y))
        self.screen.blit(pygame.transform.smoothscale(virtual, (1000, 360)), (0, 0))

        # Einsatzmünzen und ggf. Text darüber rendern
        for bet, amount in self.bets.items():
            if amount > 0:
                self.screen.blit(self.coin_png, [sum(x) for x in zip(coords[bet], (-27.5, -27.5))])
                if amount > 10:
                    text = shadows.add_shadow(self.font.render(str(amount), True, (255, 255, 255), None), (0, 0), 1.1, 0.2)
                    textSize = text.get_size()
                    self.screen.blit(text, [sum(x) for x in zip(coords[bet], (-textSize[0] / 2, -textSize[1] / 2))])

        # Zeigt den Geldbetrag im Bankkonto an
        color = self.interpolateColor([255, 0, 0], [255, 255, 255], (now - self.lose_timestamp) / 1500)
        text = shadows.add_shadow(self.font.render(f"Bank: ${str(self.bank_account)}", True, color, None), (2, 2), 1.0, 0.2)
        self.screen.blit(text, [340, 12])

        # Zeigt den gesetzten Gesamtbetrag an
        prev_length = text.get_size()[0]  # Versatz basierend auf Textlänge
        text = shadows.add_shadow(self.font.render(f"Amount bet: ${str(sum(self.bets.values()))}", True, [255, 255, 255], None), (2, 2), 1.0, 0.2)
        self.screen.blit(text, [340 + prev_length + 10, 12])

        # Highscore anzeigen
        text = shadows.add_shadow(self.font.render(f"High-score: ${str(self.highscore)}", True, [255, 255, 255], None), (2, 2), 1.0, 0.2)
        self.screen.blit(text, [882 - text.get_size()[0], 12])

        # Levelanzeige und Bonusprozentsatz
        pygame.draw.rect(self.screen, (200, 200, 200), (894, 45, 15, 269))

        remaining_xp = (self.xp / 4) % 269
        pygame.draw.rect(self.screen, (255, 0, 0), (894, 45 + (269 - remaining_xp), 15, remaining_xp))

        text = shadows.add_shadow(self.font.render(f"LVL {self.level}", True, [255, 255, 255], None), (2, 2), 1.0, 0.2)
        self.screen.blit(text, [920, 45])

        text = shadows.add_shadow(self.font.render(f"{self.bonus_percent}%", True, [255, 255, 255], None), (2, 2), 1.0, 0.2)
        self.screen.blit(text, [920, 45 + 274 - text.get_size()[1] * 2])
        text = shadows.add_shadow(self.font.render("Bonus", True, [255, 255, 255], None), (2, 2), 1.0, 0.2)
        self.screen.blit(text, [920, 45 + 274 - text.get_size()[1]])

        # Gewinnbildschirm anzeigen und in 1,5 Sekunden ausblenden
        if now - self.win_timestamp < 1500:
            image = self.win_screen.copy()
            image.set_alpha(255 - int((now - self.win_timestamp) * 255 / 1500))
            self.screen.blit(image, [0, 0])

        # Spezielle bildschirm, wenn der Nutzer während des Drehens versucht zu beenden
        if now - self.quit_timestamp < 500:
            self.quit_during_game_screen_png.set_alpha(255 - int((now - self.quit_timestamp) * 255 / 500))
            self.screen.blit(self.quit_during_game_screen_png, [0, 0])

    async def gameloop(self):
        while True:
            now = pygame.time.get_ticks()  # Millisekunden seit Spielstart

            dt = (now - self.prev_timestamp) / 25.0
            self.prev_timestamp = now

            self.processEvents(now, dt)
            self.processPhysics(now, dt)

            if self.quit_counter > 0:
                match self.quit_counter:  # Quit-Screens anzeigen
                    case 1:
                        self.screen.blit(self.quit_screen_1_png, [0, 0])
                    case 2:
                        self.screen.blit(self.quit_screen_2_png, [0, 0])
                    case 3:
                        self.screen.blit(self.quit_screen_3_png, [0, 0])
            else:
                self.renderTable(now)  # Alles rendern

                if self.bank_account == 0:  # Ist das Spiel vorbei?
                    if self.game_over_timestamp == 0:
                        self.game_over_timestamp = now + 2000  # Wir addieren 2000, damit 2 Sekunden gewartet wird, bevor der Endbildschirm angezeigt wird
                        self.game_over_screen = random.choice(self.end_screens)
                        pygame.mixer.music.fadeout(4000)

                    # Bildschirm für 3 Sekunden einblenden (Fade-In)
                    image = self.game_over_screen.copy()
                    image.set_alpha(int((now - self.game_over_timestamp) * 255 / 3000))
                    self.screen.blit(image, [0, 0])

                    # Spiel 2 + 4 = 6 Sekunden nachdem der Spieler pleite ist beenden
                    if (now - self.game_over_timestamp) > 4000:
                        pygame.quit()
                        raise SystemExit
                    
            self.screen.blit(self.quit_button_png, [10, 10])

            pygame.display.update()  # Aktualisiert den Fensterinhalt

            self.clock.tick(60)  # Spiel auf 60 FPS begrenzen

            await asyncio.sleep(0)

# pygbag erfordert, dass main.py eine asynchrone main()-Funktion enthält und dass diese main-Funktion in jedem Frame "await asyncio.sleep(0)" aufruft

async def main():
    game = Roulette()
    await game.gameloop()

asyncio.run(main())  # Wir brauchen asyncio.run() um asynchrone Funktionen aufzurufen