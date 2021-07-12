import cirq
from cirq.contrib.svg import SVGCircuit, circuit_to_svg


class Adder(cirq.Gate):
    def __init__(self, num_qubits):
        super(Adder, self)
        self._num_qubits = num_qubits

    def num_qubits(self):
        return self._num_qubits

    def carry(self, *qubits):
        c0, b, a = qubits
        yield cirq.CNOT(a, b)
        yield cirq.CNOT(a, c0)
        yield cirq.TOFFOLI(c0, b, a)

    def uncarry(self, *qubits):
        c0, b, a = qubits
        yield cirq.TOFFOLI(c0, b, a)
        yield cirq.CNOT(a, c0)
        yield cirq.CNOT(c0, b)

    def _decompose_(self, qubits):
        n = int(len(qubits) / 2)
        b = qubits[1::2]
        a = qubits[0::2]
        for i in range(n - 1):
            yield self.carry(a[i], b[i], a[i + 1])
        yield cirq.CNOT(a[- 1], b[- 1])
        for i in range(n - 2, -1, -1):
            yield self.uncarry(a[i], b[i], a[i + 1])

    def get(self, qubits):
        n = int(len(qubits) / 2)
        b = qubits[1::2]
        a = qubits[0::2]
        for i in range(n - 1):
            yield self.carry(a[i], b[i], a[i + 1])
        yield cirq.CNOT(a[- 1], b[- 1])
        for i in range(n - 2, -1, -1):
            yield self.uncarry(a[i], b[i], a[i + 1])


def init_qubits(x_bin, *qubits):
    for x, qubit in zip(x_bin[::-1], list(qubits)):
        cirq.reset(qubit)
        if x == '1':
            yield cirq.X(qubit)


def experiment_adder(p, q, n, qubits, circuit1):
    a_bin = '{:08b}'.format(p)[-n:]
    b_bin = '{:08b}'.format(q)[-n:]
    # qubits = cirq.LineQubit.range(2 * n + 2)
    a = qubits[2::2]
    b = qubits[1::2]

    # circuit1 = cirq.Circuit()
    # qubits = cirq.LineQubit.range(2 * n + 2)
    # circuit1.append(Adder(2 * n + 2).get(qubits))
    circuit = cirq.Circuit(init_qubits(b_bin, *b), init_qubits(a_bin, *a),
                           circuit1,
                           cirq.measure(*b, key='result'))
    print(circuit)
    circuit_to_svg(circuit)

    # circuit = cirq.Circuit(init_qubits(b_bin, *b), init_qubits(a_bin, *a),
    #                        Adder(n * 2 + 2).on(*qubits),
    #                        cirq.measure(*b, key='result'))

    # print(
    #     cirq.Circuit(
    #         cirq.decompose(circuit)))

    simulator = cirq.Simulator()
    result = simulator.run(circuit, repetitions=1).measurements['result']
    sum_bin = ''.join(result[0][::-1].astype(int).astype(str))
    print('{} + {} = {}'.format(a_bin, b_bin, sum_bin))


def main(n=3):
    m = 2 * n + 2
    qubits = cirq.LineQubit.range(m)
    circuit1 = cirq.Circuit()
    circuit1.append(Adder(2 * n + 2).get(qubits))
    print('Execute Adder')
    # print(
    #     cirq.Circuit(
    #         cirq.decompose(Adder(m).on(*cirq.LineQubit.range(m)))))
    for p in range(2 ** n):
        for q in range(2 ** n):
            experiment_adder(p, q, n, qubits, circuit1)


if __name__ == '__main__':
    main()
