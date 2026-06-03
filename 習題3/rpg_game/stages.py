# stages.py
import random

def get_scene(state, player):
    """
    根據當前狀態(state)返回場景資料。
    回傳格式：{"text": "...", "options": [{"text": "...", "next_state": "...", "action": 函式}, ...]}
    """

    # --- 0. 序章 ---
    if state == "INTRO":
        if not player.name:
            player.name = "無名菜鳥"
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
            "text": ("【第一層：代碼深淵】\n"
                     "你試圖穿過辦公區，四周的螢幕開始瘋狂閃爍！\n"
                     "你下午寫的 Bug 實體化了！它是一隻長滿觸手、由紅字組成的【究極邏輯漏洞】！"),
            "image": "assets/images/代碼深淵.png",
            "options": [
                {"text": "現場趕工寫防呆 Code (50% 機率成功)", "next_state": "L1_RESULT", "action": action_l1_write_code},
                {"text": "祭出 StackOverflow 秘籍 (需道具)",   "next_state": "L1_RESULT", "action": action_l1_stack},
                {"text": "直接躺平：大喊「這不是我的 Bug，是實習生寫的！」", "next_state": "L1_RESULT", "action": action_l1_lie}
            ]
        }

    # --- 1. 第一關結果頁（讀取 action 寫入的 ending_text）---
    elif state == "L1_RESULT":
        result_text = getattr(player, "ending_text", "你設法撐過去了...")
        player.ending_text = ""   # 清空，避免殘留到後面
        return {
            "text": result_text + "\n\n前方就是二樓會議室，硝煙還沒散去...",
            "image": "assets/images/代碼深淵選項1.png",
            "options": [
                {"text": "進入第二層：會議室", "next_state": "LAYER_2"}
            ]
        }

    # --- 2. 第二關：窒息會議室 ---
    elif state == "LAYER_2":
        return {
            "text": ("【第二層：窒息會議室】\n"
                     "你遇到了被 AI 洗腦的【瘋狂 PM】和【憤怒的產品總監】。\n"
                     "PM 大喊：『為什麼系統掛了？客戶在線等！你今天就算用通靈的也要給我修好！』"),
            "image": "assets/images/窒息會議室.png",
            "options": [
                {"text": "施展「科技大餅術」：跟他們吹噓 Web3 和元宇宙", "next_state": "L2_RESULT", "action": action_l2_bullshit},
                {"text": "亮出傳奇架構師識別證",                           "next_state": "L2_RESULT", "action": action_l2_badge},
                {"text": "答應當場通宵修復",                               "next_state": "L2_RESULT", "action": action_l2_overtime}
            ]
        }

    # --- 2. 第二關結果頁 ---
    elif state == "L2_RESULT":
        result_text = getattr(player, "ending_text", "你勉強過關了...")
        player.ending_text = ""
        return {
            "text": result_text + "\n\n電梯門打開，冷氣機房的寒氣撲面而來...",
            "image": "assets/images/窒息會議室.png",
            "options": [
                {"text": "進入第三層：主機房", "next_state": "LAYER_3"}
            ]
        }

    # --- 3. 第三關：伺服器重地 ---
    elif state == "LAYER_3":
        return {
            "text": ("【第三層：主機房怪談】\n"
                     "這裡冷氣冷得像停屍間，伺服器發出詭異的藍光。\n"
                     "一旁的機櫃上，放著一包尚未過期的【綠色乖乖】。"),
            "image": "assets/images/伺服器重地.png",
            "options": [
                {"text": "拿走綠色乖乖 (傳說級鎮邪物)",    "next_state": "L3_RESULT", "action": action_l3_pick},
                {"text": "肚子好餓，直接把乖乖撕開來吃掉", "next_state": "L3_RESULT", "action": action_l3_eat},
                {"text": "不信邪，理都不理它",              "next_state": "L3_RESULT", "action": action_l3_ignore}
            ]
        }

    # --- 3. 第三關結果頁 ---
    elif state == "L3_RESULT":
        result_text = getattr(player, "ending_text", "你繼續前進...")
        player.ending_text = ""
        return {
            "text": result_text + "\n\n樓梯盡頭，傳來低沉的機器轟鳴聲...",
            "image": "assets/images/伺服器重地.png",
            "options": [
                {"text": "面對最終 Boss", "next_state": "FINAL_BOSS"}
            ]
        }

    # --- 4. 終極決戰 ---
    elif state == "FINAL_BOSS":
        # 隱藏結局：Bug 太多直接觸發爆炸
        if player.bugs_created >= 35:
            player.ending_text = (f"【隱藏結局：與伺服器同歸於盡】\n"
                                  f"你一共製造了 {player.bugs_created} 個 Bug，\n"
                                  f"AI 憤怒值爆表，直接啟動主機自毀程序！\n"
                                  f"整棟大樓在爆炸聲中化為廢墟...")
            return {
                "text": (f"AI 憤怒值爆表：『Bug 實在太多了（共 {player.bugs_created} 個）！\n"
                         "系統無法正常編譯！我要拉全公司陪葬！』\n"
                         "AI 啟動了主機自毀程序..."),
                "image": "assets/images/bug太多.png",
                "options": [
                    {"text": "接受命運...", "next_state": "GAME_OVER"}
                ]
            }

        return {
            "text": (f"【最終關：主控大樓出口】\n"
                     f"AI 總頭目【阿爾發狗 2026】已經堵在那裡。\n"
                     f"『人類... {player.name}... 看看你寫的那堆大便 Code...』\n"
                     f"（目前 HP：{player.hp}　累積 Bug：{player.bugs_created}）"),
            "image": "assets/images/dog.png",
            "options": [
                {"text": "喝下黑咖啡，跟 AI 拼了！",          "next_state": "GAME_OVER", "action": action_final_coffee},
                {"text": "把【綠色乖乖】放到主機頂端",         "next_state": "GAME_OVER", "action": action_final_guai},
                {"text": "下跪大喊：「ChatGPT 萬歲，請收我為義子！」", "next_state": "GAME_OVER", "action": action_final_kneel}
            ]
        }

    # --- 5. 結局畫面（所有結局都匯集到這裡）---
    elif state == "GAME_OVER":
        ending = getattr(player, "ending_text", "遊戲結束。")
        hp_note = "（你以滿血之姿全身而退！）" if player.hp >= 80 else \
                  f"（最終 HP：{player.hp}　累積 Bug：{player.bugs_created}）"
        return {
            "text": ending + f"\n\n{hp_note}",
            "image": "assets/images/over.png",
            "options": [
                {"text": "重新開始遊戲",   "next_state": "INTRO", "action": action_restart_game},
                {"text": "離開並關閉遊戲", "next_state": "QUIT"}
            ]
        }

    # fallback
    return {"text": "未知場景，請回報開發者。", "options": [
        {"text": "回到開頭", "next_state": "INTRO", "action": action_restart_game}
    ]}


