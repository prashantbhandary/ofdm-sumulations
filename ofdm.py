"""
Simple OFDM + QPSK link simulation:
text -> bits -> QPSK symbols -> N-subcarrier OFDM blocks -> IFFT
     -> AWGN channel -> FFT -> QPSK demod -> bits -> text
"""

import numpy as np
import matplotlib.pyplot as plt

# ---------- Step 1: Text -> bits ----------
message = "Hello, okk prashantt???? done donee "

bits = ""
for character in message:
    ascii_value = ord(character)
    binary = format(ascii_value, "08b")
    bits += binary

print("Message :", message)
print("Bits    :", bits, f"({len(bits)} bits)")

# ---------- Step 2: Bits -> QPSK symbol pairs ----------
pairs = [bits[i:i+2] for i in range(0, len(bits), 2)]

qpsk_map = {
    "00": (1 + 1j) / np.sqrt(2),
    "01": (-1 + 1j) / np.sqrt(2),
    "11": (-1 - 1j) / np.sqrt(2),
    "10": (1 - 1j) / np.sqrt(2),
}
inv_qpsk_map = {v: k for k, v in qpsk_map.items()}

qpsk_symbols = np.array([qpsk_map[p] for p in pairs])
print("\nQPSK symbols:", len(qpsk_symbols))

# ---------- Step 3: Split into N-subcarrier OFDM blocks ----------
N = 8  # number of subcarriers per OFDM symbol

pad_len = (-len(qpsk_symbols)) % N
if pad_len:
    qpsk_symbols = np.concatenate([qpsk_symbols, np.zeros(pad_len, dtype=complex)])

num_blocks = len(qpsk_symbols) // N
X_blocks = qpsk_symbols.reshape(num_blocks, N)  # each row = one OFDM symbol's subcarriers

print(f"Split into {num_blocks} OFDM symbols of {N} subcarriers each"
      f" ({pad_len} zero-padding symbols added)")

# ---------- Step 4: IFFT per block (freq -> time) ----------
x_blocks = np.fft.ifft(X_blocks, axis=1)  # shape: (num_blocks, N)
x = x_blocks.flatten()  # serialized time-domain samples

# ---------- Step 5: Plot TX-side time-domain signal (after IFFT) ----------
plt.figure()
plt.stem(np.arange(N), x_blocks[0].real, linefmt="C0-", markerfmt="C0o", basefmt="r-")
plt.xlabel("Sample number (n)")
plt.ylabel("Amplitude")
plt.title("TX Side: Time-Domain Signal after IFFT (first OFDM symbol)")
plt.grid()
plt.savefig("tx_ifft_first_symbol.png")
plt.show()

# ---------- Step 6: AWGN channel ----------
noise_power = 0.05
noise = np.sqrt(noise_power / 2) * (
    np.random.randn(len(x)) + 1j * np.random.randn(len(x))
)
received_signal = x + noise

# ---------- Step 7: Receiver FFT per block ----------
r_blocks = received_signal.reshape(num_blocks, N)
Y_blocks = np.fft.fft(r_blocks, axis=1)
Y = Y_blocks.flatten()

# ---------- Plot RX-side frequency-domain signal (after FFT) ----------
# Compare recovered subcarrier values (Y) against the original transmitted
# subcarrier values (X) for the first OFDM symbol, to visualize noise impact.
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

axes[0].stem(np.arange(N), X_blocks[0].real, linefmt="C0-", markerfmt="C0o", basefmt="k-", label="Tx (real)")
axes[0].stem(np.arange(N), Y_blocks[0].real, linefmt="C3--", markerfmt="C3x", basefmt="k-", label="Rx (real)")
axes[0].set_title("Real Part: Tx vs Rx Subcarriers")
axes[0].set_xlabel("Subcarrier index (k)")
axes[0].set_ylabel("Amplitude")
axes[0].legend()
axes[0].grid()

axes[1].stem(np.arange(N), X_blocks[0].imag, linefmt="C0-", markerfmt="C0o", basefmt="k-", label="Tx (imag)")
axes[1].stem(np.arange(N), Y_blocks[0].imag, linefmt="C3--", markerfmt="C3x", basefmt="k-", label="Rx (imag)")
axes[1].set_title("Imag Part: Tx vs Rx Subcarriers")
axes[1].set_xlabel("Subcarrier index (k)")
axes[1].set_ylabel("Amplitude")
axes[1].legend()
axes[1].grid()

fig.suptitle("RX Side: Frequency-Domain Signal after FFT (first OFDM symbol)")
fig.tight_layout()
plt.savefig("rx_fft_first_symbol.png")
plt.show()

# ---------- Step 8: QPSK demapping (nearest constellation point) ----------
constellation = np.array(list(qpsk_map.values()))
labels = list(qpsk_map.keys())

def demap(symbol):
    distances = np.abs(constellation - symbol)
    return labels[np.argmin(distances)]

recovered_pairs = [demap(y) for y in Y]
recovered_bits = "".join(recovered_pairs)[: len(bits)]  # strip padding

# ---------- Step 9: Bits -> text ----------
recovered_chars = [
    chr(int(recovered_bits[i:i+8], 2))
    for i in range(0, len(recovered_bits), 8)
]
recovered_message = "".join(recovered_chars)

# ---------- Results ----------
bit_errors = sum(a != b for a, b in zip(bits, recovered_bits))
ber = bit_errors / len(bits)

print("\nRecovered bits   :", recovered_bits)
print("Recovered message:", recovered_message)
print(f"Bit errors: {bit_errors}/{len(bits)}  (BER = {ber:.4f})")