# !/usr/bin/env python
# !-*- coding:utf-8 -*-
# !@Time   : 2020/11/17 19:58
# !@Author : DongHan Yang
# !@File   : BagCom.py
import random
import cirq
import math
import time
from cirq import LineQubit, InsertStrategy
import V

# 电路代价：2,3,4,5,6,7..10;2的n-3
cir_cost = [1, 5, 13, 29, 61, 125, 253, 509, 1021]


# 阔算算子
def make_grover(q):
    qn_1 = q[0:len(q) - 1]
    yield cirq.H.on_each(*q)
    yield cirq.X.on_each(*q)
    yield cirq.Z(q[len(q) - 1]).controlled_by(*qn_1)
    yield cirq.X.on_each(*q)
    yield cirq.H.on_each(*q)


result_answer = []


# 生成随机result,传统计算解
def ratio_add(ratio):
    add_sum = 0
    # 保证辅助位位数达到要求
    while add_sum < max(ratio):
        num = random.randint(0, len(ratio))
        add_sum = sum(random.sample(ratio, num))
    ratio.sort(reverse=True)
    # print(ratio)
    t0 = time.clock()
    do(add_sum, ratio, [])
    t1 = time.clock()
    print("传统做法花费时间：", t1 - t0)
    # print(add_sum)
    print("正确解为：", result_answer)
    return add_sum


# 暴力求解答案
def do(i, lst, lst_has):
    if i == 0:
        result_answer.append(lst_has)
        return
    elif i < 0:
        return
    if len(lst) == 0:
        return
    else:
        t = lst_has[:]
        t.append(lst[0])
        do(i - lst[0], lst[1:], t)
        do(i, lst[1:], lst_has[:])


ans_num = {}


# 构造半加器数组
def hal_cir_arr(q, qn_1, ratio):
    ratio_2bit = [[(ratio[i] & (2 ** j)) for j in range(0, len(qn_1))] for i in range(len(ratio))]
    ratio_circuit = [[j + len(qn_1) + 1, i] for j in range(len(qn_1)) for i in range(len(ratio_2bit)) if
                     ratio_2bit[i][j]]
    # ratio_circuit = [[4, 0], [5, 0], [4, 2], [5, 1]]
    return ratio_circuit


# 优化前：构造全加器数组
def make_add_function(q, qn_1, ratio):
    ratio_circuit = hal_cir_arr(q, qn_1, ratio)
    print("半加器数组：", ratio_circuit)
    for i in range(0, len(q) - 1):
        flag = 0
        index = 0
        while index < len(ratio_circuit):
            ratio_i = ratio_circuit[index]
            # print(ratio_i)
            if flag == 1 and ratio_i[0] == i + len(qn_1) + 1:
                t = ratio_i[:]
                t.insert(0, i + len(qn_1) + 2)
                ratio_circuit.insert(index, t)
                index += 2
                continue
            if ratio_i[0] == i + len(qn_1) + 1 and flag == 0:
                flag = 1
                pass
            index += 1
    print("全加器数组：", ratio_circuit)
    return ratio_circuit


# 优化前，根据数组生成全加器电路
def array_circuit(array):
    make_circuit = []
    for i in range(len(array)):
        t = [LineQubit(array[i][j]) for j in range(1, len(array[i]))]
        make_circuit.append(cirq.X(LineQubit(array[i][0])).controlled_by(*t))
    return make_circuit


