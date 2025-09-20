import pygame
import random
import math
import sys

# 初始化pygame
pygame.init()

# 屏幕设置
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("行星战争")

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
PLAYER_COLOR = (78, 192, 255)  # 玩家颜色
ENEMY_COLOR = (255, 96, 96)   # 敌人颜色
NEUTRAL_COLOR = (180, 180, 180) # 中立颜色
LINE_COLOR = (50, 50, 50)     # 连线颜色

# 字体
font = pygame.font.SysFont('SimHei', 20)
large_font = pygame.font.SysFont('SimHei', 32)

# 加载背景图片
try:
    background_image = pygame.image.load("space_background.jpg").convert()
    background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))
except pygame.error:
    print("Warning: space_background.jpg not found. Using a solid black background.")
    background_image = None

# 星球类
class Planet:
    def __init__(self, x, y, radius, owner, ships, production_rate):
        self.x = x
        self.y = y
        self.radius = radius
        self.owner = owner  # 0: 中立, 1: 玩家, 2: 敌人
        self.ships = ships
        self.production_rate = production_rate
        self.selected = False
        self.color = self.get_color()
        self.glow_radius = radius + 5
        self.glow_color = self.color

    def get_color(self):
        if self.owner == 0:
            return NEUTRAL_COLOR
        elif self.owner == 1:
            return PLAYER_COLOR
        else:
            return ENEMY_COLOR
            
    def produce_ships(self):
        if self.owner != 0:
            self.ships += self.production_rate
            
    def draw(self, surface):
        # 绘制星球本体
        pygame.draw.circle(surface, self.color, (self.x, self.y), self.radius)
        
        # 绘制星球光晕（根据归属和选中状态）
        if self.owner != 0:
            glow_surface = pygame.Surface((self.glow_radius * 2, self.glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (self.color[0], self.color[1], self.color[2], 50), (self.glow_radius, self.glow_radius), self.glow_radius)
            surface.blit(glow_surface, (self.x - self.glow_radius, self.y - self.glow_radius))

        # 绘制星球环
        pygame.draw.circle(surface, (255, 255, 255, 50), (self.x, self.y), self.radius + 5, 2)
        
        # 如果被选中，绘制选择圆圈
        if self.selected:
            pygame.draw.circle(surface, WHITE, (self.x, self.y), self.radius + 7, 2)
            
        # 绘制飞船数量
        text = font.render(str(self.ships), True, WHITE)
        text_rect = text.get_rect(center=(self.x, self.y))
        surface.blit(text, text_rect)
        
    def is_clicked(self, pos):
        distance = math.sqrt((pos[0] - self.x) ** 2 + (pos[1] - self.y) ** 2)
        return distance <= self.radius

# 舰队类
class Fleet:
    def __init__(self, start_planet, end_planet, ships, owner):
        self.start_planet = start_planet
        self.end_planet = end_planet
        self.ships = ships
        self.owner = owner
        self.color = PLAYER_COLOR if owner == 1 else ENEMY_COLOR
        self.x = start_planet.x
        self.y = start_planet.y
        self.progress = 0
        
        BASE_SPEED = 0.015
        SPEED_FACTOR = 1000
        
        speed_modifier = math.log(self.ships + 1) / SPEED_FACTOR
        self.speed = max(BASE_SPEED - speed_modifier, 0.001)
        
    def update(self):
        self.progress += self.speed
        if self.progress >= 1:
            self.arrive()
            return True
            
        self.x = self.start_planet.x + (self.end_planet.x - self.start_planet.x) * self.progress
        self.y = self.start_planet.y + (self.end_planet.y - self.start_planet.y) * self.progress
        return False
        
    def arrive(self):
        if self.end_planet.owner == self.owner:
            self.end_planet.ships += self.ships
        else:
            if self.ships > self.end_planet.ships:
                self.end_planet.owner = self.owner
                self.end_planet.ships = self.ships - self.end_planet.ships
                self.end_planet.color = self.end_planet.get_color()
            else:
                self.end_planet.ships -= self.ships
                
    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), 5)
        
        text = font.render(str(self.ships), True, WHITE)
        surface.blit(text, (int(self.x) + 10, int(self.y) - 10))

