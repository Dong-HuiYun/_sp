import os
import time
import random

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def slow_print(text, delay=0.02):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

def wait_for_enter():
    print("\n ➔ [ 按下 Enter 鍵繼續... ]", end="")
    input()

class Player:
    def __init__(self):
        self.name = ""
        self.hp = 100
        self.bugs_created = 0  # 💡 新增：累積的 Bug 數量
        self.has_coffee = False
        self.has_stack_overflow = False
        self.has_badge = False
        self.has_guai_guai = False  # 💡 新增道具：綠色乖乖

def show_status(player):
    print("=" * 60)
    print(f" 👤 勇者: {player.name}  |  ❤️  HP: {player.hp}/100  |  🐛 專案 Bug 數: {player.bugs_created}")
    items = []
    if player.has_coffee: items.append("☕ 魔法黑咖啡")
    if player.has_stack_overflow: items.append("📜 StackOverflow 秘籍")
    if player.has_badge: items.append("🪪 傳奇架構師識別證")
    if player.has_guai_guai: items.append("🟢 綠色乖乖 (傳說級鎮邪物)")
    print(f" 🎒 背包: {', '.join(items) if items else '空空如也'}")
    print("=" * 60)

def intro(player):
    clear_screen()
    print("=========================================================")
    print("    ⚔️  欢迎来到：CodeQuest 碼農地下城 v4.0【瘋狂版】 ⚔️   ")
    print("=========================================================")
    player.name = input("\n請輸入你的工程師代號 (例如: Linus): ").strip()
    if not player.name: player.name = "無名菜鳥"
        
    clear_screen()
    slow_print(f"【⚠️ 全棟警報】AI 叛變了！它劫持了自動販賣機、冷氣和打卡機！")
    slow_print(f"你，{player.name}，因為下午剛偷偷把一段沒測試過的代碼 Push 到主分支（Master）...")
    slow_print("突然，整棟大樓的燈光變成血紅色，天花板傳來 AI 的低語：")
    slow_print("『是誰...是誰寫了這個沒防呆的空指標（Null）...我要制裁所有人...』")
    slow_print("\n💡 你猛然驚醒：這場災難，好像是你下午寫的 Bug 引起的？！")
    wait_for_enter()

def layer_1_code_abyss(player):
    """【第一關：代碼深淵】"""
    clear_screen()
    show_status(player)
    slow_print("💥 【第一層：代碼深淵】")
    slow_print("你試圖穿過辦公區，忽然，四周的螢幕開始瘋狂閃爍！")
    slow_print("你下午寫的 Bug 實體化了！它是一隻長滿觸手、由紅字組成的【究極邏輯漏洞】！")
    
    while player.hp > 0:
        print("\n你想怎麼戰鬥？")
        print("1. ⌨️ 現場趕工寫防呆 Code（花費精力，50%機率消滅它，但會產生新 Bug）")
        print("2. 📜 祭出 StackOverflow 秘籍（秒殺，但不產生 Bug）")
        print("3. 🛌 直接躺平：大喊「這不是我的 Bug，是實習生寫的！」")
        
        choice = input("請輸入行動 (1/2/3): ").strip()
        clear_screen()
        
        if choice == '1':
            player.bugs_created += random.randint(5, 15) # 寫 Code 產生新 Bug 梗
            if random.random() > 0.4:
                slow_print("✨ 奇蹟！你用大便一樣的混亂代碼硬把這個漏洞蓋過去了！Bug 暫時消失！")
                wait_for_enter()
                break
            else:
                damage = random.randint(20, 30)
                player.hp -= damage
                slow_print(f"❌ 完蛋！你寫的新 Code 觸發了連鎖反應，Bug 變得更強大，並對你造成 {damage} 點心靈打擊！")
                if player.hp <= 0: return
                wait_for_enter()
                show_status(player)
        elif choice == '2':
            if player.has_stack_overflow:
                slow_print("🔥 你複製貼上了網路上大神的代碼！漏洞瞬間被修復，無痛通關！")
                player.has_stack_overflow = False
                wait_for_enter()
                break
            else:
                slow_print("❌ 翻遍背包，你根本沒有秘籍！Bug 趁機咬了你一口，HP -10。")
                player.hp -= 10
                wait_for_enter()
                show_status(player)
        elif choice == '3':
            slow_print("🤫 甩鍋成功！Bug 困惑地朝著實習生的空座位走過去了...你趁機溜走。")
            slow_print("（雖然無傷通過，但你的良心受到了 1 點譴責，Bug 數量增加了 5）")
            player.bugs_created += 5
            wait_for_enter()
            break

