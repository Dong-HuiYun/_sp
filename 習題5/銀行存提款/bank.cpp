/**
 * 銀行存提款模擬 (Bank Deposit/Withdraw Simulation)
 *
 * 問題描述：
 *   同一個帳戶，多個執行緒同時執行存款與提款，
 *   各執行 100000 次，最終餘額必須正確。
 *
 * 解決方案：
 *   使用 std::mutex 保護臨界區 (critical section)，
 *   確保每次存提款操作的原子性 (atomicity)。
 */

#include <iostream>
#include <thread>
#include <mutex>
#include <cassert>

// ─────────────────────────────────────────────
// BankAccount：帶互斥鎖的銀行帳戶
// ─────────────────────────────────────────────
class BankAccount {
public:
    explicit BankAccount(long long initial_balance)
        : balance_(initial_balance) {}

    // 存款
    void deposit(long long amount) {
        std::lock_guard<std::mutex> lock(mutex_);
        balance_ += amount;
    }

    // 提款（若餘額不足則不執行）
    void withdraw(long long amount) {
        std::lock_guard<std::mutex> lock(mutex_);
        if (balance_ >= amount)
            balance_ -= amount;
    }

    long long balance() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return balance_;
    }

private:
    long long balance_;
    mutable std::mutex mutex_;
};

// ─────────────────────────────────────────────
// 執行緒工作函式
// ─────────────────────────────────────────────
constexpr int ITERATIONS = 100000;
constexpr long long AMOUNT = 1;

void depositor(BankAccount& account) {
    for (int i = 0; i < ITERATIONS; ++i)
        account.deposit(AMOUNT);
}

void withdrawer(BankAccount& account) {
    for (int i = 0; i < ITERATIONS; ++i)
        account.withdraw(AMOUNT);
}

int main() {
    const long long initial = 1000000LL;
    BankAccount account(initial);

    std::cout << "=== 銀行存提款模擬 ===" << std::endl;
    std::cout << "初始餘額 : " << initial << std::endl;
    std::cout << "存款執行緒 x2，各執行 " << ITERATIONS << " 次，每次 +" << AMOUNT << std::endl;
    std::cout << "提款執行緒 x2，各執行 " << ITERATIONS << " 次，每次 -" << AMOUNT << std::endl;

    // 2 個存款執行緒 + 2 個提款執行緒
    std::thread t1(depositor,  std::ref(account));
    std::thread t2(depositor,  std::ref(account));
    std::thread t3(withdrawer, std::ref(account));
    std::thread t4(withdrawer, std::ref(account));

    t1.join(); t2.join(); t3.join(); t4.join();

    long long final_balance = account.balance();
    // 2 個存款執行緒各存 ITERATIONS 次，2 個提款執行緒各提 ITERATIONS 次
    // 總存入 = 總提出  →  最終餘額應等於初始餘額
    long long expected = initial
        + 2LL * ITERATIONS * AMOUNT   // 存款
        - 2LL * ITERATIONS * AMOUNT;  // 提款

    std::cout << "\n最終餘額 : " << final_balance << std::endl;
    std::cout << "預期餘額 : " << expected       << std::endl;

    if (final_balance == expected)
        std::cout << "[PASS] 餘額正確！互斥鎖成功防止競態條件。" << std::endl;
    else
        std::cout << "[FAIL] 餘額錯誤！差值 = " << (final_balance - expected) << std::endl;

    return 0;
}