# 游戏类
class Game:
    def __init__(self):
        self.planets = []
        self.fleets = []
        self.selected_planet = None
        self.game_over = False
        self.winner = None
        self.turn_count = 0
        self.setup_game()
        
    def setup_game(self):
        self.planets = []
        num_planets = 10
        for i in range(num_planets):
            while True:
                x = random.randint(50, WIDTH - 50)
                y = random.randint(50, HEIGHT - 50)
                too_close = False
                for planet in self.planets:
                    distance = math.sqrt((x - planet.x) ** 2 + (y - planet.y) ** 2)
                    if distance < 100:
                        too_close = True
                        break
                if not too_close:
                    break
                    
            radius = random.randint(20, 40)
            owner = 0
            if i == 0:
                owner = 1
            elif i == 1:
                owner = 2
                
            ships = random.randint(10, 50) if owner != 0 else random.randint(5, 20)
            production_rate = random.randint(1, 5)
            self.planets.append(Planet(x, y, radius, owner, ships, production_rate))
            
    def select_planet(self, pos):
        for planet in self.planets:
            if planet.is_clicked(pos):
                return planet
        return None
        
    def update(self):
        for fleet in self.fleets[:]:
            if fleet.update():
                self.fleets.remove(fleet)
                
        player_planets = sum(1 for p in self.planets if p.owner == 1)
        enemy_planets = sum(1 for p in self.planets if p.owner == 2)
        
        if player_planets == 0 and len([f for f in self.fleets if f.owner == 1]) == 0:
            self.game_over = True
            self.winner = 2
        elif enemy_planets == 0 and len([f for f in self.fleets if f.owner == 2]) == 0:
            self.game_over = True
            self.winner = 1
            
        if self.turn_count % 60 == 0:
            self.ai_turn()
            
        self.turn_count += 1
        
    def ai_turn(self):
        enemy_planets = [p for p in self.planets if p.owner == 2]
        if not enemy_planets:
            return
            
        if random.random() < 0.5:
            source_planet = random.choice(enemy_planets)
            if source_planet.ships > 1:
                possible_targets = [p for p in self.planets if p.owner != 2]
                if possible_targets:
                    target_planet = random.choice(possible_targets)
                    ships_to_send = source_planet.ships // 2
                    if ships_to_send > 0:
                        source_planet.ships -= ships_to_send
                        self.fleets.append(Fleet(source_planet, target_planet, ships_to_send, 2))
        else:
            ai_planets = [p for p in self.planets if p.owner == 2]
            if len(ai_planets) > 1:
                source_planet = max(ai_planets, key=lambda p: p.ships)
                target_planet = min(ai_planets, key=lambda p: p.ships)

                if source_planet != target_planet and source_planet.ships > 1:
                    ships_to_send = source_planet.ships // 2
                    source_planet.ships -= ships_to_send
                    self.fleets.append(Fleet(source_planet, target_planet, ships_to_send, 2))
                
    def produce_ships(self):
        for planet in self.planets:
            planet.produce_ships()
            
    def draw(self, surface):
        if background_image:
            surface.blit(background_image, (0, 0))
        else:
            surface.fill(BLACK)
        
        for i, planet1 in enumerate(self.planets):
            for planet2 in self.planets[i+1:]:
                pygame.draw.line(surface, LINE_COLOR, (planet1.x, planet1.y), (planet2.x, planet2.y), 1)
        
        for planet in self.planets:
            planet.draw(surface)
            
        for fleet in self.fleets:
            fleet.draw(surface)
            
        player_planets = sum(1 for p in self.planets if p.owner == 1)
        enemy_planets = sum(1 for p in self.planets if p.owner == 2)
        neutral_planets = sum(1 for p in self.planets if p.owner == 0)
        
        status_text = f"玩家星球: {player_planets} | 敌人星球: {enemy_planets} | 中立星球: {neutral_planets}"
        text = font.render(status_text, True, WHITE)
        surface.blit(text, (10, 10))

        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            surface.blit(overlay, (0, 0))
            
            if self.winner == 1:
                result_text = "你赢了!"
                color = PLAYER_COLOR
            else:
                result_text = "你输了!"
                color = ENEMY_COLOR
                
            text = large_font.render(result_text, True, color)
            text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2))
            surface.blit(text, text_rect)
            
            restart_text = font.render("按空格键重新开始", True, WHITE)
            restart_rect = restart_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 50))
            surface.blit(restart_text, restart_rect)

# 主游戏循环
def main():
    clock = pygame.time.Clock()
    game = Game()
    production_timer = 0
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if game.game_over:
                    continue
                
                clicked_planet = game.select_planet(event.pos)

                if game.selected_planet:
                    if clicked_planet and clicked_planet != game.selected_planet:
                        ships_to_send = game.selected_planet.ships // 2
                        if ships_to_send > 0:
                            game.selected_planet.ships -= ships_to_send
                            game.fleets.append(Fleet(game.selected_planet, clicked_planet, ships_to_send, game.selected_planet.owner))
                        
                        game.selected_planet.selected = False
                        game.selected_planet = None
                    else:
                        game.selected_planet.selected = False
                        game.selected_planet = None
                else:
                    if clicked_planet and clicked_planet.owner == 1:
                        game.selected_planet = clicked_planet
                        game.selected_planet.selected = True
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and game.game_over:
                    game = Game()
        
        production_timer += 1
        if production_timer >= 300:
            game.produce_ships()
            production_timer = 0
            
        if not game.game_over:
            game.update()
            
        game.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)
        
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()