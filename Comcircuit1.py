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
from Comcircuit import Adder
from cirq.contrib.svg import SVGCircuit, circuit_to_svg


def make_grover(q):
    qn_1 = q[0:len(q) - 1]
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
    t0 = time.clock()
    do(add_sum, ratio, [])
    t1 = time.clock()
    print("传统做法花费时间：", t1 - t0)
    # print(add_sum)
    print("正确解为：", result_answer)
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


def result_bit(res, re, q):
    # 结果
    res = [(res & (2 ** j)) for j in range(0, len(q))]
    yield (cirq.X(q) for (q, bit) in zip(q, res) if not bit)
    yield (cirq.X(re).controlled_by(*q))
    yield (cirq.X(q) for (q, bit) in zip(q, res) if not bit)


def init_qubits(x_bin, re, *qubits):
    for x, qubit in zip(x_bin[::-1], list(qubits)):
        # yield cirq.reset(qubit)
        if x == '1':
            yield cirq.CNOT(re, qubit)


def add_circuit(m, ratio, n, qn_1, q):
    a = q[2::2]
    b = q[1::2]
    circuit = cirq.Circuit(cirq.reset(b[j]) for j in range(len(b)))
    # circuit = cirq.Circuit()
    b_bin = '{:08b}'.format(ratio[0])[-n:]
    circuit.append(init_qubits(b_bin, qn_1[0], *b), strategy=InsertStrategy.NEW_THEN_INLINE)
    for i in range(1, m):
        circuit_add = Adder(2 * n + 2).get(q)
        a_bin = '{:08b}'.format(ratio[i])[-n:]
        circuit.append(init_qubits(a_bin, qn_1[i], *a), strategy=InsertStrategy.NEW_THEN_INLINE)
        circuit.append(circuit_add, strategy=InsertStrategy.NEW_THEN_INLINE)
        circuit.append(init_qubits(a_bin, qn_1[i], *a), strategy=InsertStrategy.NEW_THEN_INLINE)
    return circuit


def main():
    # n系数范围；m生成参数个数
    n = input("请输入参数个数n:")
    n = int(n)
    m = n
    # 随机生成m个系数
    ratio = random.sample(range(1, 2 ** n - 1), m)
    # print(ratio)
    # 生成结果以及对应的解数目
    result = ratio_add(ratio)
    result_num = len(result_answer)
    print('解的个数:{}'.format(str(result_num)))
    # print(au_bit)
    print('Bag function:f(x) = <{}>={}'.format(
        ', '.join(str(e) for e in ratio), result))
    # qn_1 系数 ；q 辅助位 ; re 结果测试位
    qn_1 = [LineQubit(i) for i in range(0, n)]
    re = LineQubit(n)
    q = [LineQubit(i) for i in range(n + 1, 3 * n + 3)]

    count = int(math.pi / 4 * (2 ** n / result_num) ** 0.5)  # 4分之pi*根号N/M
    print("需要迭代的次数：")
    print(count)
    t2 = time.clock()
    circuit = cirq.Circuit(
        cirq.H.on_each(*qn_1),
        cirq.X(re),
        cirq.H(re)
    )

    circuit_add1 = add_circuit(m, ratio, n, qn_1, q)
    for _ in range(0, count):
        circuit.append(circuit_add1)
        # circuit.append(result_bit(result, re, q[1::2]), strategy=InsertStrategy.NEW_THEN_INLINE)
        circuit.append(make_grover(qn_1), strategy=InsertStrategy.NEW_THEN_INLINE)
    circuit.append(cirq.measure(*qn_1, key='result'))
    # circuit = cirq.decompose(circuit)
    print(circuit)
    # print(circuit.to_qasm())
    print(circuit_to_svg(circuit))
    simulator = cirq.Simulator()
    result_100 = simulator.run(circuit, repetitions=1000)

    t3 = time.clock()
    print("Grover算法花费时间：", t3 - t2)

    frequencies = result_100.histogram(key='result')
    frequencies_n = dict(frequencies)
    frequencies_m = [(i, v) for i, v in frequencies_n.items()]
    frequencies_m.sort(key=lambda x: x[1], reverse=True)
    # print(frequencies_m)
    print('Sampled results:\n{}'.format(frequencies_m))
    np = []
    for j in range(result_num):
        nq = [ratio[-i - 1] for i in range(len(qn_1)) if frequencies_m[j][0] & 2 ** i]
        np.append(nq[::-1])
    print('解为f{}={}'.format(np, result))


if __name__ == '__main__':
    main()
