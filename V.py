import cirq
import numpy as np


class VGate(cirq.Gate):
    def __init__(self):
        super(VGate, self)

    def _num_qubits_(self):
        return 1

    def _unitary_(self):
        return np.array([
            [1.0, -1j],
            [-1j, 1.0]
        ]) * (1 + 1j) / 2

    def _circuit_diagram_info_(self, args):
        return "V"


class VdgGate(cirq.Gate):
    def __init__(self):
        super(VdgGate, self)

    def _num_qubits_(self):
        return 1

    def _unitary_(self):
        return np.array([
            [1.0, 1j],
            [1j, 1.0]
        ]) * (1 - 1j) / 2

    def _circuit_diagram_info_(self, args):
        return "V+"

# my_vgate = VGate()
# my_vdgate = VdgGate()
# circ = cirq.Circuit(
#     my_vgate.on(cirq.LineQubit(0)).controlled_by(cirq.LineQubit(1),cirq.LineQubit(2))
# )
#
# print("Circuit with custom gates:")
# print(circ)
