import sys
import logging
import argparse
import os
import subprocess
from pathlib import Path

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


def cut_video(filename, output_dir, start_time, end_time):
    process = subprocess.Popen(["ffmpeg", "-i", filename, "-ss", f"{start_time}", "-t", f"{end_time-start_time}", os.path.join(output_dir, f'part_{start_time}_{end_time}{os.path.splitext(filename)[1]}')], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()


def sync_subtitles(video_filename, subtitle_filename, output_filename, start_time, end_time):
    subtitle_offset = start_time
    subtitle_output_filename = output_filename + ".srt"
    comando_ffmpeg = [
        'ffmpeg',
        '-i', video_filename,
        '-ss', f'{subtitle_offset}',
        '-i', subtitle_filename,
        '-c:v', 'copy',
        '-c:a', 'copy',
        '-c:s', 'srt',  # Ajusta según tu formato de subtítulos
        '-t', f'{end_time-start_time}',
        subtitle_output_filename
    ]
    subprocess.run(comando_ffmpeg)


def find_multimedia_file(multimedia_filename):
    base_filename = os.path.splitext(os.path.basename(multimedia_filename))[0]
    folder = os.path.dirname(multimedia_filename)
    for filename in os.listdir(folder):
        if filename.lower().startswith(base_filename.lower()) and any(filename.lower().endswith(extension) for extension in tools.multimedia_extensions):
            return os.path.join(folder, filename)
    return None


def get_folder_path_from_file(file_path):
    file_folder = os.path.dirname(file_path)
    folder_path = os.path.join(file_folder, os.path.splitext(os.path.basename(file_path))[0])
    return folder_path


def process_cut(fullpath: str, duration, overlap):
    subtitle_filename = fullpath
    multimedia_filename = find_multimedia_file(subtitle_filename)
    if multimedia_filename is None:
        return
    dest_path = get_folder_path_from_file(fullpath)
    Path(dest_path).mkdir(parents=True, exist_ok=True)

    multimedia_duration = get_duration(multimedia_filename)

    # Cut the video
    start_time = 0
    while start_time < multimedia_duration:
        end_time = min(multimedia_duration, start_time + duration + overlap)
        cut_video(multimedia_filename, dest_path, start_time, end_time)
        start_time = start_time + duration

    # Sinc the subtitles
    file_extension = os.path.splitext(multimedia_filename)[1]
    start_time = 0
    while start_time < multimedia_duration:
        end_time = min(multimedia_duration, start_time + duration + overlap)
        output_filename = os.path.join(dest_path, f'part_{start_time}_{end_time}{file_extension}')
        sync_subtitles(multimedia_filename, subtitle_filename, output_filename, start_time, end_time)
        start_time = start_time + duration

def main(config: tools.Configuration) -> None:
    src_path = config['path']
    duration = config['duration']
    overlap = config['overlap']
    if os.path.isdir(src_path):
        for filename in os.listdir(src_path):
            if filename.endswith(".srt") and not filename.lower().endswith(".gen.srt"):
                filepath = os.path.join(src_path, filename)
                process_cut(filepath, duration, overlap)
    elif os.path.isfile(src_path):
        process_cut(src_path, duration, overlap)


if __name__ == "__main__":
    logger.info("Program running")
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-p', '--path', type=str, help='Path to the file or the folder: C:\\dev\\data\\poc_a1.pdf')
    config = tools.Configuration( __file__.replace('py', 'json'), parser)
    main(config)
