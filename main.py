# TEE PELI TÄHÄN
from collections import namedtuple
from math import sqrt
import pygame
import random
from enum import Enum, IntFlag, auto
from threading import Thread, Lock

# GameObject on yliluokka kaikille piirrettäville entiteeteille
class GameObject():

    # Esitellään staattiset muuttujat, jotka voidaan ylikirjoittaa aliluokissa
    oletus_grafiikka = pygame.Surface([0, 0])
    nopeus = 0
    DIAGONAL_MOVE_RATIO = sqrt(2) / 2 # Pythagoras auttaa viistottaisessa liikkumisessa
    y_bound = None  # Liikkumis rajoitteet luokan objekteille
    x_bound = None

    @classmethod
    def oletus_leveys(cls):
        return cls.oletus_grafiikka.get_width()

    @classmethod
    def oletus_korkeus(cls):
        return cls.oletus_grafiikka.get_height()

    # Liikkumisraja peliobjektille. 
    # Oletus: None = Ei rajoja
    @classmethod
    def set_bounds(cls, x_bound = None, y_bound = None):
        cls.x_bound = (x_bound - cls.oletus_leveys()) if x_bound is not None else None
        cls.y_bound = (y_bound - cls.oletus_korkeus()) if y_bound is not None else None

    def __init__(self, sijainti):
       
       self.grafiikka = self.oletus_grafiikka
       self.x = sijainti[0] # x ja y kertovat tarkan sijainnin float arvona
       self.y = sijainti[1]
       self.hitbox = self.grafiikka.get_rect().move(sijainti) # hitbox kertaa pyöristetyn sijainnin pixeli tarkkuudella

    # Törmäys laskenta jäteään pygamelle.
    # Törmäys tulee, jos peliobjekti koskettaa toisen keskipistettä
    def collides(self, other):
        return self.hitbox.collidepoint(other.hitbox.center)

    # Yleinen tuki liikkumiselle 8 eri suuntaan (huom. viistot)
    def liiku(self, direction, speed_scale):

        movement = self.nopeus
        
        # Viistottain liikkuessa liikutaan vähemmän x ja y akseleilla Pythogoraan mukaisesti
        if (direction & (Direction.LEFT|Direction.RIGHT) != Direction.NONE and direction & (Direction.UP|Direction.DOWN) != Direction.NONE):
            movement *= self.DIAGONAL_MOVE_RATIO

        # Framet eivät aina tule tasaista tahtia, joten tasoitetaan liikkumista aika kertoimella
        # Syynä voi olla laitteen suorituskyky, joka ei pysy tahdissa, tai jos päivitysväliä muutetaan (esim 60 vs 144)
        movement *= speed_scale

        if (direction & Direction.LEFT) == Direction.LEFT:
            self.x -= movement if self.x_bound is None or self.x >= movement else self.x

        if (direction & Direction.RIGHT) == Direction.RIGHT:
            self.x += movement if (self.x_bound is None or (self.x + movement) <= self.x_bound) else (self.x_bound - self.x)

        if (direction & Direction.UP) == Direction.UP:
            self.y -= movement if self.y_bound is None or self.y >= movement else self.y

        if (direction & Direction.DOWN) == Direction.DOWN:
            self.y += movement if (self.y_bound is None or (self.y + movement) <= self.y_bound) else (self.y_bound - self.y)

        self.hitbox.x = round(self.x) 
        self.hitbox.y = round(self.y)

class Putoava(GameObject):

    y_culling = None

    # Putoavat liikkuvat aina alaspäin
    def liiku(self, speed_scale):
        GameObject.liiku(self, Direction.DOWN, speed_scale)

    def poistunut(self):
        return self.y > self.y_culling


class Kolikko(Putoava):

    oletus_grafiikka = pygame.image.load("kolikko.png")
    nopeus = 60

class Hirvio(Putoava):

    oletus_grafiikka = pygame.image.load("hirvio.png")
    nopeus = 60

class Robo(GameObject):

    oletus_grafiikka = pygame.image.load("robo.png")
    nopeus = 360

# Pelitilanteet. Pelin täytyy aina olla jossain näistä tiloista
class GameState(Enum):
    ALKU = auto()
    PELI_OHI = auto()
    PELI = auto()
    RESET = auto()
    CLOSING = auto()

