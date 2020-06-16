import pygame
import random
import os
import time
import pickle
import neat
import sys
import time
from pygame.locals import*

pygame.font.init()

#Window dimensions
win_width = 1000
win_height = 600

#Set the window and display
WIN = pygame.display.set_mode((win_width,win_height))
pygame.display.set_caption("T-Rex Dino Run AI")

#Load all the images
bg = pygame.transform.scale(pygame.image.load(os.path.join("imgs","background(3).png")).convert_alpha(), (1000, 600))
dino_run = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","dino" + str(x) + ".png"))) for x in range(3,5)]
dino_duck = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","dino" + str(x) + ".png"))) for x in range(5,7)]
dino_jump = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","dino1.png")).convert_alpha())
dino_dead = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","dino7.png")).convert_alpha())
crow_imgs = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","crow" + str(x) + ".png"))) for x in range(1,3)]
cactus_imgs = [pygame.transform.scale(pygame.image.load(os.path.join("imgs","cactus" + str(x) + ".png")).convert_alpha(),(54,80)) for x in range(1,6)]
base_img = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","ground.png")).convert_alpha())

GEN = 0 #Current generation

#Variables to move the background
bgX = 0
bgX2 = bg.get_width()

#For jump mechanism
gravity = 0.6


class Dino(object):
    RUN_IMGS = dino_run
    DUCK_IMGS = dino_duck
    JUMP_IMG = dino_jump
    DEAD_IMGS = dino_dead
    ANIMATION_TIME = 5

    def __init__(self,x,y):
        self.x=x #Starting position
        self.y=y #Starting postion
        self.height = 0
        self.score = 0
        self.img_count = 0 #Choose which image to display
        self.img = self.RUN_IMGS[0]
        self.isDucking = False
        self.isJumping = False
        self.jumpCount = 10
        self.jumpSpeed = 11.5
        self.duckCount = 0
        self.runCount = 0
        self.tick_count = 0 #Jumping and falling of dino
        self.vel = 0 #Start at 0 because dino is not moving
        
    def duck(self):
        self.isDucking = True

    def jump(self):
        # to avoid double jump when in air
        if self.isJumping:
            return
        # reseting tick_count (time) = 0 to denote the instant at which the jump occured
        self.tick_count = 0
        # the velocity with which the t-rex moves up when it jumps
        # NOTE vel is negative cause the top left corner of the pygame window is (0, 0)
        self.vel = -9
        
    #Make sure that the dinos come down after jumping and don't stay stuck in the air
    def move(self):
        # increasing time as move occured every "second" or tick
        self.tick_count += 1

        # s = u * t + 0.5 * a * t^2
        displacement = self.vel * self.tick_count + 0.5 * 1.5 * (self.tick_count**2)
        
        # limits the displacement in the downward direction to a max displacement value
        if displacement >= 16:
            displacement = 16
        
        # limits the displacement in the upward direction to a max displacement value
        if displacement < 0:
            displacement -= 2

        self.y += displacement
        
        if self.y > 350:
            self.isJumping = False
            self.y = 350
        else:
            self.isJumping = True

    def draw(self,win):
        #Animation for dino jump
        if self.isJumping:
            self.jump()
            win.blit(self.JUMP_IMG,(self.x,self.y))
        #Animation for dino duck
        elif self.isDucking:
            if self.duckCount >= 4:
                self.duckCount = 0
            win.blit(self.DUCK_IMGS[self.duckCount//2],(self.x,self.y+20))
            self.isDucking = False
            self.duckCount += 1
        #Animation for dino run
        else:
            if self.runCount >= 4:
                self.runCount = 0
            win.blit(self.RUN_IMGS[self.runCount//2],(self.x,self.y))
            self.runCount +=1

    #For collision detection
    def get_mask(self):
        return pygame.mask.from_surface(self.img)

class Cactus(object):
    images = cactus_imgs
    VEL = 10

    def __init__(self,x,y):
        self.x=x
        self.y=y
        self.cactus_image = self.images[random.randrange(0,5)]
        self.passed = False #Check if dino passes the cactus

    def __iter__(self):
        return self

    def move(self):
        self.x -= self.VEL

    def draw(self,win):
        win.blit(self.cactus_image,(self.x,self.y))

    def collide(self,dino):
        #Get dino's mask
        dino_mask = dino.get_mask()
        #Get cactus's mask
        cactus_mask = pygame.mask.from_surface(self.cactus_image)
        #Calculate the pixel positions
        cactus_offset = (self.x - dino.x, self.y - round(dino.y))
        #If the pixels of both cactus and dino overlap, then they have collided
        cactus_point = dino_mask.overlap(cactus_mask,cactus_offset)

        if cactus_point:
            return True
        return False

class Crow(object):
    IMGS = crow_imgs
    VEL = 13

    def __init__(self,x,y):
        self.x=x
        self.y=y
        self.height=0
        self.passed=False
        self.vel=0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[random.randrange(0,2)]
        self.set_height()

    def __iter__(self):
        return self

    def set_height(self):
        self.height=random.randrange(150,350)

    def move(self):
        self.x -= self.VEL

    #Animate the crow flying
    def draw(self,win):
        if self.img_count >= 4:
            self.img_count = 0
        win.blit(self.IMGS[self.img_count//2],(self.x,self.height))
        self.img_count += 1

    def collide(self,dino):
        dino_mask = dino.get_mask()
        crow_mask = pygame.mask.from_surface(self.img)
        crow_offset = (self.x - dino.x, self.height - round(dino.y))
        crow_point = dino_mask.overlap(crow_mask,crow_offset)

        if crow_point:
            return True
        return False

class Base:
    VEL = 10
    WIDTH = base_img.get_width()
    IMG = base_img

    def __init__(self,y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL
        
        #When the background goes offscreen, attach the starting position to
        #the end position to give it an effect of movement
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    #Animate the background by blitting both the coordinates
    def draw(self,win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))

#Draw windows for main game loop
def draw_window(win, dinos, cactuses, crows, base):
    win.blit(bg,(bgX,0))
    win.blit(bg,(bgX2,0))

    for cactus in cactuses:
        cactus.draw(win)

    for crow in crows:
        crow.draw(win)

    base.draw(win)

    for dino in dinos:
        dino.draw(win)
        
    pygame.display.update()

def main():
    win = pygame.display.set_mode((win_width,win_height))
    clock = pygame.time.Clock()

    dino = Dino(100,350)
    base = Base(410)
    cactuses = [Cactus(1010,350)]
    crows = [Crow(2000,550)]

    score = 0

    #Setting timer events
    pygame.time.set_timer(USEREVENT+1,25000)
    pygame.time.set_timer(USEREVENT+2,random.randrange(1000,1300))
    pygame.time.set_timer(USEREVENT+3,random.randrange(3000,3500))
    speed = 30

    global bgX, bgX2

    run = True
    while run:
        
        clock.tick(speed)
        for event in pygame.event.get():
            #Quit the game if the user clicks on the 'x' buttom
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                break
            #Increase the speed after every 25 seconds when userevent 1 is triggered
            if event.type == USEREVENT+1:
                    speed += 1
            #Trigger userevent 2 every 1 to 1.3
            if event.type == USEREVENT+2:
                #If r = 0 spawn the cactus
                r = random.randrange(0,2)
                if r == 0:
                    cactuses.append(Cactus(1010,350))
            #Trigger userevent 3 every 3 to 3.5 seconds
            if event.type == USEREVENT+3:
                #If r2 = 0 spawn a crow
                r2 = random.randrange(0,3)
                if r2 == 0:
                    crows.append(Crow(2000,550))
        
        dino.move()
        
        #Set keys to move the dino to go up or down
        #Not necessary when AI is going to play the game
        keys = pygame.key.get_pressed()

        if keys[pygame.K_SPACE] or keys[pygame.K_UP]:
           dino.isJumping = True
           if not(dino.isJumping):
                dino.isJumping = True

        if keys[pygame.K_DOWN]:
            if not(dino.isDucking):
                dino.isDucking = True

        #Move the background
        bgX -= 1.4
        bgX2 -= 1.4

        if bgX < bg.get_width() * -1:
            bgX = bg.get_width()
        if bgX2 < bg.get_width() * -1:
            bgX2 = bg.get_width()

        rem = [] #List to store removed cactuses
        add_cactus = False
        for cactus in cactuses:
            #Check if dino collides the cactus
            if cactus.collide(dino):
                run = False
            #Check if cactus goes off-screen, and remove if does
            if cactus.x + cactus.cactus_image.get_width() < 0:
                rem.append(cactus)
            #Check if dino passes the cactus
            if not cactus.passed and cactus.x < dino.x:
                cactus.passed = True
                add_cactus = True
                
            cactus.move()

        if add_cactus:
            score += 1

        for r in rem:
            cactuses.remove(r)

        rem_crow = [] #List to store removed crows
        add_crow = False
        for crow in crows:
            if crow.collide(dino):
                run = False
    
            if crow.x + crow.img.get_width() < 0:
                rem_crow.append(crow)
                
            if not crow.passed and crow.x < dino.x:
                crow.passed = True
                add_crow = True

            crow.move()

        if add_crow:
            score += 1

        for r in rem_crow:
            crows.remove(r)

        draw_window(win,[dino],cactuses,crows,base)

    pygame.time.wait(2000)
    pygame.quit()
    quit()

#Fuction for AI
def eval_genome(genomes,config):

    #Runs the simulation of the current population of dinoss and sets their fitness
    #based on the distance they reach in the game.
    
    global GEN
    GEN += 1
    
    nets = [] #List to store neural network associated with the genome
    ge = [] #List to store the genome
    dinos = [] #Dino object that uses NN to play

    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g,config)
        nets.append(net)
        dinos.append(Dino(100,350))
        g.fitness = 0
        ge.append(g)

    win = pygame.display.set_mode((win_width,win_height))
    clock = pygame.time.Clock()

    base = Base(410)
    cactuses = [Cactus(1010,350)]
    crows = [Crow(2000,550)]
    score = 0

    pygame.time.set_timer(USEREVENT+1,60000)
    pygame.time.set_timer(USEREVENT+2,random.randrange(1000,1300))
    pygame.time.set_timer(USEREVENT+3,random.randrange(3000,3500))
    speed = 30

    global bgX, bgX2
    
    win = pygame.display.set_mode((win_width,win_height))
    clock = pygame.time.Clock()

    run = True
    while run:
        
        clock.tick(speed)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                break
            if event.type == USEREVENT+1:
                    speed += 1
            if event.type == USEREVENT+2:
                r = random.randrange(0,2)
                if r == 0:
                    cactuses.append(Cactus(1010,350))
            if event.type == USEREVENT+3:
                r2 = random.randrange(0,3)
                if r2 == 0:
                    crows.append(Crow(2000,550))

        cactus_ind = 0
        crow_ind = 0
        #Tell the AI which cactus to see. For eg: See the 2nd when first one is passsed
        if len(dinos) > 0 and len(cactuses) > 0:
            for i,dist in enumerate([cactus.x - dinos[0].x for cactus in cactuses]):
                if dist > 0:
                    cactus_ind = i
                    break
                
        #Tell the AI which crow to see. For eg: See the 2nd when first one is passed
        if len(dinos) > 0 and len(crows) > 0:
            for i,dist in enumerate([crow.x - dinos[0].x for crow in crows]):
                if dist > 0:
                    crow_ind = i
                    break

        else:
            run = False
            break

        #Loop that allows the AI to play the game
        for x,dino in enumerate(dinos):
            ge[x].fitness += 0.1 #Give each dino a fitness of 0.1 to stay alive
            
            dino.move()
            
            #The NN consists of 3 inputs and 2 outputs
            #Give the dino as input its position, distance from the upcoming cactus and the width of that cactus
            output = nets[x].activate((dino.y,abs(dino.x - cactuses[cactus_ind].x),cactuses[cactus_ind].cactus_image.get_width()))
            #Give the dino as input its position, distance from the upcoming crow and the width of that crow
            output2 = nets[x].activate((dino.y,abs(dino.x - crows[crow_ind].x),crows[crow_ind].img.get_width()))
                           
            #In the tanh function if the result is 0.5 for output, then jump
            if output[0] > 0.5:
                dino.jump()

            #In the tanh function if the result is 0.5 for output2, then duck
            if output2[0] > 0.5:
                dino.duck()

        base.move()

        add_cactus = False
        add_crow = False
        rem = []
        rem_crow = []

        for cactus in cactuses:
            for x,dino in enumerate(dinos):
                #If a dino collides with the cactus, remove it from the game
                if cactus.collide(dino):
                    ge[x].fitness -= 1
                    dinos.pop(x)
                    nets.pop(x)
                    ge.pop(x)

                #If dino passes the cactus
                if not cactus.passed and cactus.x < dino.x:
                    cactus.passed = True
                    add_cactus = True
                    
            #If cactus goes off screen, remove it
            if cactus.x + cactus.cactus_image.get_width() < 0:
                rem.append(cactus)
                
            cactus.move()

        if cactus.passed:
            score += 1
            #Give a fitness score of 5 if a dino passes a cactus
            for g in ge:
                g.fitness += 5

        for crow in crows:
            for x,dino in enumerate(dinos):
                #If a dino collides with the crow, remove it from the game
                if crow.collide(dino):
                    ge[x].fitness -= 1
                    dinos.pop(x)
                    nets.pop(x)
                    ge.pop(x)

                if not crow.passed and crow.x < dino.x:
                    crow.passed = True
                    add_crow = True
                    
            if crow.x + crow.img.get_width() < 0:
                rem_crow.append(crow)

            crow.move()

        if crow.passed:
            score += 1
            #Give a fitness score of 5 if a dino passes a cactus
            for g in ge:
                g.fitness += 5

        draw_window(win,dinos,cactuses,crows,base)

#Run the NEAT algorithm
def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)
    p = neat.Population(config)

    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winner = p.run(eval_genome,50) #Call main() 50 times and pass genomes

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir,"config-feedforward.txt")
    run(config_path)
