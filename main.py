# TEE PELI TÄHÄN
from collections import namedtuple
import pygame
import random
from enum import Enum, IntFlag, auto

# GameObject on yliluokka kaikille piirrettäville entiteeteille
class GameObject():

    # Esitellään staattiset muuttujat, jotka ylikirjoitetaan aliluokissa
    oletus_grafiikka = pygame.Surface([0, 0])
    nopeus = 0

    @classmethod
    def oletus_leveys(cls):
        return cls.oletus_grafiikka.get_width()

    def __init__(self, sijainti, custom_grafiikka = None):
       
       self.grafiikka = self.oletus_grafiikka if custom_grafiikka is None else custom_grafiikka
       self.hitbox = self.grafiikka.get_rect().move(sijainti)

    def collides(self, other):
        return self.hitbox.collidepoint(other.hitbox.center)

    def liiku(self):
        pass

class Putoava(GameObject):

    def liiku(self):
        self.hitbox.y += self.nopeus

class Kolikko(Putoava):

    oletus_grafiikka = pygame.image.load("kolikko.png")
    nopeus = 1

class Hirvio(Putoava):

    oletus_grafiikka = pygame.image.load("hirvio.png")
    nopeus = 1

class Robo(GameObject):

    oletus_grafiikka = pygame.image.load("robo.png")
    nopeus = 6

    def liiku(self, direction, leveys_raja):

        if (direction & Direction.LEFT) == Direction.LEFT:
            if self.hitbox.x >= self.nopeus:
                self.hitbox.x -= self.nopeus

        if (direction & Direction.RIGHT) == Direction.RIGHT:
            if self.hitbox.x + self.grafiikka.get_width() <= (leveys_raja - self.nopeus):        
                self.hitbox.x += self.nopeus

# Pelitilanteet. Pelin täytyy aina olla jossain näistä tiloista
class GameState(Enum):
    ALKU = 1
    PELI_OHI = 2
    PELI = 3
    RESET = 4

# Suunnat ja niiden yhdistelmät joihin pelaaja voi liikkua
# Arvoja yhdistellään ja vertaillaan bitwise operaatioilla
class Direction(IntFlag):
    LEFT = auto()
    RIGHT = auto()
    NONE = auto()

Piirto = namedtuple('Piirto', 'funktio staattinen')

