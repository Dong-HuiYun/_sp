import pygame
import sys
from models import Player

# --- 初始化 Pygame ---
pygame.init()
pygame.mixer.init()

# --- 設定參數 ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (50, 50, 50)
GREEN = (0, 200, 0)

screen = pygame.display.set_caption("CodeQuest 碼農地下城 v4.0")
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

# --- 載入資源 (請確保路徑下有這些檔案，或先用註解掉) ---
# font = pygame.font.Font("assets/fonts/NotoSansTC-Bold.otf", 24) 
font = pygame.font.SysFont("SimHei", 24) # 先用系統內建字體測試

class GameGUI:
    def __init__(self):
        self.player = Player()
        self.state = "INTRO"
        self.dialogue_text = ""
        self.display_text = ""
        self.options = []
        self.bg_color = BLACK
        self.running = True
        
        # 初始狀態
        self.setup_intro()

    def setup_intro(self):
        self.dialogue_text = "【⚠️ 全棟警報】AI 叛變了！它劫持了所有機器！你下午寫的 Bug 好像成真了..."
        self.options = [
            {"text": "開始挑戰", "next_state": "LAYER_1"}
        ]

    def setup_layer_1(self):
        self.dialogue_text = "【第一層：代碼深淵】你遇到了「究極邏輯漏洞」！你想怎麼戰鬥？"
        self.options = [
            {"text": "1. 寫防呆 Code", "action": self.fight_bug},
            {"text": "2. 祭出秘籍", "action": self.use_stack},
            {"text": "3. 甩鍋給實習生", "next_state": "LAYER_2"}
        ]

    def fight_bug(self):
        # 這裡放入你原本的邏輯計算
        self.player.hp -= 20
        self.dialogue_text = f"你硬寫了 Code，HP 剩下 {self.player.hp}！Bug 暫時消失了。"
        self.options = [{"text": "繼續前進", "next_state": "LAYER_2"}]

    def use_stack(self):
        self.dialogue_text = "你沒有秘籍！被 Bug 咬了一口。"
        self.player.hp -= 10
        self.options = [{"text": "痛...繼續走", "next_state": "LAYER_2"}]

    # --- 渲染邏輯 ---
    def draw(self):
        screen.fill(self.bg_color)
        
        # 1. 畫背景圖區塊 (暫時用灰色矩形代替)
        pygame.draw.rect(screen, GRAY, (50, 50, 900, 350))
        
        # 2. 畫狀態列
        status_str = f"👤 {self.player.name} | ❤️ HP: {self.player.hp} | 🐛 Bugs: {self.player.bugs_created}"
        status_surf = font.render(status_str, True, WHITE)
        screen.blit(status_surf, (50, 20))

        # 3. 畫對話框
        pygame.draw.rect(screen, WHITE, (50, 420, 900, 150), 2)
        lines = self.dialogue_text.split('\n')
        for i, line in enumerate(lines):
            text_surf = font.render(line, True, WHITE)
            screen.blit(text_surf, (70, 440 + (i * 30)))

        # 4. 畫按鈕
        for i, opt in enumerate(self.options):
            rect = pygame.Rect(50, 580 + (i * 40), 900, 35)
            pygame.draw.rect(screen, GREEN, rect, 1)
            opt_surf = font.render(opt["text"], True, GREEN)
            screen.blit(opt_surf, (70, 585 + (i * 40)))
            opt["rect"] = rect

        pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                for opt in self.options:
                    if opt.get("rect") and opt["rect"].collidepoint(mouse_pos):
                        self.execute_option(opt)

    def execute_option(self, opt):
        if "action" in opt:
            opt["action"]()
        elif "next_state" in opt:
            self.state = opt["next_state"]
            if self.state == "LAYER_1": self.setup_layer_1()
            if self.state == "LAYER_2": self.dialogue_text = "你來到了第二層：會議室..."; self.options = [] # 依此類推

    def run(self):
        while self.running:
            self.handle_events()
            self.draw()
            clock.tick(60)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = GameGUI()
    game.run()