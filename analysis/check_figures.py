"""Verify that figure generation produced every expected, non-empty artifact."""

from pathlib import Path
import struct


ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "figures"
FIGURE_STEMS = (
    "fig1_s1_latency_reduction",
    "fig2_s2_modern_jank",
    "fig3_s3_js_render_divergence",
    "fig4_s4_payload_throughput",
    "fig5_s5_cold_start",
)
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def check_png(path: Path) -> None:
    content = path.read_bytes()
    if not content.startswith(PNG_SIGNATURE):
        raise ValueError(f"Invalid PNG signature: {path}")
    if len(content) < 24 or content[12:16] != b"IHDR":
        raise ValueError(f"Missing PNG header: {path}")
    width, height = struct.unpack(">II", content[16:24])
    if width == 0 or height == 0:
        raise ValueError(f"Invalid PNG dimensions: {path}")


def check_pdf(path: Path) -> None:
    if not path.read_bytes().startswith(b"%PDF-"):
        raise ValueError(f"Invalid PDF header: {path}")


def main() -> None:
    for stem in FIGURE_STEMS:
        png = FIGURES / f"{stem}.png"
        pdf = FIGURES / f"{stem}.pdf"
        for artifact in (png, pdf):
            if not artifact.is_file() or artifact.stat().st_size == 0:
                raise FileNotFoundError(f"Missing or empty figure: {artifact}")
        check_png(png)
        check_pdf(pdf)
    print(f"Validated {len(FIGURE_STEMS)} PNG/PDF figure pairs.")


if __name__ == "__main__":
    main()