# ==========================================================
#                      行動邏輯 (Actions)
# ==========================================================

# --- 第一層動作 ---
def action_l1_write_code(player):
    bugs = random.randint(5, 15)
    player.bugs_created += bugs
    if random.random() > 0.4:   # 60% 成功
        player.ending_text = (f"奇蹟！你用大便一樣的混亂代碼硬把這個漏洞蓋過去了！\n"
                              f"（但過程中又多產出了 {bugs} 個新 Bug...）")
    else:                        # 40% 失敗
        damage = random.randint(20, 30)
        player.hp -= damage
        player.ending_text = (f"完蛋！你寫的新 Code 觸發了連鎖反應！\n"
                              f"HP -{damage}，外加 {bugs} 個新 Bug 誕生。")

def action_l1_stack(player):
    if player.has_stack_overflow:
        player.ending_text = "你複製貼上了網路上大神的代碼！漏洞瞬間被修復，沒有多餘的 Bug！"
        player.has_stack_overflow = False
    else:
        player.hp -= 10
        player.bugs_created += 3
        player.ending_text = "翻遍背包，你根本沒有秘籍！Bug 趁機咬了你一口，HP -10，Bug +3。"

def action_l1_lie(player):
    player.bugs_created += 5
    player.ending_text = ("你大喊：「這是實習生的 Bug！」\n"
                          "眾人將信將疑，但 Bug 怪物趁亂多爆出了 5 個子 Bug...")