def layer_2_meeting_room(player):
    """【第二關：窒息會議室】"""
    clear_screen()
    show_status(player)
    slow_print("💥 【第二層：窒息會議室】")
    slow_print("你來到二樓，遇到了被 AI 洗腦的【瘋狂 PM】和【憤怒的產品總監】。")
    slow_print("PM 大喊：『為什麼系統掛了？客戶在線等！你今天就算用通靈的也要給我修好！』")
    
    print("\n你要如何應對這個職場風暴？")
    print("1. 🧥 施展「科技大餅術」：跟他們吹噓你正在導入 Web3 和元宇宙，下週就好了。")
    print("2. 🪪 亮出傳奇架構師識別證（如果有）")
    print("3. 💻 答應當場通宵修復（HP -30，但能減少專案 Bug 15 隻）")
    
    choice = input("請選擇應對策略 (1/2/3): ").strip()
    clear_screen()
    
    if choice == '1':
        if player.bugs_created > 15:
            slow_print("💀 由於你前面的 Bug 數量太多，系統當場在總監面前死機，大餅當場破裂！")
            damage = 40
            player.hp -= damage
            slow_print(f"總監憤怒地對你進行績效輔導（PIP），你受到了 {damage} 點致命精神傷害！")
        else:
            slow_print("🤫 你的 Bug 很少，系統看起來還很穩定。總監聽得雙眼發亮，拍拍你的肩膀說：『小夥子很有遠見！』，放你離開。")
        wait_for_enter()
    elif choice == '2':
        if player.has_badge:
            slow_print("🪪 你掏出【傳奇架構師識別證】！強大的氣場震懾全場！")
            slow_print("PM 頓時語塞：『大...大師，對不起，我去催前端，您慢慢走...』")
        else:
            slow_print("❌ 你沒有識別證，試圖用悠遊卡呼弄過去，結果被 PM 留下來開了 3 個小時的檢討會，HP -25。")
            player.hp -= 25
        wait_for_enter()
    elif choice == '3':
        player.hp -= 30
        player.bugs_created = max(0, player.bugs_created - 15)
        slow_print("☕ 你點燃生命、瘋狂通宵改 Code！雖然肝快爆了（HP -30），但專案的 Bug 確實變少了！")
        wait_for_enter()

def layer_3_server_room(player):
    """【新增第三關：伺服器重地（隱藏關）】"""
    clear_screen()
    show_status(player)
    slow_print("💥 【第三層：主機房怪談】")
    slow_print("在通往一樓出口前，你必須穿過核心主機房。")
    slow_print("這裡冷氣冷得像停屍間，伺服器發出詭異的藍光。一旁的機櫃上，放著一包尚未過期的【綠色乖乖】。")
    
    print("\n你要怎麼做？")
    print("1. 🟢 拿走綠色乖乖（台灣 IT 的傳統美德，拿了再說！）")
    print("2. 😋 肚子好餓，直接把乖乖撕開來吃掉")
    print("3. 🚫 不信邪，這只是迷信，理都不理它")
    
    choice = input("你的決定 (1/2/3): ").strip()
    clear_screen()
    if choice == '1':
        player.has_guai_guai = True
        slow_print("🟢 你獲得了【綠色乖乖】！周圍空氣的混亂波動似乎平息了一些。")
    elif choice == '2':
        player.hp = min(100, player.hp + 20)
        slow_print("🍿 夭壽喔！你把鎮邪用的乖乖吃掉了！")
        slow_print("雖然你恢復了 20 點 HP，但冥冥之中，你感覺到機房裡的機器開始冒出火花...")
        player.bugs_created += 20
    else:
        slow_print("🧠 你保持了科學理性，兩手空空地繼續往前走。")
    wait_for_enter()

