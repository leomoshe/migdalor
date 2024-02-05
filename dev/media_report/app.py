import sys
import logging
import argparse
import os
import subprocess


common_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "common"))
sys.path.append(common_path)
import tools

logging.basicConfig(level=logging.DEBUG, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler(filename=__file__.replace('py', 'log'), mode='w', encoding='utf-8')
console_handler = logging.StreamHandler()
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def get_info(fullpath):
    command = ['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type', '-of', 'default=noprint_wrappers=1:nokey=1', fullpath]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, error = process.communicate()
    if error:
        logger.info(error)
    res = '/'.join(out.decode("utf-8").splitlines())
    return res


def process_report(fullpath: str):
    info = get_info(fullpath)
    if info is None:
        return ''
    return info


def main(config: tools.Configuration) -> None:
    src_path = config['path']
    report_path = os.path.join(src_path, "media_report.csv")
    with open(report_path, "w", encoding="utf-8") as report_file:
        report_file.write(f"File,Codecs\n")
    if os.path.isdir(src_path):
        for filename in os.listdir(src_path):
            filepath = os.path.join(src_path, filename)
            report = process_report(filepath)
            with open(report_path, "a", encoding="utf-8") as report_file:
                report_file.write(f'{filename},{report}\n')
    elif os.path.isfile(src_path):
        report = process_report(src_path)
        with open(report_path, "a", encoding="utf-8") as report_file:
            report_file.write(f'{filename},{report}\n')


if __name__ == "__main__":
    logger.info("Program running")
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-p', '--path', type=str, help='Path to the file or the folder: C:\\dev\\data\\')
    config = tools.Configuration(__file__.replace('py', 'json'), parser)
    logger.info(config)
    main(config)
