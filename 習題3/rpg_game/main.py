import pygame
import sys
from models import Player
import stages
import os

# 強制把工作目錄切換到 main.py 所在的資料夾
# 這樣 assets/images/xxx.png 的相對路徑才能正確找到圖片
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# --- 初始化設定 ---
DEFAULT_WIDTH = 1000
DEFAULT_HEIGHT = 750
FPS = 60

# 顏色定義
WHITE = (255, 255, 255)
BLACK = (10, 10, 15)
GRAY = (40, 40, 45)
GREEN = (50, 255, 50)

class CodeQuestGUI:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        
        self.width, self.height = 1000, 750
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("CodeQuest 碼農地下城 v4.0 (響應式升級版)")
        self.clock = pygame.time.Clock()
        
        # 動態取得當前的視窗寬高
        self.width, self.height = self.screen.get_size()
        
        self.font_main = pygame.font.SysFont("Microsoft JhengHei", 28)
        self.font_status = pygame.font.SysFont("Microsoft JhengHei", 18, bold=True)
        
        self.player = Player()
        self.current_state = "INTRO"
        self.running = True
        
        # --- 圖片處理變數 ---
        self.raw_image = None      # 原始載入的圖片
        self.current_image = None  # 縮放後顯示的圖片
        
        self.all_lines = []       
        self.line_index = 0       
        self.char_index = 0       
        self.typing_speed = 2     
        self.typing_counter = 0
        self.is_finished_all_lines = False 
        
        self.text_scroll_y = 0
        self.button_scroll_y = 0
        
        self.buttons = []
        self.load_scene(self.current_state)

    def wrap_text(self, text, font, max_width):
        lines = []
        for paragraph in text.split('\n'):
            if not paragraph.strip():
                continue
            current_line = ""
            for char in paragraph:
                test_line = current_line + char
                if font.size(test_line)[0] <= max_width:
                    current_line = test_line
                else:
                    lines.append(current_line)
                    current_line = char
            if current_line:
                lines.append(current_line)
        return lines

    def apply_image_scaling(self):
        """根據當前插圖區域大小縮放圖片"""
        if self.raw_image:
            target_w = self.width - 100
            target_h = self.height - 380
            if target_w > 0 and target_h > 0:
                self.current_image = pygame.transform.smoothscale(self.raw_image, (target_w, target_h))
        else:
            self.current_image = None

    def load_scene(self, state):
        scene_data = stages.get_scene(state, self.player)
        self.all_lines = self.wrap_text(scene_data["text"], self.font_main, self.width - 140)
        
        self.line_index = 0
        self.char_index = 0
        self.is_finished_all_lines = False
        self.current_scene_data = scene_data
        
        # 載入圖片邏輯
        self.raw_image = None
        if "image" in scene_data:
            img_path = scene_data["image"]
            print(f"[圖片] 嘗試載入：{img_path}  →  存在：{os.path.exists(img_path)}")
            if os.path.exists(img_path):
                try:
                    self.raw_image = pygame.image.load(img_path).convert_alpha()
                    print(f"[圖片] 載入成功！尺寸：{self.raw_image.get_size()}")
                except Exception as e:
                    print(f"[圖片] 載入失敗：{e}")
        
        self.apply_image_scaling() # 載入後立即縮放一次
        
        self.text_scroll_y = 0
        self.button_scroll_y = 0

    def get_inventory_str(self):
        items = []
        if self.player.has_coffee: items.append("☕")
        if self.player.has_stack_overflow: items.append("📜")
        if self.player.has_badge: items.append("🪪")
        if self.player.has_guai_guai: items.append("🟢")
        return " ".join(items) if items else "無"

    def draw_status_bar(self):
        pygame.draw.rect(self.screen, GRAY, (0, 0, self.width, 50))
        status_text = (f"👤 勇者: {self.player.name}  |  "
                       f"❤️ HP: {self.player.hp}/100  |  "
                       f"🐛 Bug 數: {self.player.bugs_created}  |  "
                       f"🎒 背包: {self.get_inventory_str()}")
        surf = self.font_status.render(status_text, True, WHITE)
        self.screen.blit(surf, (20, 15))

    def update_typing(self):
        if self.line_index < len(self.all_lines):
            current_line_full_text = self.all_lines[self.line_index]
            if self.char_index < len(current_line_full_text):
                self.typing_counter += 1
                if self.typing_counter >= self.typing_speed:
                    self.char_index += 1
                    self.typing_counter = 0
        else:
            self.is_finished_all_lines = True

    def draw_dialogue(self):
        dialogue_y = self.height - 290
        rect = pygame.Rect(50, dialogue_y, self.width - 100, 120)
        pygame.draw.rect(self.screen, GRAY, rect)
        pygame.draw.rect(self.screen, WHITE, rect, 2)
        
        self.screen.set_clip(rect)
        
        start_y = dialogue_y + 15 + self.text_scroll_y
        for i in range(self.line_index):
            text_surf = self.font_main.render(self.all_lines[i], True, (200, 200, 200))
            self.screen.blit(text_surf, (70, start_y + (i * 35)))
            
        if self.line_index < len(self.all_lines):
            display_text = self.all_lines[self.line_index][:self.char_index]
            text_surf = self.font_main.render(display_text, True, WHITE)
            self.screen.blit(text_surf, (70, start_y + (self.line_index * 35)))
            
            if self.char_index >= len(self.all_lines[self.line_index]):
                prompt_surf = self.font_status.render("▼ Click to Continue", True, GREEN)
                self.screen.set_clip(None)
                self.screen.blit(prompt_surf, (self.width - 220, dialogue_y + 90))
                
        self.screen.set_clip(None)

    def draw_buttons(self, options):
        self.buttons = []
        if not self.is_finished_all_lines:
            return

        button_area_y = self.height - 150
        button_area_rect = pygame.Rect(50, button_area_y, self.width - 100, 130)
        self.screen.set_clip(button_area_rect)

        for i, opt in enumerate(options):
            rect_y = button_area_y + (i * 45) + self.button_scroll_y
            rect = pygame.Rect(50, rect_y, self.width - 100, 40)
            
            pygame.draw.rect(self.screen, BLACK, rect)
            pygame.draw.rect(self.screen, GREEN, rect, 1)
            
            mouse_pos = pygame.mouse.get_pos()
            if rect.collidepoint(mouse_pos) and button_area_rect.collidepoint(mouse_pos):
                pygame.draw.rect(self.screen, (60, 60, 60), rect)

            text_surf = self.font_main.render(opt["text"], True, GREEN)
            self.screen.blit(text_surf, (70, rect_y + 5))
            self.buttons.append({"rect": rect, "next_state": opt["next_state"], "action": opt.get("action")})
            
        self.screen.set_clip(None)

    def run(self):
        while self.running:
            self.update_typing()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.width, self.height = 1000, 750
                        self.screen = pygame.display.set_mode((self.width, self.height))
                        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                        self.all_lines = self.wrap_text(self.current_scene_data["text"], self.font_main, self.width - 140)
                        self.apply_image_scaling() # 恢復視窗時重新縮放圖片
                    
                    elif event.key == pygame.K_F11:
                        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                        self.width, self.height = self.screen.get_size()
                        self.all_lines = self.wrap_text(self.current_scene_data["text"], self.font_main, self.width - 140)
                        self.apply_image_scaling() # 全螢幕時重新縮放圖片
                
                elif event.type == pygame.VIDEORESIZE:
                    self.width, self.height = event.w, event.h
                    self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                    self.all_lines = self.wrap_text(self.current_scene_data["text"], self.font_main, self.width - 140)
                    self.apply_image_scaling() # 手動拉動視窗時重新縮放圖片
                    if self.line_index >= len(self.all_lines):
                        self.line_index = max(0, len(self.all_lines) - 1)
                        self.char_index = len(self.all_lines[self.line_index]) if self.all_lines else 0

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: 
                        if self.line_index < len(self.all_lines):
                            current_line_text = self.all_lines[self.line_index]
                            if self.char_index < len(current_line_text):
                                self.char_index = len(current_line_text)
                            else:
                                self.line_index += 1
                                self.char_index = 0
                                if self.line_index * 35 + self.text_scroll_y > 80: 
                                    self.text_scroll_y -= 35
                        
                        elif self.is_finished_all_lines:
                            button_area_y = self.height - 150
                            button_area_rect = pygame.Rect(50, button_area_y, self.width - 100, 130)
                            if button_area_rect.collidepoint(event.pos):
                                for btn in self.buttons:
                                    if btn["rect"].collidepoint(event.pos):
                                        if btn["action"]:
                                            btn["action"](self.player)
                                        
                                        if btn["next_state"] == "QUIT":
                                            self.running = False
                                        else:
                                            self.current_state = btn["next_state"]
                                            self.load_scene(self.current_state)

                    elif event.button == 4: 
                        if self.is_finished_all_lines:
                            self.button_scroll_y = min(0, self.button_scroll_y + 15)
                        else:
                            self.text_scroll_y = min(0, self.text_scroll_y + 15)

                    elif event.button == 5: 
                        if self.is_finished_all_lines:
                            self.button_scroll_y -= 15
                        else:
                            self.text_scroll_y -= 15

            self.screen.fill(BLACK)
            
            # --- 繪製圖片區 ---
            illustration_rect = (50, 70, self.width - 100, self.height - 380)
            if self.current_image:
                # 顯示載入的圖片
                self.screen.blit(self.current_image, (50, 70))
            else:
                # 沒圖時顯示預設的深色方塊
                pygame.draw.rect(self.screen, (20, 20, 30), illustration_rect)
            
            self.draw_status_bar()
            self.draw_dialogue()
            self.draw_buttons(self.current_scene_data["options"])
            
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = CodeQuestGUI()
    game.run()