class Moneyrobot():

    def __init__(self):
        pygame.init()

        self.korkeus = 640
        self.leveys = 640
        self.liikkumisuunta = Direction.NONE
        self.viimeksi_piirretty_tila = GameState.RESET # Tätä käytetään, jotta staattisia näyttöjä ei piirrettäisi uudelleen

        # Näytön piirtofunktiot pelitilan mukaan. Näin ei tarvita if-else rakennetta piirrossa
        # Toinen parameteri (staattinen) määrittää päivitetäänkö näyttö vain kerran vai koko ajan
        self.piirto_funktiot = {
            GameState.ALKU: Piirto(self.piirra_alku, True),
            GameState.PELI_OHI: Piirto(self.piirra_peli_ohi, True),
            GameState.PELI: Piirto(self.piirra_peli, False)
        }

        self.kello = pygame.time.Clock()
        
        self.naytto = pygame.display.set_mode((self.leveys, self.korkeus))
        self.fontti = pygame.font.SysFont("Cambria", 20)
        pygame.display.set_caption("Moneyrobot")

        self.reset()

        self.silmukka()

    # Asettaa pelin alkutilanteeseen
    def reset(self):

        self.taso = 0
        self.game_state = GameState.ALKU

        robox = int(self.leveys/2-(Robo.oletus_leveys()) / 2) # Robotti aloittaa aina keskeltä
        roboy = int(self.korkeus-100) #Robotti aloittaa aina -100 alareunasta
        self.robo = Robo((robox, roboy))

        self.juoksu = 0 #vaikeustason määritykseen apumuuttuja

        #putoaviin vihollisiin ja kolikkoihin määritettävät muuttujat
        self.viholliset = []
        self.kolikot = []
        self.keratyt_kolikot = 0
        self.putoavien_maara = 200 #tätä pienentämällä saa enemmän putoavia 


    def silmukka(self):
        while True:

            self.piirra_naytto()
            
            self.tutki_tapahtumat()

            if self.game_state == GameState.PELI:
                self.logiikka()

            elif self.game_state == GameState.RESET:
                self.reset()

            self.kello.tick(60)

    def piirra_naytto(self): #Täällä piirretään näytölle tapahtuvat asiat

        # Jos staattinen ja kerran jo piirretty, älä piirrä uudelleen
        if self.piirto_funktiot[self.game_state].staattinen and self.viimeksi_piirretty_tila == self.game_state:
            return

        # Kutsutaan pelitilannetta vastaava piirtofunktio
        self.piirto_funktiot[self.game_state].funktio()

        pygame.display.flip()
        self.viimeksi_piirretty_tila = self.game_state

    def piirra_alku(self):

        self.naytto.fill((230,230,230))
        aloitus_teksti = self.fontti.render("Tervetuloa, ohjaat robottia nuolinäppäimillä.", True, (0,0,0))
        aloitus_teksti2 = self.fontti.render("Tavoitteenasi on kerätä mahdollisimman monta kolikkoa.", True, (0,0,0))
        aloitus_teksti3 = self.fontti.render("Paina Enter aloittaaksesi", True, (0,0,0))
        self.naytto.blit(aloitus_teksti, (20, (self.korkeus/2)))
        self.naytto.blit(aloitus_teksti2, (20, (self.korkeus/2)+20))
        self.naytto.blit(aloitus_teksti3, (20, (self.korkeus/2)+40))
     
    def piirra_peli(self):

        self.naytto.fill((230,230,230))

        for kolikko in self.kolikot: #Piirretään kolikot
            self.naytto.blit(kolikko.grafiikka, kolikko.hitbox)

        for vihu in self.viholliset: #Piirretään vihut
                self.naytto.blit(vihu.grafiikka, vihu.hitbox)

        teksti = self.fontti.render("Taso: " + str(self.taso), True, (255, 0 ,0))
        self.naytto.blit(teksti, (550, 10))

        teksti = self.fontti.render("Kerätyt kolikot: " +str(self.keratyt_kolikot), True, (255,0,0))
        self.naytto.blit(teksti, (10, 10))

        self.naytto.blit(self.robo.grafiikka, self.robo.hitbox)

    def piirra_peli_ohi(self):

        pygame.draw.rect(self.naytto, (200,200,200), (30, 300, 390, 100))
        pygame.draw.rect(self.naytto, (230,230,230), (40, 310, 370, 80))
        if self.keratyt_kolikot == 1:
            teksti = self.fontti.render("Peli ohi, sait kerättyä " +str(self.keratyt_kolikot) + ":n kolikon", True, (0,0,0))
            teksti2 = self.fontti.render("Uusi peli paina F2, poistu painamalla ESC", True, (0,0,0))
        else:
            teksti = self.fontti.render("Peli ohi, sait kerättyä " +str(self.keratyt_kolikot) + " kolikkoa", True, (0,0,0))
            teksti2 = self.fontti.render("Uusi peli paina F2, poistu painamalla ESC", True, (0,0,0))
        self.naytto.blit(teksti, (50, self.korkeus/2))
        self.naytto.blit(teksti2, (50, ((self.korkeus/2)+30)))
    
    def tutki_tapahtumat(self):
        for tapahtuma in pygame.event.get():

            if tapahtuma.type == pygame.KEYDOWN:
                if tapahtuma.key == pygame.K_LEFT:
                    self.liikkumisuunta |= Direction.LEFT
                if tapahtuma.key == pygame.K_RIGHT:
                    self.liikkumisuunta |= Direction.RIGHT
            
            if tapahtuma.type == pygame.KEYUP:
                if tapahtuma.key == pygame.K_LEFT:
                    self.liikkumisuunta &= ~Direction.LEFT
                if tapahtuma.key == pygame.K_RIGHT:
                    self.liikkumisuunta &= ~Direction.RIGHT

                if tapahtuma.key == pygame.K_ESCAPE:
                    exit()
                if tapahtuma.key == pygame.K_F2:
                    self.game_state = GameState.RESET

                if tapahtuma.key == pygame.K_RETURN:
                    self.game_state = GameState.PELI

            if tapahtuma.type == pygame.QUIT:
                exit()


    def logiikka(self): #arvotaan hirviöitä ja kolikoita random funktiolla sekä määritetään vaikeustaso


        self.robo.liiku(self.liikkumisuunta, self.leveys) #Robotin liikkuminen 
        
        for i in range(len(self.kolikot) -1, -1, -1): #Liikutetaan kolikoita ja määritetään osumat robotin kanssa
            # Käydään lista läpi takaperin (aloittaen lopusta), jotta ruudulta poistuvat elementit voidaan poistaa samalla

            self.kolikot[i].liiku()

            if self.robo.collides(self.kolikot[i]):
                del self.kolikot[i]
                self.keratyt_kolikot += 1 
                self.juoksu = 0

            # Poista viholliset jotka ovat poistuneet ruudulta
            elif self.kolikot[i].hitbox.y > self.korkeus+100:
                del self.kolikot[i]


        for i in range(len(self.viholliset) -1, -1, -1): #Liikutetaan vihollisia ja määritetään osumat robotin kanssa

            self.viholliset[i].liiku()

            if self.robo.collides(self.viholliset[i]):
                self.game_state = GameState.PELI_OHI
                return

            # Poista viholliset jotka ovat poistuneet ruudulta
            if self.viholliset[i].hitbox.y > self.korkeus+100:
                del self.viholliset[i]

        arvotaanko = random.randint(0, self.putoavien_maara)
        
        if self.keratyt_kolikot % 10 == 0 and self.keratyt_kolikot != 0 and self.juoksu == 0: #Vaikeustason määritys
            Hirvio.nopeus += 1
            Kolikko.nopeus += 1
            self.taso += 1
            self.juoksu += 1

            if self.taso == 5:
                self.putoavien_maara = 150
            if self.taso == 10:
                self.putoavien_maara = 100
            if self.taso == 15:
                self.putoavien_maara == 50
        
        # Lisätään vihollisia ja kolikoita
        if arvotaanko in range (1, 4):
            self.viholliset.append(Hirvio((random.randint(0, self.leveys - Hirvio.oletus_leveys()), -100)))
        
        if arvotaanko in range (2, 5):
            self.kolikot.append(Kolikko((random.randint(0, self.leveys - Kolikko.oletus_leveys()), -100)))

if __name__ == "__main__":
    Moneyrobot()
