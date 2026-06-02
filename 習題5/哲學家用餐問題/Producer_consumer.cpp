/**
 * 生產者消費者問題 (Producer-Consumer Problem)
 *
 * 問題描述：
 *   生產者持續產生資料放入緩衝區；消費者從緩衝區取出資料處理。
 *   緩衝區容量有限，必須協調雙方速度。
 *
 * 解決方案：
 *   - std::mutex            保護緩衝區
 *   - std::condition_variable
 *       not_full  : 生產者等待「緩衝區不滿」
 *       not_empty : 消費者等待「緩衝區非空」
 */

#include <iostream>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <queue>
#include <chrono>
#include <iomanip>

// ─────────────────────────────────────────────
// 有界緩衝區 (Bounded Buffer)
// ─────────────────────────────────────────────
class BoundedBuffer {
public:
    explicit BoundedBuffer(int capacity) : capacity_(capacity) {}

    // 生產者放入資料（若滿則阻塞等待）
    void produce(int item) {
        std::unique_lock<std::mutex> lock(mutex_);
        not_full_.wait(lock, [this] { return (int)queue_.size() < capacity_; });
        queue_.push(item);
        std::cout << "  [Producer] 生產 item=" << std::setw(3) << item
                  << "  (緩衝區: " << queue_.size() << "/" << capacity_ << ")\n";
        not_empty_.notify_one();
    }

    // 消費者取出資料（若空則阻塞等待）
    int consume() {
        std::unique_lock<std::mutex> lock(mutex_);
        not_empty_.wait(lock, [this] { return !queue_.empty(); });
        int item = queue_.front();
        queue_.pop();
        std::cout << "  [Consumer] 消費 item=" << std::setw(3) << item
                  << "  (緩衝區: " << queue_.size() << "/" << capacity_ << ")\n";
        not_full_.notify_one();
        return item;
    }

private:
    std::queue<int>         queue_;
    int                     capacity_;
    std::mutex              mutex_;
    std::condition_variable not_full_;
    std::condition_variable not_empty_;
};

// ─────────────────────────────────────────────
// 執行緒工作函式
// ─────────────────────────────────────────────
constexpr int PRODUCE_COUNT = 10;

void producer(BoundedBuffer& buf) {
    for (int i = 1; i <= PRODUCE_COUNT; ++i) {
        // 模擬生產耗時
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
        buf.produce(i);
    }
}

void consumer(BoundedBuffer& buf, int count) {
    for (int i = 0; i < count; ++i) {
        // 模擬消費耗時（比生產稍慢，示範緩衝作用）
        std::this_thread::sleep_for(std::chrono::milliseconds(120));
        buf.consume();
    }
}

int main() {
    std::cout << "=== 生產者消費者模擬 ===" << std::endl;
    std::cout << "緩衝區容量 = 3，生產 " << PRODUCE_COUNT
              << " 個 item，由 2 個消費者分攤消費\n\n";

    BoundedBuffer buf(3);

    // 1 個生產者，2 個消費者（各消費 5 個）
    std::thread prod(producer, std::ref(buf));
    std::thread cons1(consumer, std::ref(buf), PRODUCE_COUNT / 2);
    std::thread cons2(consumer, std::ref(buf), PRODUCE_COUNT / 2);

    prod.join();
    cons1.join();
    cons2.join();

    std::cout << "\n[Done] 所有 item 已生產並消費完畢。" << std::endl;
    return 0;
}