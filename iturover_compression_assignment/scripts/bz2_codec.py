"""Bounded BZ2 decoding, independent of ROS (also shipped with the ROS 1 repo)."""

import bz2
from collections import Counter


def solve_hex(payload, max_compressed_bytes=1048576, max_decoded_bytes=4194304):
    """Return (most frequent byte, count); ties use first occurrence in the text.

    Supports concatenated BZ2 streams. Empty, truncated, corrupt or trailing
    garbage data is rejected, as is data exceeding either size limit.
    Char is a byte message: values 128..255 are preserved, not called ASCII.
    """
    if max_compressed_bytes <= 0 or max_decoded_bytes <= 0:
        raise ValueError("size limits must be positive")
    if len(payload) > max_compressed_bytes * 3:
        raise ValueError("hex input exceeds size limit")
    remaining = bytes.fromhex(payload)
    if not remaining or len(remaining) > max_compressed_bytes:
        raise ValueError("empty or oversized compressed payload")
    counts = Counter()
    total = 0
    while remaining:
        decoder = bz2.BZ2Decompressor()
        chunk = decoder.decompress(remaining, max_length=max_decoded_bytes - total + 1)
        total += len(chunk)
        if total > max_decoded_bytes:
            raise ValueError("decoded payload exceeds size limit")
        if not decoder.eof:
            raise ValueError("truncated BZ2 stream")
        counts.update(chunk)
        remaining = decoder.unused_data
    if not counts:
        raise ValueError("decoded payload is empty")
    return counts.most_common(1)[0]