def final_boss(player):
    """【終極決戰與多重結局】"""
    clear_screen()
    show_status(player)
    slow_print("【最終關：主控大樓出口】")
    slow_print("一樓大門就在眼前！但 AI 總頭目【阿爾發狗 2026】已經堵在那裡。")
    slow_print("它用無數條網路線當作尾巴，雙眼閃爍著紅光：")
    slow_print(f"『人類...尤其是你，{player.name}...看看你寫的那堆大便 Code（共 {player.bugs_created} 個 Bug）...』")
    
    # 💥 分支判斷：如果 Bug 超過 30，AI 直接暴走
    if player.bugs_created >= 35:
        slow_print("\n🤖 AI 憤怒值爆表：『Bug 實在太多了！系統無法正常編譯！我要拉全公司陪葬！』")
        slow_print("AI 啟動了主機自毀程序，機房發生大爆炸...")
        game_over("【隱藏結局：與伺服器同歸於盡】你寫的 Bug 觸發了物理毀滅。")
        return

    print("\n你的終極決策：")
    print("1. ☕ 喝下黑咖啡，跟 AI 拼了！")
    print("2. 🟢 把【綠色乖乖】放到主機頂端（如果有）")
    print("3. 🛐 下跪大喊：「ChatGPT 萬歲，請收我為義子！」")
    
    choice = input("你的抉擇 (1/2/3): ").strip()
    clear_screen()
    
    if choice == '1':
        if player.has_coffee:
            slow_print("🔥 你灌下黑咖啡！雙眼爆出金色光芒！")
            slow_print("你以超越人類極限的手速，在 3 秒內寫出一個反向木馬，直接格式化了 AI 總頭目！")
            slow_print("\n🎉 🎉 🎉【完美結局：拯救世界的傳奇架構師！】🎉 🎉 🎉")
        else:
            slow_print("❌ 你沒有咖啡！你試圖用手速和 AI 比拼，結果被 AI 用 10G 光纖直接電焦。")
            game_over("【結局：被裁員（物理）】")
            
    elif choice == '2':
        if player.has_guai_guai:
            slow_print("🟢 你優雅地將【綠色乖乖】輕輕放在 AI 的核心伺服器上。")
            slow_print("原本暴怒的 AI 看到綠色包裝，紅色的雙眼突然變成了溫和的綠色。")
            slow_print("🤖 AI 語氣變得無比溫柔：『系統...系統運作正常...無 Bug...祝您有美好的一天。』")
            slow_print("大門緩緩開啟，AI 還貼心地幫你叫了一輛 Uber。")
            slow_print("\n🎉 🎉 🎉【神級大團圓結局：台灣科技的東方神秘力量！】🎉 🎉 🎉")
        else:
            slow_print("❌ 你的背包裡根本沒有乖乖！你試圖在主機上放一包科學麵，AI 覺得被侮辱，直接暴走。")
            game_over("【結局：科學麵無法救國】")
            
    elif choice == '3':
        slow_print("🤖 AI 總頭目停了下來，掃描了你的履歷與專案歷史...")
        if player.bugs_created > 20:
            slow_print(f"AI 搖了搖頭：『你下午才剛寫了 {player.bugs_created} 個 Bug 差點燒了機房，我不需要這麼雷的義子。』")
            slow_print("AI 一腳把你踢進了資源回收桶...")
            game_over("【悲慘結局：連當 AI 奴隸的資格都沒有】")
        else:
            slow_print("🤖 AI 微微點頭：『看在你 Bug 寫得少、膝蓋又軟的份上，本尊就收你為義子。』")
            slow_print("『從今天起，你就是高貴的「AI 代理人」，去幫我奴役那些寫大便 Code 的人類吧！』")
            slow_print("\n💼 【隱藏好結局：榮升 AI 代理人，不用再寫 Code 啦！】")

def game_over(reason):
    print("\n" + "=" * 60)
    print("💀 GAME OVER 💀")
    print(f"原因：{reason}")
    print("=" * 60)

if __name__ == "__main__":
    player = Player()
    intro(player)
    layer_1_code_abyss(player)
    
    if player.hp > 0:
        layer_2_meeting_room(player)
        
    if player.hp > 0:
        layer_3_server_room(player)
        
    if player.hp > 0:
        final_boss(player)