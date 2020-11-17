# !/usr/bin/env python
# !-*- coding:utf-8 -*-
# !@Time   : 2020/11/17 19:58
# !@Author : DongHan Yang
# !@File   : BagCom.py
import random
import cirq
import math
from cirq import LineQubit, InsertStrategy


def make_grover(q):
    qn_1 = q[0:len(q)-1]
    yield cirq.H.on_each(*q)
    yield cirq.X.on_each(*q)
    yield cirq.Z(q[len(q) - 1]).controlled_by(*qn_1)
    yield cirq.X.on_each(*q)
    yield cirq.H.on_each(*q)


def ratio_add(ratio):
    add_sum = 0
    # 保证辅助位位数达到要求
    while add_sum < max(ratio):
        num = random.randint(0, len(ratio))
        add_sum = sum(random.sample(ratio, num))
    ratio.sort(reverse=True)
    # print(ratio)
    do(add_sum, ratio, [])
    # print(add_sum)
    # print(resultAnswer)
    return add_sum


result_answer = []


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


def make_add_function(q, qn_1, ratio):
    ratio_2bit = [[(ratio[i] & (2 ** j)) for j in range(0, len(qn_1))] for i in range(len(ratio))]
    ratio_circuit = [[j+len(qn_1)+1, i] for j in range(len(qn_1)) for i in range(len(ratio_2bit)) if ratio_2bit[i][j]]
    print(ratio_2bit)
    print(ratio_circuit)
    for i in range(0, len(q)-1):
        flag = 0
        index = 0
        while index < len(ratio_circuit):
            ratio_i = ratio_circuit[index]
            # print(ratio_i)
            if flag == 1 and ratio_i[0] == i+len(qn_1)+1:
                t = ratio_i[:]
                t.insert(0, i+len(qn_1)+2)
                ratio_circuit.insert(index, t)
                index += 2
                continue
            if ratio_i[0] == i+len(qn_1)+1:
                flag = 1
                pass
            index += 1
    print(ratio_circuit)
    return ratio_circuit


def array_circuit(array):
    make_circuit = []
    for i in range(len(array)):
        t = [LineQubit(array[i][j]) for j in range(1, len(array[i]))]
        make_circuit.append(cirq.X(LineQubit(array[i][0])).controlled_by(*t))
    return make_circuit


def orc(q, re, res, circuit_add, circuit):
    circuit.append(
        circuit_add,
        strategy=InsertStrategy.NEW_THEN_INLINE
    )
    circuit.append(result_bit(res, re, q), strategy=InsertStrategy.NEW_THEN_INLINE)
    circuit.append(
        circuit_add[::-1],
        strategy=InsertStrategy.NEW_THEN_INLINE
    )


def result_bit(res, re, q):
    # 结果
    res = [(res & (2 ** j)) for j in range(0, len(q))]
    # print(res)
    # print(re)
    # print(q)
    yield (cirq.X(q) for (q, bit) in zip(q, res) if not bit)
    yield (cirq.X(re).controlled_by(*q))
    yield (cirq.X(q) for (q, bit) in zip(q, res) if not bit)


def main():
    # n系数范围；m生成参数个数
    n = input("请输入参数个数n:")
    n = int(n)
    # m = input("请输入函数参数的个数m:")
    # m = int(m)
    # while m > 2**n-1:
    #     print("函数参数数量要小于{}".format(2**n-1))
    #     m = input("请输入函数参数的个数m:")
    #     m = int(m)
    m = n
    # 随机生成m个系数
    ratio = random.sample(range(1, 2**n-1), m)
    # print(ratio)
    # 生成结果以及对应的解数目
    result = ratio_add(ratio)
    result_num = len(result_answer)
    print('解的个数:{}'.format(str(result_num)))
    # print(result_num)
    # print(result_answer)
    # 辅助位的位数
    au_bit = math.ceil(math.log(result + 1, 2))
    # print(au_bit)
    print('Bag function:f(x) = <{}>={}'.format(
        ', '.join(str(e) for e in ratio), result))
    # qn_1 系数 ；q 辅助位 ; re 结果测试位
    qn_1 = [LineQubit(i) for i in range(0, n)]
    re = LineQubit(n)
    q = [LineQubit(i) for i in range(n+1, n+au_bit+1)]
    # # q.reverse()
    # print(qn_1)
    # print(q)

    count = int(math.pi / 4 * (2 ** n / result_num) ** 0.5)  # 4分之pi*根号N/M
    print("需要迭代的次数：")
    print(count)

    circuit = cirq.Circuit(
        cirq.H.on_each(*qn_1),
        cirq.X(re),
        cirq.H(re)
    )
    circuit_add = array_circuit(make_add_function(q, qn_1, ratio))
    for _ in range(0, count):
        orc(q, re, result, circuit_add, circuit)
        circuit.append(make_grover(qn_1), strategy=InsertStrategy.NEW_THEN_INLINE)

    circuit.append(cirq.measure(*qn_1, key='result'))
    print(circuit)
    # Sample from the circuit a couple times.
    simulator = cirq.Simulator()
    result_100 = simulator.run(circuit, repetitions=100)
    frequencies = result_100.histogram(key='result')
    frequencies_n = dict(frequencies)
    frequencies_m = [(i, v) for i, v in frequencies_n.items()]
    frequencies_m.sort(key=lambda x: x[1], reverse=True)
    # print(frequencies_m)
    print('Sampled results:\n{}'.format(frequencies_m))
    np = []
    for j in range(result_num):
        nq = [ratio[-i-1] for i in range(len(qn_1)) if frequencies_m[j][0] & 2**i]
        np.append(nq[::-1])
    print('解为f{}={}'.format(np,result))


if __name__ == '__main__':
    main()
