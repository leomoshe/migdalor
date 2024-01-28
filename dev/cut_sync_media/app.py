import sys
import logging
import argparse
import os
import subprocess
from pathlib import Path
import re
from datetime import datetime, timedelta


common_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "common"))
sys.path.append(common_path)
import tools

logging.basicConfig(level=logging.DEBUG, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler(filename=__file__.replace('py', 'log'), mode='w', encoding='utf-8')
console_handler = logging.StreamHandler()
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def get_duration(filename):
    comando_ffprobe = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', filename]
    try:
        duration_str = subprocess.check_output(comando_ffprobe, stderr=subprocess.STDOUT, text=True)
        duration = float(duration_str)
        return duration
    except subprocess.CalledProcessError as e:
        print(f"Error obteniendo la duración del video: {e}")
        return None


def get_subtitles(subtitle_filename, padding=True):
    with open(subtitle_filename, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    subtitles = []
    current_subtitle = None
    for line in lines:
        line = line.strip()
        if line.isdigit():
            if current_subtitle:
                subtitles.append(current_subtitle)
            current_subtitle = {"index": int(line), "text": [], "start_time": None, "end_time": None}
        elif re.match(r'\d+:\d+:\d+,\d+ --> \d+:\d+:\d+,\d+', line):
            start_time, end_time = map(str.strip, line.split("-->"))
            current_subtitle["start_time"] = start_time
            current_subtitle["end_time"] = end_time
        elif line:
            current_subtitle["text"].append(line)
    
    if current_subtitle:
        subtitles.append(current_subtitle)
    
    if padding:
        index = subtitles[0]["index"]-1
        end_time = subtitles[0]["start_time"]
        start_time = '00:00:00,000'
        subtitles.insert(0, {"index": index, "text": [], "start_time": start_time, "end_time": end_time})

    return subtitles


def get_folder_path_from_file(file_path):
    file_folder = os.path.dirname(file_path)
    folder_path = os.path.join(file_folder, os.path.splitext(os.path.basename(file_path))[0])
    return folder_path


def srt2timedelta(srttime):
    time_format = "%H:%M:%S,%f" if ',' in srttime else "%H:%M:%S.%f"
    # str to datetime
    time_object = datetime.strptime(srttime, time_format)
    # extract the timedelta part
    timedelta_result = timedelta(
        hours=time_object.hour,
        minutes=time_object.minute,
        seconds=time_object.second,
        microseconds=time_object.microsecond
    )
    return timedelta_result


def closest_than(subtitles, max):
    for idx, item in enumerate(subtitles):
        end_time = srt2timedelta(item["end_time"]).total_seconds()
        if end_time > max:
            return subtitles[idx-1]
    return None


def cut(input_fullpath, output_fullpath, start_time, end_time):
    comando_ffmpeg = [
        'ffmpeg',
        '-i', input_fullpath,
        '-c', 'copy', # all codecs
        '-ss', f'{start_time}',
        '-t', f'{end_time - start_time}',
        output_fullpath
    ]
    subprocess.run(comando_ffmpeg, check=True)


def find_multimedia_file(multimedia_filename):
    base_filename = os.path.splitext(os.path.basename(multimedia_filename))[0]
    folder = os.path.dirname(multimedia_filename)
    for filename in os.listdir(folder):
        if filename.lower().startswith(base_filename.lower()) and any(filename.lower().endswith(extension) for extension in tools.multimedia_extensions):
            return os.path.join(folder, filename)
    return None


def process_cut(fullpath: str, duration, overlap):
    subtitle_filename = fullpath
    subtitle_extension = ".srt"
    multimedia_filename = find_multimedia_file(subtitle_filename)
    multimedia_extension = os.path.splitext(multimedia_filename)[1]
    if multimedia_filename is None:
        return
    dest_path = get_folder_path_from_file(fullpath)
    Path(dest_path).mkdir(parents=True, exist_ok=True)

    subtitles = get_subtitles(subtitle_filename)
    multimedia_duration = get_duration(multimedia_filename)
    start_time = 0
    i = 0
    while start_time < multimedia_duration:
        limit = start_time + duration + overlap
        item = closest_than(subtitles, limit)
        if item:
            end_time = srt2timedelta(item['end_time']).total_seconds()
        else:
            end_time = multimedia_duration

        output_filename = os.path.join(dest_path, f'part_{i}{multimedia_extension}')
        cut(multimedia_filename, output_filename, start_time, end_time)
        output_filename = os.path.join(dest_path, f'part_{i}{subtitle_extension}')
        cut(subtitle_filename, output_filename, start_time, end_time)

        i = i + 1
        start_time = end_time


def main(config: tools.Configuration) -> None:
    src_path = config['path']
    duration = int(config['duration'])
    overlap = int(config['overlap'])
    if os.path.isdir(src_path):
        for filename in os.listdir(src_path):
            if filename.endswith(".srt") and not filename.lower().endswith(".gen.srt"):
                srt_path = os.path.join(src_path, filename)
                process_cut(srt_path, duration, overlap)
    elif os.path.isfile(src_path):
        process_cut(src_path, duration, overlap)


if __name__ == "__main__":
    logger.info("Program running")
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-p', '--path', type=str, help='Path to the file or the folder: C:\\dev\\data\\poc_a1.pdf')
    parser.add_argument('-d', '--duration', required=False)
    parser.add_argument('-o', '--overlap', required=False)
    config = tools.Configuration( __file__.replace('py', 'json'), parser)
    main(config)
