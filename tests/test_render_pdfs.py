"""Blocked rasterising of the chart PDFs.

The block size is not a tuning knob. pdfium draws through AGG, whose cell
coordinates overflow past about 2^15 device pixels: ask it for a bitmap wider
than that and it returns the full size, fills it white, draws the page frame and
silently omits the interior. A whole IFR sheet at 2x is 48000 px wide and lost
its right third that way, which read as a georeferencing fault. These guard the
size and the tiling that keeps every render under it.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from render_pdfs import BLOCK, blocks  # noqa: E402

# Measured against ENR_L27: 31868 px rendered completely, 35324 px began
# dropping content, 47900 px lost everything past ~32000.
AGG_LIMIT = 32767


def test_block_size_stays_under_the_rasteriser_limit():
    assert BLOCK <= AGG_LIMIT // 2, (
        f"BLOCK={BLOCK} is too close to pdfium's ~{AGG_LIMIT} px limit, past which "
        "it silently stops drawing")
    # Also a whole number of 256 px TIFF tiles, so blocks land on the tile grid.
    assert BLOCK % 256 == 0


@pytest.mark.parametrize("total", [1, 255, 8192, 8193, 16000, 44000, 48000])
def test_blocks_tile_the_whole_extent_exactly(total):
    got = list(blocks(total))
    # Contiguous, gapless, no overlap, and covering everything.
    assert got[0][0] == 0
    assert sum(length for _, length in got) == total
    for (offset, length), (next_offset, _) in zip(got, got[1:]):
        assert offset + length == next_offset
    assert all(0 < length <= BLOCK for _, length in got)


def test_a_full_sheet_is_split_in_both_axes():
    """48000 x 16000 is the real shape that broke: it must not be one render."""
    assert len(list(blocks(48000))) > 1
    assert len(list(blocks(16000))) > 1
    assert all(length <= AGG_LIMIT for _, length in blocks(48000))
