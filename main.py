# TEE PELI TÄHÄN
import pygame
import random

class Moneyrobot():

    def __init__(self):
        pygame.init()
        self.lataa_kuvat()
        self.taso = 0
        self.kolikot = 0
        self.korkeus = 640
        self.leveys = 640
        self.peli_ohi = False
        self.kello = pygame.time.Clock()
        self.vasemmalle = False
        self.oikealle = False
        self.robox = int(self.leveys/2-(self.robo.get_width()/2)) # Robotti aloittaa aina keskeltä
        self.roboy = int(self.korkeus-100) #Robotti aloittaa aina -100 alareunasta
        self.juoksu = 0 #vaikeustason määritykseen apumuuttuja
        self.putoavat()
        self.alku = True

        self.naytto = pygame.display.set_mode((self.leveys, self.korkeus))
        self.fontti = pygame.font.SysFont("Cambria", 20)
        pygame.display.set_caption("Moneyrobot")

        self.silmukka()

    def lataa_kuvat(self):
        self.hirvio = pygame.image.load("hirvio.png")
        self.kolikko = pygame.image.load("kolikko.png")
        self.robo = pygame.image.load("robo.png")

    def putoavat(self): #täällä on putoaviin vihollisiin ja kolikkoihin määritettävät muuttujat
        self.viholliset = []
        self.kolikot = []
        self.vihumaara = 0
        self.kolikkomaara = 0
        self.keratyt_kolikot = 0
        self.vihuy = []
        self.vihux = []
        self.kolikkox = []
        self.kolikkoy = []
        self.putoavan_nopeus = 1 
        self.putoavien_maara = 200 #tätä pienentämällä saa enemmän putoavia 

    def silmukka(self):
        while True:
            self.aloitus()
            self.tutki_tapahtumat()
            self.piirra_naytto()
            self.arvonta()
    
    def aloitus(self):
        while self.alku:
            self.naytto.fill((230,230,230))
            aloitus_teksti = self.fontti.render("Tervetuloa, ohjaat robottia nuolinäppäimillä.", True, (0,0,0))
            aloitus_teksti2 = self.fontti.render("Tavoitteenasi on kerätä mahdollisimman monta kolikkoa.", True, (0,0,0))
            aloitus_teksti3 = self.fontti.render("Paina Enter aloittaaksesi", True, (0,0,0))
            self.naytto.blit(aloitus_teksti, (20, (self.korkeus/2)))
            self.naytto.blit(aloitus_teksti2, (20, (self.korkeus/2)+20))
            self.naytto.blit(aloitus_teksti3, (20, (self.korkeus/2)+40))
            pygame.display.flip()
            self.tutki_tapahtumat()

    def piirra_naytto(self): #Täällä piirretään näytölle tapahtuvat asiat

        self.naytto.fill((230,230,230))

        for i in range (0, self.kolikkomaara): #Liikutetaan kolikoita ja määritetään osumat robotin kanssa
            kolikon_keskipiste_x = self.kolikkox[i]+(self.kolikot[i].get_width()/2)
            kolikon_keskipiste_y = self.kolikkoy[i]+(self.kolikot[i].get_height()/2)

            if self.kolikkoy[i] <= self.korkeus+100:
                self.kolikkoy[i] += self.putoavan_nopeus
                self.naytto.blit(self.kolikot[i], (self.kolikkox[i], self.kolikkoy[i]))

            if self.robox <= kolikon_keskipiste_x and self.robox+self.robo.get_width() >= kolikon_keskipiste_x and self.roboy <= kolikon_keskipiste_y and self.roboy+self.robo.get_height() >= kolikon_keskipiste_y:
                self.kolikkoy[i]+=400
                self.keratyt_kolikot += 1 
                self.juoksu = 0


        for i in range (0, self.vihumaara): #Liikutetaan vihollisia ja määritetään osumat robotin kanssa
            vihun_keskipiste_x = self.vihux[i]+(self.viholliset[i].get_width()/2)
            vihun_keskipiste_y = self.vihuy[i]+(self.viholliset[i].get_height()/2)

            if self.vihuy[i] <= self.korkeus+100:
                self.vihuy[i] += self.putoavan_nopeus
                self.naytto.blit(self.viholliset[i], (self.vihux[i], self.vihuy[i]))

            if self.robox <= vihun_keskipiste_x and self.robox+self.robo.get_width() >= vihun_keskipiste_x and self.roboy <= vihun_keskipiste_y and self.roboy+self.robo.get_height() >= vihun_keskipiste_y:
                self.peli_ohi = True

        if self.peli_ohi: #Pysäytetään animaatiot ja ilmoitetaan pelin loppuminen
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
            pygame.display.flip()
            while True:
                self.tutki_tapahtumat()

        teksti = self.fontti.render("Taso: " + str(self.taso), True, (255, 0 ,0))
        self.naytto.blit(teksti, (550, 10))

        teksti = self.fontti.render("Kerätyt kolikot: " +str(self.keratyt_kolikot), True, (255,0,0))
        self.naytto.blit(teksti, (10, 10))

        self.naytto.blit(self.robo, (self.robox, self.roboy))
        pygame.display.flip()
        self.kello.tick(60)
    
    def tutki_tapahtumat(self):
        for tapahtuma in pygame.event.get():

            if tapahtuma.type == pygame.KEYDOWN:
                if tapahtuma.key == pygame.K_LEFT:
                    self.vasemmalle = True
                if tapahtuma.key == pygame.K_RIGHT:
                    self.oikealle = True
            
            if tapahtuma.type == pygame.KEYUP:
                if tapahtuma.key == pygame.K_LEFT:
                    self.vasemmalle = False
                if tapahtuma.key == pygame.K_RIGHT:
                    self.oikealle = False

                if tapahtuma.key == pygame.K_ESCAPE:
                    exit()
                if tapahtuma.key == pygame.K_F2:
                    Moneyrobot()

                if tapahtuma.key == pygame.K_RETURN:
                    self.alku = False

            if tapahtuma.type == pygame.QUIT:
                exit()

        self.nopeus = 6 #Robotin nopeus

        if self.robox >= self.nopeus:  #Robotin liikkuminen 
            if self.vasemmalle:
                self.robox -= self.nopeus
        if self.robox+self.robo.get_width() <= (self.leveys - self.nopeus):        
            if self.oikealle: 
                self.robox += self.nopeus

    def arvonta(self): #arvotaan hirviöitä ja kolikoita random funktiolla sekä määritetään vaikeustaso
        arvotaanko = random.randint(0, self.putoavien_maara)
        
        if self.keratyt_kolikot % 10 == 0 and self.keratyt_kolikot != 0 and self.juoksu == 0: #Vaikeustason määritys
            self.putoavan_nopeus += 1
            self.taso += 1
            self.juoksu += 1

            if self.taso == 5:
                self.putoavien_maara = 150
            if self.taso == 10:
                self.putoavien_maara = 100
            if self.taso == 15:
                self.putoavien_maara == 50

        if arvotaanko in range (1, 4):
            self.viholliset.append(self.hirvio)
            self.vihux.append(random.randint(0, self.leveys-self.hirvio.get_width()))
            self.vihuy.append(-100)
            self.vihumaara += 1
        
        if arvotaanko in range (2, 5):
            self.kolikot.append(self.kolikko)
            self.kolikkox.append(random.randint(0, self.leveys-self.hirvio.get_width()))
            self.kolikkoy.append(-100)
            self.kolikkomaara += 1

if __name__ == "__main__":
    Moneyrobot()
