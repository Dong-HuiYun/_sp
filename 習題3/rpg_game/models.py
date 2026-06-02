# models.py

class Player:
    def __init__(self):
        self.name = ""
        self.hp = 100
        self.bugs_created = 0  # 累積的 Bug 數量
        self.has_coffee = False
        self.has_stack_overflow = False
        self.has_badge = False
        self.has_guai_guai = False  # 綠色乖乖