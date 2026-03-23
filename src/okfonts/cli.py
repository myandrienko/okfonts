import argparse
import sys

from fontTools.ttLib import TTFont

from okfonts import process


def main():
    parser = argparse.ArgumentParser(
        description="Makes font size and default line height equal to cap height. Supports TTF and WOFF2."
    )
    parser.add_argument("input", help="input font file")
    parser.add_argument("-o", "--output", required=True, help="output font file")
    args = parser.parse_args()

    try:
        font = TTFont(args.input)
    except FileNotFoundError:
        sys.exit(f"Error: file not found: {args.input}")
    except Exception as e:
        sys.exit(f"Error: could not load font: {e}")

    process(font)

    try:
        font.save(args.output)
    except Exception as e:
        sys.exit(f"Error: could not save font: {e}")
