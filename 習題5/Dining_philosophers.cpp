/**
 * 哲學家用餐問題 (Dining Philosophers Problem)
 *
 * 問題描述：
 *   5 位哲學家圍坐圓桌，每人左右各一支筷子（共 5 支）。
 *   用餐前必須同時持有左右兩支筷子。
 *   若所有人同時拿起左邊筷子，則形成死鎖 (Deadlock)。
 *
 * 解決方案（資源排序法）：
 *   將筷子編號 0~4，每位哲學家「先拿編號小的」再拿編號大的。
 *   最後一位哲學家（原本先拿右邊=4，再拿左邊=0）改為先拿 0 再拿 4，
 *   打破循環等待條件，從而避免死鎖。
 */

#include <iostream>
#include <thread>
#include <mutex>
#include <chrono>
#include <array>
#include <iomanip>
#include <atomic>

constexpr int NUM_PHILOSOPHERS = 5;
constexpr int EAT_ROUNDS      = 3;   // 每位哲學家用餐次數

std::array<std::mutex, NUM_PHILOSOPHERS> chopsticks;  // 0~4 號筷子
std::atomic<int> total_meals{0};

const char* names[] = {"Aristotle", "Plato    ", "Socrates ", "Descartes", "Kant     "};

// ─────────────────────────────────────────────
// 哲學家行為
// ─────────────────────────────────────────────
void philosopher(int id) {
    int left  = id;
    int right = (id + 1) % NUM_PHILOSOPHERS;

    // 資源排序：先鎖編號小者，避免循環等待
    int first  = std::min(left, right);
    int second = std::max(left, right);

    for (int round = 0; round < EAT_ROUNDS; ++round) {
        // 思考
        std::cout << "[" << names[id] << "] 思考中...\n";
        std::this_thread::sleep_for(std::chrono::milliseconds(100 + id * 20));

        // 拿筷子（先小後大，破除死鎖）
        std::lock_guard<std::mutex> lk1(chopsticks[first]);
        std::cout << "[" << names[id] << "] 拿起筷子 #" << first << "\n";

        std::lock_guard<std::mutex> lk2(chopsticks[second]);
        std::cout << "[" << names[id] << "] 拿起筷子 #" << second
                  << " → 開始用餐 (第 " << round + 1 << " 次)\n";

        // 用餐
        std::this_thread::sleep_for(std::chrono::milliseconds(80));
        ++total_meals;

        std::cout << "[" << names[id] << "] 放下筷子，用餐完畢。\n";
        // lock_guard 析構時自動釋放
    }
}

int main() {
    std::cout << "=== 哲學家用餐問題（資源排序法，避免死鎖）===\n";
    std::cout << "哲學家數量 = " << NUM_PHILOSOPHERS
              << "，每人用餐 " << EAT_ROUNDS << " 次\n\n";

    std::array<std::thread, NUM_PHILOSOPHERS> threads;
    for (int i = 0; i < NUM_PHILOSOPHERS; ++i)
        threads[i] = std::thread(philosopher, i);

    for (auto& t : threads)
        t.join();

    std::cout << "\n[Done] 所有哲學家用餐完畢，總計 "
              << total_meals << " 次，無死鎖發生。\n";
    return 0;
}