import random

# ===================== 1. 生成 320 条指令地址序列 =====================
TOTAL_INSTR = 320
MAX_ADDR = 319
random.seed()

instructions = []
while len(instructions) < TOTAL_INSTR:
    # ① 随机起点 m
    m = random.randint(0, MAX_ADDR - 1)
    # ② 顺序执行 m+1
    if len(instructions) < TOTAL_INSTR:
        instructions.append(m + 1)
    # ③ 前地址 [0, m+1]
    m_prime = random.randint(0, m + 1)
    # ④ 顺序执行 m'+1
    if len(instructions) < TOTAL_INSTR:
        instructions.append(m_prime + 1)
    # ⑤ 后地址 [m'+2, 319]
    start = m_prime + 2
    end = MAX_ADDR
    back_addr = end if start > end else random.randint(start, end)
    if len(instructions) < TOTAL_INSTR:
        instructions.append(back_addr)

# ===================== 2. 指令地址 → 页地址流（核心） =====================
# 规则：每10条指令1页 → 页号 = 地址 // 10
page_stream = [addr // 10 for addr in instructions]

# ===================== 3. FIFO 页面置换算法 =====================
def FIFO(page_stream, mem_capacity):
    memory = []       # 内存中的页面
    fail_count = 0    # 缺页次数

    for page in page_stream:
        if page not in memory:
            fail_count += 1
            # 内存满则先进先出
            if len(memory) >= mem_capacity:
                memory.pop(0)
            memory.append(page)
    # 命中率 = 1 - 缺页次数 / 总长度
    hit_rate = 1 - fail_count / len(page_stream)
    return hit_rate, fail_count

# ===================== 4. LRU 最近最久未使用算法 =====================
def LRU(page_stream, mem_capacity):
    memory = []
    fail_count = 0

    for page in page_stream:
        if page not in memory:
            fail_count += 1
            if len(memory) >= mem_capacity:
                memory.pop(0)  # 最久未使用在队首
            memory.append(page)
        else:
            # 命中：移到队尾表示最近使用
            memory.remove(page)
            memory.append(page)

    hit_rate = 1 - fail_count / len(page_stream)
    return hit_rate, fail_count

# ===================== 5. 测试不同内存容量（4~32页）并输出结果 =====================
print("===== 请求页式存储管理 - FIFO & LRU 命中率对比 =====")
print(f"页地址流长度：{len(page_stream)}")
print("-" * 60)

# 测试内存容量：4页、8页、16页、32页
for cap in [4, 8, 16, 32]:
    fifo_hit, fifo_fail = FIFO(page_stream, cap)
    lru_hit, lru_fail = LRU(page_stream, cap)
    
    print(f"内存容量 = {cap:2d}页 | "
          f"FIFO 缺页:{fifo_fail:3d} 命中率:{fifo_hit:.2%} | "
          f"LRU 缺页:{lru_fail:3d} 命中率:{lru_hit:.2%}")

print("-" * 60)