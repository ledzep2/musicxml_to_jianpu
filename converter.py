#!/usr/bin/env python3

import argparse, sys
import os.path

from reader import MusicXMLReader, MusicXMLParseError
from writer import Jianpu99Writer, WriterError
from byguitar_writer import ByguitarWriter

def parseArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', help="input file in MusicXML format")
    parser.add_argument('-m', '--mode', choices=('jianpu99', 'byguitar', 'jcx'), default='jcx', help="output format")
    return parser.parse_args()


if __name__ == "__main__":
    args = parseArguments()
    output_filebase, ext = os.path.splitext(args.input_file)

    reader = MusicXMLReader(args.input_file)
    if args.mode == 'jcx':
        writer = ByguitarWriter()
        print(writer.generate_jcx(reader))
    elif args.mode == 'byguitar':
        writer = ByguitarWriter()
        parts = reader.getPartIdList()
        for i in range(0, len(parts)):
            output_filename = f"{output_filebase}-{i}.txt"
            d = writer.generate(reader, i)
            with open(output_filename, 'w') as f:
                f.write(d)
    elif args.mode == 'jianpu99':
        output_filename = f"{output_filebase}.txt"
        writer = Jianpu99Writer()
        d = writer.generate(reader)
        with open(output_filename, 'w') as f:
            f.write(d)
    else:
        print("unrecognized mode:", args.mode)

