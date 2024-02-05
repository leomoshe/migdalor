
import os
import sys
from pathlib import Path
import argparse
import logging
from jiwer import wer
import string

common_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "common"))
sys.path.append(common_path)
from tools import Configuration

logging.basicConfig(level=logging.DEBUG, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler(filename=__file__.replace('py', 'log'), mode='w', encoding='utf-8')
console_handler = logging.StreamHandler()
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def srt_to_text(lines):
    text = ""
    for line in lines:
        line = line.strip()
        if '-->' in line:
            continue
        if line.isnumeric() or line == '':
            continue
        text += line + '\n'
    return text.strip()


def process_wer(fullpath: str):
    hypothesis_path = fullpath
    reference_path  = hypothesis_path.replace(".gen.srt", ".srt")

    # Open the test dataset human translation file
    with open(reference_path, "r", encoding="utf-8-sig") as ref:
        reference = srt_to_text(ref.readlines())
    reference = reference.lower().translate(str.maketrans('', '', string.punctuation)).replace('\n', ' ')

    # Open the translation file by the NMT model
    with open(hypothesis_path, "r", encoding='utf-8-sig') as hyp:
        hypothesis = srt_to_text(hyp.readlines())
    hypothesis = hypothesis.lower().translate(str.maketrans('', '', string.punctuation)).replace('\n', ' ')

    wer_score = wer(reference, hypothesis)
    return wer_score

def main(config: Configuration) -> None:
    src_path = config['path']
    report_path = os.path.join(src_path, "wer_report.csv")
    with open(report_path, "w", encoding="utf-8") as report_file:
        report_file.write(f"Srt,Score\n")
    if os.path.isdir(src_path):
        for filename in os.listdir(src_path):
            if filename.endswith(".gen.srt"):
                filepath = os.path.join(src_path, filename)
                wer = process_wer(filepath)
                with open(report_path, "a", encoding="utf-8") as report_file:
                    report_file.write(f'{filename},{wer}\n')

    elif os.path.isfile(src_path):
        wer = process_wer(src_path)
        with open(report_path, "a", encoding="utf-8") as report_file:
            report_file.write(f'{filename},{wer}\n')


if __name__ == "__main__":
    logger.info("Program running")
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-p', '--path', type=str, help='Path to the file or the folder: C:\\dev\\data\\poc_a1.pdf')
    config = Configuration( __file__.replace('py', 'json'), parser)
    logger.info(config)
    main(config)

