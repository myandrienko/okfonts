import argparse

from fontTools.ttLib import TTFont

from okfonts import process


def main():
    parser = argparse.ArgumentParser(
        description="Make font metrics predictable: cap height = UPM = ascender, descender = 0"
    )
    parser.add_argument("input", help="Input font file")
    parser.add_argument("-o", "--output", required=True, help="Output font file")
    args = parser.parse_args()

    font = TTFont(args.input)
    process(font)
    font.save(args.output)
