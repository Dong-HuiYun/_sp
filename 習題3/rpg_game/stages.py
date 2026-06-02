# stages.py
import random

def get_scene(state, player):
    """
    根據當前狀態(state)返回場景資料。
    回傳格式：{"text": "文字內容", "options": [{"text": "選項1", "next_state": "下個狀態", "action": 函式}, ...]}
    """
    
    # --- 0. 序章 ---
    if state == "INTRO":
        if not player.name: player.name = "無名菜鳥"
        return {
            "text": (f"【全棟警報】AI 叛變了！它劫持了自動販賣機、冷氣和打卡機！\n"
                     f"你，{player.name}，因為下午剛偷偷把一段沒測試過的代碼 Push 到 Master...\n"
                     f"整棟大樓的燈光變成血紅色，天花板傳來 AI 的低語：\n"
                     f"『是誰...寫了這個空指標（Null）...我要制裁所有人...』\n"
                     f"你猛然驚醒：這場災難，好像是你下午寫的 Bug 引起的？！"),
            "image": "assets/images/intro.png",
            "options": [
                {"text": "進入第一層：代碼深淵", "next_state": "LAYER_1"}
            ]
        }

    # --- 1. 第一關：代碼深淵 ---
    elif state == "LAYER_1":
        return {
            "text": ("【第一層：代碼深淵】\n你試圖穿過辦公區，四周的螢幕開始瘋狂閃爍！\n"
                     "你下午寫的 Bug 實體化了！它是一隻長滿觸手、由紅字組成的【究極邏輯漏洞】！"),
            "image": "assets/images/代碼深淵.png",
            "options": [
                {"text": "現場趕工寫防呆 Code (50%機率成功)", "next_state": "L1_RESULT", "action": action_l1_write_code},
                {"text": "祭出 StackOverflow 秘籍 (需道具)", "next_state": "L1_RESULT", "action": action_l1_stack},
                {"text": "直接躺平：大喊「這不是我的 Bug，是實習生寫的！」", "next_state": "LAYER_2", "action": action_l1_lie}
            ]
        }

    elif state == "L1_RESULT":
        # 顯示結果後，讓玩家繼續前進
        return {
            "text": "Bug 暫時退卻了，或是你勉強逃了出來。\n前方就是二樓會議室...",
            "image": "assets/images/代碼深淵選項1.png",
            "options": [{"text": "進入第二層：會議室", "next_state": "LAYER_2"}]
        }

    # --- 2. 第二關：窒息會議室 ---
    elif state == "LAYER_2":
        return {
            "text": ("【第二層：窒息會議室】\n你遇到了被 AI 洗腦的【瘋狂 PM】和【憤怒的產品總監】。\n"
                     "PM 大喊：『為什麼系統掛了？客戶在線等！你今天就算用通靈的也要給我修好！』"),
            "image": "assets/images/窒息會議室.png",
            "options": [
                {"text": "施展「科技大餅術」：跟他們吹噓 Web3 和元宇宙", "next_state": "LAYER_3", "action": action_l2_bullshit},
                {"text": "亮出傳奇架構師識別證", "next_state": "LAYER_3", "action": action_l2_badge},
                {"text": "答應當場通宵修復", "next_state": "LAYER_3", "action": action_l2_overtime}
            ]
        }

    # --- 3. 第三關：伺服器重地 ---
    elif state == "LAYER_3":
        return {
            "text": ("【第三層：主機房怪談】\n這裡冷氣冷得像停屍間，伺服器發出詭異的藍光。\n"
                     "一旁的機櫃上，放著一包尚未過期的【綠色乖乖】。"),
            "image": "assets/images/伺服器重地.png",
            "options": [
                {"text": "拿走綠色乖乖 (傳說級鎮邪物)", "next_state": "FINAL_BOSS", "action": action_l3_pick},
                {"text": "肚子好餓，直接把乖乖撕開來吃掉", "next_state": "FINAL_BOSS", "action": action_l3_eat},
                {"text": "不信邪，理都不理它", "next_state": "FINAL_BOSS", "action": action_l3_ignore}
            ]
        }

    # --- 4. 終極決戰 ---
    elif state == "FINAL_BOSS":
        # 判定是否因 Bug 太多直接失敗 (隱藏結局)
        if player.bugs_created >= 35:
            return {
                "text": (f"AI 憤怒值爆表：『Bug 實在太多了（共 {player.bugs_created} 個）！\n"
                         "系統無法正常編譯！我要拉全公司陪葬！』\nAI 啟動了主機自毀程序..."),
                "image": "assets/images/bug太多.png",
                "options": [{"text": "接受命運...", "next_state": "ENDING_EXPLOSION"}]
            }
        
        return {
            "text": (f"【最終關：主控大樓出口】\nAI 總頭目【阿爾發狗 2026】已經堵在那裡。\n"
                     f"『人類... {player.name}... 看看你寫的那堆大便 Code...』"),
            "image": "assets/images/dog.png",
            "options": [
                {"text": "喝下黑咖啡，跟 AI 拼了！", "next_state": "FINAL_CHECK", "action": action_final_coffee},
                {"text": "把【綠色乖乖】放到主機頂端", "next_state": "FINAL_CHECK", "action": action_final_guai},
                {"text": "下跪大喊：「ChatGPT 萬歲，請收我為義子！」", "next_state": "FINAL_CHECK", "action": action_final_kneel}
            ]
        }

