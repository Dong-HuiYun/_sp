import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# --- 1. 資料準備 ---
connections = [10, 100, 500, 1000, 2000]
qps = [8000, 45000, 52000, 48000, 31000]
latency = [1.2, 3.5, 8.2, 15.4, 45.1]

# 設定全局樣式 (科技感與乾淨樣式)
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_context("talk") # 讓標籤大一點，適合 PPT 展示

# --- 2. 繪製 QPS 吞吐量圖表 ---
plt.figure(figsize=(10, 6))
# 畫出折線圖
plt.plot(connections, qps, marker='o', markersize=10, linewidth=3, color='#00B4D8', label='QPS')
# 填充下方區域增加視覺豐富度
plt.fill_between(connections, qps, color='#00B4D8', alpha=0.1)

# 標記峰值 (500 connections, 52000 QPS)
peak_idx = 2
plt.annotate(f'Peak: {qps[peak_idx]} QPS\n(Optimal Concurrency)', 
             xy=(connections[peak_idx], qps[peak_idx]), 
             xytext=(connections[peak_idx]+200, qps[peak_idx]+2000),
             arrowprops=dict(facecolor='#D00000', shrink=0.05, width=2, headwidth=8),
             fontsize=12, fontweight='bold', color='#D00000', bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#D00000", alpha=0.8))

plt.title('Web Server Throughput (QPS) Analysis', fontsize=18, fontweight='bold', pad=20)
plt.xlabel('Concurrent Connections', fontsize=14)
plt.ylabel('Requests per Second (QPS)', fontsize=14)
plt.xticks(connections)
plt.grid(True, linestyle='--', alpha=0.6)

# 優化存檔
plt.tight_layout()
plt.savefig('qps_chart.png', dpi=300)
print("Successfully saved: qps_chart.png")
plt.show()


# --- 3. 繪製 Latency 延遲趨勢圖表 ---
plt.figure(figsize=(10, 6))
# 使用長條圖來展現延遲的增長量感
bars = plt.bar([str(c) for c in connections], latency, color='#457B9D', alpha=0.8, width=0.6)

# 在長條圖上方顯示數值
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval + 1, f'{yval}ms', ha='center', va='bottom', fontsize=12, fontweight='bold')

# 畫一條趨勢線輔助觀看
plt.plot([str(c) for c in connections], latency, marker='s', color='#E63946', linewidth=2, label='Latency Trend')

plt.title('Average Latency under Different Loads', fontsize=18, fontweight='bold', pad=20)
plt.xlabel('Concurrent Connections', fontsize=14)
plt.ylabel('Mean Latency (ms)', fontsize=14)
plt.ylim(0, max(latency) * 1.2) # 留一點頂部空間給標籤
plt.legend()

# 優化存檔
plt.tight_layout()
plt.savefig('latency_chart.png', dpi=300)
print("Successfully saved: latency_chart.png")
plt.show()