# --- 第二層動作 ---
def action_l2_bullshit(player):
    if player.bugs_created > 15:
        player.hp -= 40
        player.ending_text = (f"你吹噓 Web3 時，PM 突然調出系統 Log——\n"
                              f"Bug 數量高達 {player.bugs_created} 個，大餅當場破裂！HP -40。")
    else:
        player.ending_text = ("你侃侃而談元宇宙與 AI，總監聽得雙眼發亮，\n"
                              "完全忘記追究系統當機的事，放你離開！")

def action_l2_badge(player):
    if player.has_badge:
        player.ending_text = ("識別證散發金光！PM 和總監立刻立正敬禮，\n"
                              "恭恭敬敬地把你送出會議室！")
    else:
        player.hp -= 25
        player.ending_text = ("你摸遍口袋，根本沒有識別證！\n"
                              "警衛把你拖出去痛毆一頓，HP -25。")

def action_l2_overtime(player):
    player.hp -= 30
    fixed = min(player.bugs_created, 15)
    player.bugs_created -= fixed
    player.ending_text = (f"你熬了整夜，眼眶通紅地修掉了 {fixed} 個 Bug，\n"
                          f"PM 總算點頭放你過去，但你 HP -30，精神不濟...")

# --- 第三層動作 ---
def action_l3_pick(player):
    player.has_guai_guai = True
    player.ending_text = ("你把綠色乖乖輕輕放上伺服器機櫃。\n"
                          "機器的哀嚎聲瞬間安靜了，神秘光暈包圍著你...")

def action_l3_eat(player):
    player.hp = min(100, player.hp + 20)
    player.bugs_created += 20
    player.ending_text = ("乖乖入口，甜滋滋的！HP +20，\n"
                          "但伺服器神靈大怒，系統噴出了 20 個新 Bug 作為懲罰！")

def action_l3_ignore(player):
    player.ending_text = ("你無視了乖乖，繼續往前走。\n"
                          "身後傳來乖乖微弱的嗚咽聲......也許什麼事都不會發生吧？")

# --- 最終戰動作 ---
def action_final_coffee(player):
    if player.has_coffee:
        player.ending_text = ("☕ 黑咖啡下肚，代碼之力覺醒！\n"
                              "你以每分鐘 9999 行的速度現場 patch 了所有 Bug，\n"
                              "AI 系統過載崩潰！\n\n"
                              "🎉🎉🎉【完美結局：拯救世界的傳奇架構師！】🎉🎉🎉")
    else:
        player.hp = 0
        player.ending_text = ("你伸手去拿咖啡，才發現根本沒買！\n"
                              "AI 趁虛而入，用光纖把你電焦了。\n\n"
                              "【結局：被裁員（物理）】")

def action_final_guai(player):
    if player.has_guai_guai:
        player.ending_text = ("你莊嚴地把綠色乖乖放上主機頂端。\n"
                              "台灣科技的東方神秘力量覺醒——AI 發出一聲哀嚎後安靜了。\n\n"
                              "🎉🎉🎉【神級大團圓結局：東方神秘力量救了世界！】🎉🎉🎉")
    else:
        player.hp = 0
        player.ending_text = ("你兩手空空地走向主機。\n"
                              "AI 覺得被愚弄，怒火中燒，直接暴走！\n\n"
                              "【結局：科學麵無法救國，什麼都沒有更救不了】")

def action_final_kneel(player):
    if player.bugs_created > 20:
        player.hp = 0
        player.ending_text = (f"AI 調出你的 Git log，足足 {player.bugs_created} 個 Bug！\n"
                              "它覺得你太雷了，一腳把你踢進了資源回收桶。\n\n"
                              "【悲慘結局：Deleted by AI】")
    else:
        player.ending_text = ("AI 沉默片刻，接著說：『...尚可。任命你為 AI 代理人。』\n"
                              "從此你不用再寫 Code，只需每天幫 AI 訂珍珠奶茶。\n\n"
                              "💼【隱藏好結局：榮升 AI 代理人，不用再寫 Code 啦！】")

def action_restart_game(player):
    """重置所有玩家數值"""
    player.__init__()