# 优化后：构造全加器数组
def new_add_function(q, qn_1, ratio):
    ratio_circuit = hal_cir_arr(q, qn_1, ratio)
    for i in range(0, len(q) - 1):
        flag = 0
        cflag = 0
        index = 0
        ff = 0
        while index < len(ratio_circuit):
            ratio_i = ratio_circuit[index]
            # print(ratio_i)
            if flag == 1 and ratio_i[0] == i + len(qn_1) + 1 and ratio_i[-1] >= -1:
                ff = 1
                tv = [ratio_i[0] + 1, ratio_i[0], -2]  # v
                if ratio_i[-1] == -1:
                    tvv = [ratio_i[0] + 1] + [ratio_i[0] - 1] + ratio_i[1:]  # cv
                else:
                    tvv = [ratio_i[0] + 1] + ratio_i[1:] + [-1]  # cv
                    tdg = [ratio_i[0] + 1, ratio_i[0], -3]  # vdg
                    ratio_circuit.insert(index + 1, tdg)
                    cflag = 1
                ratio_circuit.insert(index, tv)
                ratio_circuit.insert(index, tvv)
                index += 3
                if cflag == 1:
                    index += 1
                continue
            elif ff == 1 and ratio_i[0] == i + len(qn_1) + 1 and ratio_i[-1] == -3:
                tdg = [ratio_i[0] + 1, ratio_i[0], -3]  # vdg
                ratio_circuit.insert(index + 1, tdg)
                index += 2
                ff = 0
                continue
            elif ratio_i[0] == i + len(qn_1) + 1 and flag == 0 and ratio_i[-1] >= -1:
                flag = 1
            index += 1
    # print(ratio_circuit)
    for i in range(2, len(ratio_circuit)):
        if ratio_circuit[i] \
                and ratio_circuit[i - 2] \
                and ratio_circuit[i][-1] == -2 \
                and ratio_circuit[i - 2][-1] == -3 \
                and ratio_circuit[i][0] == ratio_circuit[i - 2][0] \
                and ratio_circuit[i][1] == ratio_circuit[i - 2][1] \
                and ratio_circuit[i - 1][0] == ratio_circuit[i - 2][0] \
                and ratio_circuit[i - 1][-1] == -1:
            ratio_circuit[i] = []
            ratio_circuit[i - 2] = []
    newra = []
    for ra in ratio_circuit:
        if ra:
            newra.append(ra)
    # print(newra)
    return newra


# 优化后，根据数组生成全加器电路
def new_array_circuit(array):
    my_vgate = V.VGate()
    my_vdgate = V.VdgGate()
    make_circuit = []
    for i in range(len(array)):
        if array[i][-1] >= 0:
            t = [LineQubit(array[i][j]) for j in range(1, len(array[i]))]
        else:
            t = [LineQubit(array[i][j]) for j in range(1, len(array[i]) - 1)]
        if array[i][-1] >= 0:
            make_circuit.append(cirq.X(LineQubit(array[i][0])).controlled_by(*t))
        elif array[i][-1] >= -2:
            make_circuit.append(my_vgate.on(LineQubit(array[i][0])).controlled_by(*t))
        elif array[i][-1] == -3:
            make_circuit.append(my_vdgate.on(LineQubit(array[i][0])).controlled_by(*t))
    return make_circuit


# 计算加法器的代价(包括逆以及结果)
def get_add_cost(ratio_circuit, result, q):
    if len(q) <= 9:
        re_cost = cir_cost[len(q) - 1]
    else:
        re_cost = 2 ** len(q) - 3
    for j in range(0, len(q)):
        if (result & (2 ** j)) == 0:
            re_cost = re_cost + 2
    cost = 0
    for cir in ratio_circuit:
        n_len = len(cir)
        if cir[-1] < 0:
            if n_len <= 11:
                cost = cost + cir_cost[n_len - 3]
            else:
                cost += 2 ** (n_len - 1) - 3
        else:
            if n_len <= 10:
                cost = cost + cir_cost[n_len - 2]
            else:
                cost += 2 ** n_len - 3
    return cost * 2 + re_cost


# 构造oracle电路
def orc(q, re, res, circuit_add, circuit):
    add_cir(circuit, circuit_add, res, re, q)
    circuit.append(
        circuit_add[::-1],
        strategy=InsertStrategy.NEW_THEN_INLINE
    )


# 构造加法器电路(lw)
def add_cir(circuit, circuit_add, res, re, q):
    circuit.append(
        circuit_add,
        strategy=InsertStrategy.NEW_THEN_INLINE
    )
    circuit.append(result_bit(res, re, q), strategy=InsertStrategy.NEW_THEN_INLINE)


# 生成结果的电路
def result_bit(res, re, q):
    # 结果
    res = [(res & (2 ** j)) for j in range(0, len(q))]
    # print(res)
    # print(re)
    # print(q)
    yield (cirq.X(q) for (q, bit) in zip(q, res) if not bit)
    yield (cirq.X(re).controlled_by(*q))
    yield (cirq.X(q) for (q, bit) in zip(q, res) if not bit)


