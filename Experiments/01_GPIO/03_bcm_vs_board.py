#!/usr/bin/env python3
"""
Bab 1 - BCM vs BOARD
Menampilkan contoh mapping nomor pin fisik dan BCM.
"""


PIN_MAP = [
    (11, 17),
    (13, 27),
    (15, 22),
    (16, 23),
    (18, 24),
    (29, 5),
    (31, 6),
]


def main():
    print("=== GPIO Numbering: BCM vs BOARD ===")
    print("BOARD = nomor pin fisik di header")
    print("BCM   = nomor GPIO internal")
    print("\nContoh mapping umum:")
    print("{:<10} {:<10}".format("BOARD", "BCM"))
    print("-" * 20)
    for board_pin, bcm_pin in PIN_MAP:
        print("{:<10} {:<10}".format(board_pin, bcm_pin))

    print("\nGunakan satu mode saja secara konsisten di satu program.")


if __name__ == "__main__":
    main()