# Suunnat ja niiden yhdistelmät joihin pelaaja voi liikkua
# Arvoja yhdistellään ja vertaillaan bitwise operaatioilla
class Direction(IntFlag):
    NONE = 0
    LEFT = auto()
    RIGHT = auto()
    UP = auto()
    DOWN = auto()

# Kiinteät värit asioille
class ColorScheme():
    BACKGROUND = pygame.Color(230,230,230)
    TEXT  = pygame.Color(0,0,0)
    STATS = pygame.Color(255,0,0)
    HILIGHTBOX = pygame.Color(200,200,200)


Piirto = namedtuple('Piirto', 'funktio staattinen')
noop = lambda *args, **kwargs: None # lamda funktio, joka ei tee mitään. Joitain pelitiloja ei piirretä lainkaan, tätä käytetään niissä

class Moneyrobot():

    def __init__(self):
        pygame.init()

        self.korkeus = 640
        self.leveys = 640
        self.liikkumisuunta = Direction.NONE

        # Asetetaan rajat peliobjekteille ruudun koon mukaan
        Putoava.y_culling = self.korkeus
        Robo.set_bounds(self.leveys, self.korkeus)

        # Näytön piirtofunktiot pelitilan mukaan. Näin ei tarvita if-else rakennetta piirrossa
        # Toinen parameteri (staattinen) määrittää päivitetäänkö näyttö vain kerran vai koko ajan
        self.piirto_funktiot = {
            GameState.ALKU: Piirto(self.piirra_alku, True),
            GameState.PELI_OHI: Piirto(self.piirra_peli_ohi, True),
            GameState.PELI: Piirto(self.piirra_peli, False),
            GameState.RESET: Piirto(noop, True), # ei piirretä
            GameState.CLOSING: Piirto(noop, True) # ei piirretä
        }
        
        self.naytto = pygame.display.set_mode((self.leveys, self.korkeus))
        self.fontti = pygame.font.SysFont("Cambria", 20)
        pygame.display.set_caption("Moneyrobot")

        pygame.fastevent.init()

        engine_rate = 144.0 # Kuinka monta kertaa sekunnisa pelin tilanne päivitetään
        refresh_rate = 144.0 # Kuinka monta kertaa sekunnissa ruutu päivitetään

        self.engine_rate_ratio = engine_rate / 60.0 # Kerroin jota tulee käyttää arvoihin jotka olettavat, että peliä ajetaan 60fps

        self.reset()

        # Threadit. Logiikka ja piirto ajetaan muissa threadeissa. Eventit käsitellään main loopissa.
        self.logiikka_thread = Thread(name="logiikka", target=self.logiikka, args=[engine_rate])
        self.piirto_thread = Thread(name="piirra_naytto", target=self.piirra_naytto, args=[refresh_rate])
        self.game_state_lock = Lock() # Lukitus mekanismi, jolla estetään mm. entiteettien yhtäaikainen muokkaus ja piirto

        self.silmukka()

    # Asettaa pelin alkutilanteeseen
    def reset(self):

        self.taso = 0
        self.game_state = GameState.ALKU

        robox = int(self.leveys/2-(Robo.oletus_leveys()) / 2) # Robotti aloittaa aina keskeltä
        roboy = int(self.korkeus-100) #Robotti aloittaa aina -100 alareunasta
        self.robo = Robo((robox, roboy))

        self.juoksu = 0

        #putoaviin vihollisiin ja kolikkoihin määritettävät muuttujat
        self.viholliset = []
        self.kolikot = []
        self.keratyt_kolikot = 0

        # pienentämällä saa enemmän putoavia. putoavien_maara määritetty vakioksi 60fps nopeudella. Korjataan arvoa kertoimella, jos fps onkin jotain muuta kuin 60
        self.putoavien_maara = 200 * self.engine_rate_ratio 


    def silmukka(self):

        # Aloita säikeet
        self.piirto_thread.start()
        self.logiikka_thread.start()

        # Tutki tapahtumia, kunnes peli halutaan sulkea
        self.tutki_tapahtumat()

        # Merkitse peli suljettavaksi. Muut threadit odottelevat CLOSING tilaa
        with self.game_state_lock:
            self.game_state = GameState.CLOSING

        # Odota threadien normaalia sulkeutumista
        self.piirto_thread.join()
        self.logiikka_thread.join()

    def piirra_naytto(self, refresh_rate): #Täällä piirretään näytölle tapahtuvat asiat

        nayton_kello = pygame.time.Clock()
        viimeksi_piirretty_tila = GameState.RESET # Tätä käytetään, jotta staattisia näyttöjä ei piirrettäisi uudelleen

        while self.game_state != GameState.CLOSING:

            with self.game_state_lock:

                # Jos staattinen ja kerran jo piirretty, älä piirrä uudelleen
                if not self.piirto_funktiot[self.game_state].staattinen or viimeksi_piirretty_tila != self.game_state:

                    # Kutsutaan pelitilannetta vastaava piirtofunktio
                    self.piirto_funktiot[self.game_state].funktio()

                    pygame.display.flip()
                    self.viimeksi_piirretty_tila = self.game_state

            nayton_kello.tick(refresh_rate)

    def piirra_alku(self):

        self.naytto.fill(ColorScheme.BACKGROUND)
        aloitus_teksti = self.fontti.render("Tervetuloa, ohjaat robottia nuolinäppäimillä.", True, ColorScheme.TEXT)
        aloitus_teksti2 = self.fontti.render("Tavoitteenasi on kerätä mahdollisimman monta kolikkoa.", True, ColorScheme.TEXT)
        aloitus_teksti3 = self.fontti.render("Paina Enter aloittaaksesi", True, ColorScheme.TEXT)
        self.naytto.blit(aloitus_teksti, (20, (self.korkeus/2)))
        self.naytto.blit(aloitus_teksti2, (20, (self.korkeus/2)+20))
        self.naytto.blit(aloitus_teksti3, (20, (self.korkeus/2)+40))
     
    def piirra_peli(self):

        self.naytto.fill(ColorScheme.BACKGROUND)

        for kolikko in self.kolikot: #Piirretään kolikot
            self.naytto.blit(kolikko.grafiikka, kolikko.hitbox)

        for vihu in self.viholliset: #Piirretään vihut
            self.naytto.blit(vihu.grafiikka, vihu.hitbox)

        teksti = self.fontti.render("Taso: " + str(self.taso), True, ColorScheme.STATS)
        self.naytto.blit(teksti, (550, 10))

        teksti = self.fontti.render("Kerätyt kolikot: " +str(self.keratyt_kolikot), True, ColorScheme.STATS)
        self.naytto.blit(teksti, (10, 10))

        self.naytto.blit(self.robo.grafiikka, self.robo.hitbox)

    def piirra_peli_ohi(self):

        pygame.draw.rect(self.naytto, ColorScheme.HILIGHTBOX, (30, 300, 390, 100))
        pygame.draw.rect(self.naytto, ColorScheme.BACKGROUND, (40, 310, 370, 80))
        if self.keratyt_kolikot == 1:
            teksti = self.fontti.render("Peli ohi, sait kerättyä " +str(self.keratyt_kolikot) + ":n kolikon", True, ColorScheme.TEXT)
            teksti2 = self.fontti.render("Uusi peli paina F2, poistu painamalla ESC", True, ColorScheme.TEXT)
        else:
            teksti = self.fontti.render("Peli ohi, sait kerättyä " +str(self.keratyt_kolikot) + " kolikkoa", True, ColorScheme.TEXT)
            teksti2 = self.fontti.render("Uusi peli paina F2, poistu painamalla ESC", True, ColorScheme.TEXT)
        self.naytto.blit(teksti, (50, self.korkeus/2))
        self.naytto.blit(teksti2, (50, ((self.korkeus/2)+30)))
    
    def tutki_tapahtumat(self):

        tapahtuma = pygame.event.Event(pygame.NOEVENT)
        while tapahtuma.type != pygame.QUIT:

            tapahtuma = pygame.fastevent.wait() # odottele eventiä loputtomasti

            with self.game_state_lock:
                if tapahtuma.type == pygame.KEYDOWN:
                    if tapahtuma.key == pygame.K_LEFT:
                        self.liikkumisuunta |= Direction.LEFT
                    if tapahtuma.key == pygame.K_RIGHT:
                        self.liikkumisuunta |= Direction.RIGHT
                    if tapahtuma.key == pygame.K_UP:
                        self.liikkumisuunta |= Direction.UP
                    if tapahtuma.key == pygame.K_DOWN:
                        self.liikkumisuunta |= Direction.DOWN
            
                if tapahtuma.type == pygame.KEYUP:
                    if tapahtuma.key == pygame.K_LEFT:
                        self.liikkumisuunta &= ~Direction.LEFT
                    if tapahtuma.key == pygame.K_RIGHT:
                        self.liikkumisuunta &= ~Direction.RIGHT
                    if tapahtuma.key == pygame.K_UP:
                        self.liikkumisuunta &= ~Direction.UP
                    if tapahtuma.key == pygame.K_DOWN:
                        self.liikkumisuunta &= ~Direction.DOWN

                    if tapahtuma.key == pygame.K_ESCAPE:
                        break   # poistu while loopista
                    if tapahtuma.key == pygame.K_F2:
                        self.game_state = GameState.RESET

                    if tapahtuma.key == pygame.K_RETURN and self.game_state == GameState.ALKU:
                        self.game_state = GameState.PELI


    def paivita_tila(self, speed_scale): #arvotaan hirviöitä ja kolikoita random funktiolla sekä määritetään vaikeustaso

        self.robo.liiku(self.liikkumisuunta, speed_scale) #Robotin liikkuminen 
        
        for i in range(len(self.kolikot) -1, -1, -1): #Liikutetaan kolikoita ja määritetään osumat robotin kanssa
            # Käydään lista läpi takaperin (aloittaen lopusta), jotta ruudulta poistuvat elementit voidaan poistaa samalla

            self.kolikot[i].liiku(speed_scale)

            if self.robo.collides(self.kolikot[i]):
                del self.kolikot[i]
                self.keratyt_kolikot += 1 
                self.juoksu = 0

            # Poista viholliset jotka ovat poistuneet ruudulta
            elif self.kolikot[i].poistunut():
                del self.kolikot[i]


        for i in range(len(self.viholliset) -1, -1, -1): #Liikutetaan vihollisia ja määritetään osumat robotin kanssa

            self.viholliset[i].liiku(speed_scale)

            if self.robo.collides(self.viholliset[i]):
                self.game_state = GameState.PELI_OHI
                return

            # Poista viholliset jotka ovat poistuneet ruudulta
            if self.viholliset[i].poistunut():
                del self.viholliset[i]

        arvotaanko = random.uniform(0, self.putoavien_maara)
        
        if self.keratyt_kolikot % 10 == 0 and self.keratyt_kolikot != 0 and self.juoksu == 0: #Vaikeustason määritys
            Hirvio.nopeus += 1
            Kolikko.nopeus += 1
            self.taso += 1
            self.juoksu += 1

            if self.taso == 5:
                self.putoavien_maara = 150 * self.engine_rate_ratio # putoavien_maara määritetty vakioksi 60fps nopeudella. Korjataan arvoa kertoimella, jos fps onkin jotain muuta kuin 60
            if self.taso == 10:
                self.putoavien_maara = 100 * self.engine_rate_ratio
            if self.taso == 15:
                self.putoavien_maara = 50 * self.engine_rate_ratio
        
        # Lisätään vihollisia ja kolikoita
        if arvotaanko >= 1 and arvotaanko < 4:
            sijanti = random.randint(0, self.leveys - Hirvio.oletus_leveys()), -100
            self.viholliset.append(Hirvio(sijanti))
        
        if arvotaanko >= 2 and arvotaanko < 5:
            sijanti = random.randint(0, self.leveys - Kolikko.oletus_leveys()), -100
            self.kolikot.append(Kolikko(sijanti))


    def logiikka(self, engine_rate):

        logiikka_kello = pygame.time.Clock()

        while self.game_state != GameState.CLOSING:

            # speed_scale on kerroin ruudulla liikkuville entiteeteille. 
            # Kaikki liikkumiset tulisi kertoa tällä, jotta liike näyttää vakiolta, vaikka enginen framerate ei ole
            speed_scale = logiikka_kello.tick(engine_rate) * 0.001

            # lukitse pelitila, jotta piirto funktio ei voi piirtää keskeneräistä tilannetta
            with self.game_state_lock:

                # Resetoi peli...
                if self.game_state == GameState.RESET:
                    self.reset()

                # ... Tai päivitä pelin tila, jos ollaan pelaamassa
                elif self.game_state == GameState.PELI:
                    self.paivita_tila(speed_scale)

if __name__ == "__main__":
    Moneyrobot()