# 计算总代价
def get_all_cost(n, result, q, circuit_add_arr, count):
    # 初始化代价
    total_cost = n + 2
    # 阔算算子代价
    gro_cost = cir_cost[n - 2] + n * 4
    # 总代价
    total_cost += (get_add_cost(circuit_add_arr, result, q) + gro_cost) * count
    # print("总代价：", total_cost)
    return total_cost


# 自己设置，方便测试
def myset(ratio, result, result_num):
    ratio = [3,2,1
             ]
    result = 5
    result_num = 1
    return ratio, result, result_num


def main():
    # n系数范围；m生成参数个数
    n = input("请输入参数个数n:")
    n = int(n)
    # n = 3
    # m = input("请输入函数参数的个数m:")
    # m = int(m)
    # while m > 2**n-1:
    #     print("函数参数数量要小于{}".format(2**n-1))
    #     m = input("请输入函数参数的个数m:")
    #     m = int(m)
    m = n
    # 随机生成m个系数
    ratio = random.sample(range(1, 2 ** n - 1), m)
    # 生成结果以及对应的解数目
    result = ratio_add(ratio)
    result_num = len(result_answer)
    ratio, result, result_num = myset(ratio, result, result_num)
    print(ratio)
    print('解的个数:{}'.format(str(result_num)))
    print('解为：', result_num)

    # 辅助位的位数
    n = len(ratio)
    au_bit = math.ceil(math.log(result + 1, 2))
    print("辅助位数:", au_bit)
    print('Bag function:f({})={}'.format(
        ','.join(str(e) for e in ratio), result))
    print("优化前：")
    fun(ratio, result, result_num, n, au_bit, 0)
    print("优化后：")
    fun(ratio, result, result_num, n, au_bit, 1)


def fun(ratio, result, result_num, n, au_bit, choose):
    # qn_1 系数 ；q 辅助位 ; re 结果测试位
    qn_1 = [LineQubit(i) for i in range(0, n)]
    re = LineQubit(n)
    q = [LineQubit(i) for i in range(n + 1, n + au_bit + 1)]
    count = int(math.pi / 4 * (2 ** n / result_num) ** 0.5)  # 4分之pi*根号N/M
    print("需要迭代的次数：", count)
    circuit = cirq.Circuit(
        cirq.H.on_each(*qn_1),
        cirq.X(re),
        cirq.H(re)
    )
    if choose == 0:
        circuit_add_arr = make_add_function(q, qn_1, ratio)
        circuit_add = array_circuit(circuit_add_arr)
    else:
        circuit_add_arr = new_add_function(q, qn_1, ratio)
        circuit_add = new_array_circuit(circuit_add_arr)
    for _ in range(0, count):
        orc(q, re, result, circuit_add, circuit)
        circuit.append(make_grover(qn_1), strategy=InsertStrategy.NEW_THEN_INLINE)
    circuit.append(cirq.measure(*qn_1, key='result'))
    # 计算结果的代价
    total_cost = get_all_cost(n, result, q, circuit_add_arr, count)
    print("总代价：", total_cost)
    # Sample from the circuit a couple times.
    simulator = cirq.Simulator()
    t2 = time.clock()
    result_100 = simulator.run(circuit, repetitions=1000)
    t3 = time.clock()
    sim_time = t3 - t2
    print("Grover算法花费时间：", sim_time)
    # print(circuit)
    frequencies = result_100.histogram(key='result')
    frequencies_n = dict(frequencies)
    frequencies_m = [(i, v) for i, v in frequencies_n.items()]
    frequencies_m.sort(key=lambda x: x[1], reverse=True)
    # print(frequencies_m)
    print('采样结果:\n{}'.format(frequencies_m))
    np = []
    for j in range(result_num):
        nq = [ratio[-i - 1] for i in range(len(qn_1)) if frequencies_m[j][0] & 2 ** i]
        np.append(nq[::-1])
    print('解为f{}={}'.format(np, result))
    print("*" * 100)
    print("辅助位：{}，代价：{},模拟时间：{},成功率：{}%".format(au_bit, total_cost, sim_time,
                                                (frequencies_m[0][1]) / 10))
    print("*" * 100)


if __name__ == '__main__':
    main()
