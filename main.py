from decord                    import VideoReader
from pytube                    import YouTube
from pytesseract               import image_to_string
from re                        import findall
from googleapiclient.discovery import build
from dotenv                    import load_dotenv
from os                        import getenv
from datetime                  import datetime, timedelta, timezone
from dateutil                  import parser

load_dotenv()

YOUTUBE_API_KEY      = getenv('YOUTUBE_API_KEY')
YOUTUBE_USERNAME     = 'KSIOlajidebtHD'
YOUTUBE_CHANNEL_HOST = 'https://www.youtube.com/user/'

AWS_API_KEY       = getenv('AWS_API_KEY')
AMAZON_CODE_REGEX = '[A-Z0-9]*-[A-Z0-9]*-[A-Z0-9]*'

VIDEO_CROP_START_X = 45
VIDEO_CROP_END_X   = 210
VIDEO_CROP_START_Y = 65
VIDEO_CROP_END_Y   = 78
VIDEO_FRAME_SKIP   = 60
VIDEO_FILE_NAME    = 'video.mp4'
VIDEO_UPLOAD_CHECK_MINUTES = timedelta(minutes=5)

def download_video(url):
  YouTube(url=url).streams.filter(mime_type='video/mp4').order_by('resolution').first().download(filename = VIDEO_FILE_NAME)

def read_video(path):
  reader = VideoReader(path)
  return reader.get_batch(range(0, len(reader) - 1, VIDEO_FRAME_SKIP)).asnumpy()

def crop_video_frame(frame):
  return frame[VIDEO_CROP_START_Y:VIDEO_CROP_END_Y, VIDEO_CROP_START_X:VIDEO_CROP_END_X]

def detect_video_upload(youtube_api, channel_uploads_playlist_id):
  uploads_data = youtube_api.playlistItems().list(part='snippet', maxResults=1, playlistId=channel_uploads_playlist_id).execute()
  latest_upload = uploads_data['items'][0]

  if datetime.now(timezone.utc) <= parser.parse(latest_upload['snippet']['publishedAt']) + VIDEO_UPLOAD_CHECK_MINUTES:
    return latest_upload['snippet']['resourceId']['videoId']
  else:
    return ''

def get_channel_uploads_playlist_id(youtube_api):
  channel_data = youtube_api.channels().list(part='contentDetails', forUsername=YOUTUBE_USERNAME).execute()
  return channel_data['items'][0]['contentDetails']['relatedPlaylists']['uploads']

def main():
  youtube_api = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
  # aws_api = some api initialization

  channel_uploads_playlist_id = get_channel_uploads_playlist_id(youtube_api)

  while True:
    video_id = detect_video_upload(youtube_api, channel_uploads_playlist_id)
    print(video_id)

    if video_id:
      video_url = YOUTUBE_CHANNEL_HOST + video_id

      download_video(video_url)
      frames = read_video(VIDEO_FILE_NAME)

      for i in range(len(frames)):
        frame = crop_video_frame(frames[i])
        text  = image_to_string(frame).strip()
        
        try:
          code = findall(AMAZON_CODE_REGEX, text)[0]
          # AMAZON API MAGIC
          print(code)
        except:
          continue

main()
