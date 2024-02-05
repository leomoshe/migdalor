import os
import sys
import logging
import argparse
import faster_whisper
common_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "common"))
sys.path.append(common_path)
from tools import Configuration

logging.basicConfig(level=logging.DEBUG, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler(filename=os.path.basename(__file__).replace('py', 'log'), mode='w', encoding='utf-8')
console_handler = logging.StreamHandler()
logger.addHandler(file_handler)
logger.addHandler(console_handler)

model = None
def load_model(model_path: str):
    # Check if NVIDIA GPU is available
    DEVICE = "cpu" # device = "cuda" if torch.cuda.is_available() else "cpu"
    COMPUTE_TYPE = "float16" if DEVICE == "cuda" else "int8"
    global model
    model = faster_whisper.WhisperModel(model_path, device=DEVICE, compute_type=COMPUTE_TYPE)
    #return model


def create_srt_file(file_name, results=None, fast_whisper=True):
    with open(file_name, mode="w", encoding='utf-8-sig') as f:
        for index, _dict in enumerate(results):
            if fast_whisper:
              start_time = _dict[2]#_dict[0] # start
              end_time = _dict[3]#_dict[1] # end
              text = _dict[4]#_dict[2] # text
            else:
              start_time = _dict["start"]
              end_time = _dict["end"]
              text = _dict["text"]
            s_h, e_h = int(start_time//(60 * 60)), int(end_time//(60 * 60))
            s_m, e_m = int((start_time % (60 * 60))//60), int((end_time % (60 * 60))//60)
            s_s, e_s = int(start_time % 60), int(end_time % 60)
            f.write(f'{index+1}\n{s_h:02}:{s_m:02}:{s_s:02},000 --> {e_h:02}:{e_m:02}:{e_s:02},000\n{text}\n\n')
            #print("[%.2fs -> %.2fs] %s" % (start_time, end_time, text))


def process_audio(fullpath: str):
    try:
        #segments, info = model.transcribe(src_path, beam_size = 5, task="translate")
        segments, info = model.transcribe(fullpath, beam_size = 5)
        segments = list(segments)  # The transcription will actually run here.
        #text = ''.join(segment.text for segment in segments)
        #print(text)
        dst_path = os.path.splitext(fullpath)[0] + ".gen.srt"
        create_srt_file(file_name=dst_path, results=segments, fast_whisper=True)
    except Exception as exc:
        comment = str (exc)


def main(config: Configuration) -> None:
    load_model(config["model_path"])
    src_path = config["path"]
    if os.path.isdir(src_path):
        for filename in os.listdir(src_path):
            file_rootname,file_extension = os.path.splitext(filename)
            if file_extension.lower() in ['.wav', '.mp4', '.webm', '.3gpp']:
                filepath = os.path.join(src_path, filename)
                process_audio(filepath)
    elif os.path.isfile(src_path):
        process_audio(src_path)


if __name__ == "__main__":
    logger.info("Program running")
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-p', '--path', type=str, help='Path to the file or the folder: C:\\dev\\data\\poc_a1.pdf')
    config = Configuration( __file__.replace('py', 'json'), parser)
    logger.info(config)
    main(config)