# main.py
from models import Player
import stages

def main():
    # 1. 初始化玩家
    player = Player()

    # 2. 執行關卡流程
    stages.intro(player)
    
    if player.hp > 0:
        stages.layer_1_code_abyss(player)
        
    if player.hp > 0:
        stages.layer_2_meeting_room(player)
        
    if player.hp > 0:
        stages.layer_3_server_room(player)
        
    if player.hp > 0:
        stages.final_boss(player)

    print("\n遊戲結束，感謝遊玩！")

if __name__ == "__main__":
    main()