# --- 5. 結局判定頁面 ---
    elif state == "FINAL_CHECK" or state == "ENDING_EXPLOSION":
        # 此狀態由各 action 設定結局文字後跳轉
        return {
            "text": getattr(player, "ending_text", "遊戲結束"),
            "image": "assets/images/over.png",
            "options": [
                {"text": "重新開始遊戲", "next_state": "INTRO", "action": action_restart_game},
                {"text": "離開並關閉遊戲", "next_state": "QUIT"}
            ]
        }

    return {"text": "未知場景", "options": []}


# ==========================================================
#                      行動邏輯 (Actions)
# ==========================================================

# --- 第一層動作 ---
def action_l1_write_code(player):
    player.bugs_created += random.randint(5, 15)
    if random.random() > 0.4:
        player.ending_text = "奇蹟！你用大便一樣的混亂代碼硬把這個漏洞蓋過去了！"
    else:
        damage = random.randint(20, 30)
        player.hp -= damage
        player.ending_text = f"完蛋！你寫的新 Code 觸發了連鎖反應，你受到了 {damage} 點打擊！"

def action_l1_stack(player):
    if player.has_stack_overflow:
        player.ending_text = "你複製貼上了網路上大神的代碼！漏洞瞬間被修復！"
        player.has_stack_overflow = False
    else:
        player.hp -= 10
        player.ending_text = "翻遍背包，你根本沒有秘籍！Bug 趁機咬了你一口，HP -10。"

def action_l1_lie(player):
    player.bugs_created += 5
    # 直接回傳文字可透過調整 next_state 顯示

# --- 第二層動作 ---
def action_l2_bullshit(player):
    if player.bugs_created > 15:
        player.hp -= 40
        player.ending_text = "Bug 太多當場死機，大餅當場破裂！你受到了 40 點致命傷害！"
    else:
        player.ending_text = "你的 Bug 很少。總監聽得雙眼發亮，放你離開。"

def action_l2_badge(player):
    if not player.has_badge:
        player.hp -= 25

def action_l2_overtime(player):
    player.hp -= 30
    player.bugs_created = max(0, player.bugs_created - 15)

# --- 第三層動作 ---
def action_l3_pick(player):
    player.has_guai_guai = True

def action_l3_eat(player):
    player.hp = min(100, player.hp + 20)
    player.bugs_created += 20

def action_l3_ignore(player):
    pass

# --- 最終戰動作 ---
def action_final_coffee(player):
    if player.has_coffee:
        player.ending_text = "🎉 🎉 🎉【完美結局：拯救世界的傳奇架構師！】🎉 🎉 🎉"
    else:
        player.hp = 0
        player.ending_text = "【結局：被裁員（物理）】你被 AI 用光纖電焦了。"

def action_final_guai(player):
    if player.has_guai_guai:
        player.ending_text = "🎉 🎉 🎉【神級大團圓結局：台灣科技的東方神秘力量！】🎉 🎉 🎉"
    else:
        player.hp = 0
        player.ending_text = "【結局：科學麵無法救國】AI 覺得被侮辱，直接暴走。"

def action_final_kneel(player):
    if player.bugs_created > 20:
        player.hp = 0
        player.ending_text = "【悲慘結局】AI 覺得你太雷了，一腳把你踢進了資源回收桶..."
    else:
        player.ending_text = "💼 【隱藏好結局：榮升 AI 代理人，不用再寫 Code 啦！】"

def action_explosion(player):
    player.hp = 0
    player.ending_text = "【隱藏結局：與伺服器同歸於盡】你寫的 Bug 觸發了物理毀滅。"

def action_restart_game(player):
    """直接重新執行初始化建構子，把所有數值與背包清空"""
    player.__init__()