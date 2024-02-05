#from googleapiclient.discovery import build
#from pytube import YouTube

import os
import sys
import json
import re
from pathlib import Path
import argparse
import logging
import csv
import pytube
common_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "common"))
sys.path.append(common_path)
from tools import Configuration

from googleapiclient.discovery import build
import youtube_transcript_api
from youtube_transcript_api.formatters import SRTFormatter

logging.basicConfig(level=logging.DEBUG, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler(filename=os.path.basename(__file__).replace('py', 'log'), mode='w', encoding='utf-8')
console_handler = logging.StreamHandler()
logger.addHandler(file_handler)
logger.addHandler(console_handler)


class Result:
  def __init__(self, value=None, error=None):
    self.Value = value
    self.Error = error


def get_youtube_service(api_key):
    youtube = build('youtube', 'v3', developerKey=api_key)
    return youtube


def download_transcript(video_id, output_folder, language="iw"): #iw is Hebrew, en English
    result = Result()
    try:
        transcript_api = youtube_transcript_api.YouTubeTranscriptApi()
        # retrieve the available transcripts
        transcript_list = transcript_api.list_transcripts(video_id)
        transcript = transcript_api.get_transcript(video_id, languages=[language])
        formatter = SRTFormatter()

        srt = formatter.format_transcript(transcript)
        full_path = os.path.join(output_folder, f"{video_id}.srt")
        # Open a text file in write mode to save the SRT
        with open(full_path, "w", encoding="utf-8") as file:
            file.write(srt)

        # Print a confirmation message to indicate successful saving
        print(f"SRT transcript saved to {full_path}")
        result.Value = full_path
    except youtube_transcript_api._errors.NoTranscriptFound as e:
        print(f"Failed to retrieve transcript: {e}")
        result.Error = e.CAUSE_MESSAGE.replace('\n', ';n')
    except youtube_transcript_api.CouldNotRetrieveTranscript as e:
        print(f"Failed to retrieve transcript: {e}")
        result.Error = e.cause.replace(',', ';')
    except KeyError as e:
        print(f"Failed to retrieve transcript: {e}")
        result.Error = f"KeyError: {e.args[0]}".replace(',', ';')
    except Exception as e:
        print(f"An error occurred: {e}")
        result.Error = e
    return result

def download_media(video_id, output_folder):
    result = Result()

    url = f'https://www.youtube.com/watch?v={video_id}'
    try:
        yt = pytube.YouTube(
            url,
            use_oauth=True,
            allow_oauth_cache=True)  # Create a YouTube object

        streams = yt.streams.all()
        '''
        lowest_resolution_stream = yt.streams.get_lowest_resolution()
        lowest_quality_audio_stream = yt.streams.get_audio_only()
        metadata_stream = yt.streams.only_metadata()
        caption_tracks = yt.caption_tracks
        streams_240p_or_higher = [stream for stream in streams if stream.resolution and int(stream.resolution[:-1]) >= 240]
        for stream in streams:
            print(f"ITAG: {stream.itag} | Resolution: {stream.resolution} | Type: {stream.mime_type} | Bitrate: {stream.bitrate}")
        first = yt.streams.first()  # Get the first available stream
        stream = streams_240p_or_higher[0]
        '''
        streams_audio = yt.streams.filter(only_audio=True)
        streams_audio = sorted(streams_audio, key=lambda x: x.bitrate, reverse=True)
        stream = streams_audio[0] if streams_audio else None


        print(f"Downloading video: {stream.title}")
        full_path = os.path.join(output_folder, f"{video_id}{Path(stream.default_filename).suffix}")
        stream.download(filename=full_path)  # Download the stream
        title = stream.title
        print(f"Download complete: {title}")
        result.Value = title
    except pytube.exceptions.AgeRestrictedError as e:
        result.Error = e.error_string.replace(',', ';')
    except pytube.exceptions.LiveStreamError as e:
        result.Error = e.error_string.replace(',', ';')
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        result.Error = e
    return result


def searchVideosByKeyword(youtube, keyword):
    videos = []
    pageToken = ""
    while True:
        res = youtube.search().list(
            q=keyword,
            type='video',
            part='id,snippet',
            maxResults=50,
            pageToken=pageToken if pageToken != "" else ""
        ).execute()
        video_items = res.get('items', [])
        if video_items:
            for video_item in video_items:
                if video_item['id']['kind'] == 'youtube#video':
                    videos.append({
                        'video_id': video_item['id']['videoId'],
                        'video_title': video_item['snippet']['title']
                    })
        pageToken = res.get('nextPageToken')
        if not pageToken:
            break
    return videos


def main(config: Configuration) -> None:
    api_key = config["api_key"]
    video_id = config["video_id"]
    keyword = config["keyword"]
    dest_path = config["output"]
    root, keyword_title = os.path.split(dest_path)

    report_path = os.path.join(dest_path, f"ym_{keyword_title}_report.csv")
    # Create dest folder
    #dest_path = os.path.normpath(os.path.join(os.path.dirname(__file__), keyword_title))
    Path(dest_path).mkdir(parents=True, exist_ok=True)
    if video_id is None:
        search_path = os.path.join(dest_path, f"{keyword_title}.json")
        # load the videos ids
        if os.path.isfile(search_path):
            with open(search_path, "r", encoding="utf-8") as file:
                videos = json.load(file)
        else:
            youtube = get_youtube_service(api_key)
            videos = searchVideosByKeyword(youtube, keyword)
            with open(search_path, "w", encoding="utf-8") as file:
                file.write(json.dumps(videos))
    else:
        videos = [{"video_id": video_id}]
    report_data = []
    if os.path.isfile(report_path):
        with open(report_path, "r", encoding="utf-8") as report_file:
            reader_file = csv.DictReader(report_file)
            for row in reader_file:
                report_data.append(row)

    with open(report_path, "w", encoding="utf-8") as report_file:
        report_file.write(f"Videoid,Media,Srt\n")

    files = os.listdir(dest_path)
    for video in videos:
        videoid = video["video_id"]
        report_item = next((item for item in report_data if item["Videoid"] == videoid), None)
        if report_item is None:
            report_item = {"Videoid": videoid, "Media": "0", "Srt": "0"}
            report_data.append(report_item)

        # download srt
        srt_full_path = os.path.join(dest_path, f"{videoid}.srt")
        if not os.path.isfile(srt_full_path):
            result = download_transcript(videoid, dest_path)
            if result.Error is not None:
                report_item["Srt"] = result.Error
                report_item["Media"] = "0"
            else:
                report_item["Srt"] = "1"             

        # download media
        if os.path.isfile(srt_full_path):
            video_files = [filename for filename in files if filename.startswith(videoid)]
            file_extension = [os.path.splitext(item)[1] for item in video_files]
            media_exists = set(file_extension).difference(set(['.json', '.srt']))
            if len(media_exists) == 0:
                result = download_media(videoid, dest_path)
                if result.Error is None:
                    video_title = result.Value
                    full_path = os.path.join(dest_path, f"{videoid}.json")
                    with open(full_path, "w", encoding="utf-8") as file:
                        file.write(f'{{"video_title": "{video_title}"}}')
                    report_item["Media"] = "1"
                else:
                    report_item["Media"] = result.Error

        with open(report_path, "a", encoding="utf-8") as report_file:
            report_file.write(f'{report_item["Videoid"]},{report_item["Media"]},{report_item["Srt"]}\n')


if __name__ == "__main__":
    logger.info("Program running")
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--api_key', required=False)
    parser.add_argument('-k', '--keyword', required=False)
    parser.add_argument('-vid', '--video_id', required=False)
    parser.add_argument('-o', '--output', required=True)
    config = Configuration( __file__.replace('py', 'json'), parser)
    logger.info(config)
    if (config['api_key'] is not None and config['keyword'] is not None and config['video_id'] is None) or \
        (config['api_key'] is None and config['keyword'] is None and config['video_id'] is not None):
        pass
    else:
        parser.error("You must provide either 'api_key' and 'keyword', or 'video_id', but not both.")
    main(config)

