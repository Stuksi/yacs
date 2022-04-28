from os import getenv
from dotenv import load_dotenv
from re import findall

load_dotenv()

# Video Processing

from pytube import YouTube
from decord import VideoReader

def download_youtube_video(video_url, video_filename):
  mp4_video_streams = YouTube(url = video_url).streams.filter('video/mp4')
  lowest_quality_stream = mp4_video_streams.order_by('resolution').first()
  lowest_quality_stream.download(filename = video_filename)

def get_video_frames(video_path, frame_skip_length):
  video_reader = VideoReader(video_path)
  video_reader_batch_indices = range(0, len(video_reader) - 1, frame_skip_length)

  return video_reader.get_batch(video_reader_batch_indices).asnumpy()

def crop_frame(frame, options):
  video_start_x = options['video_start_x']
  video_start_y = options['video_start_y']
  video_end_x = options['video_end_x']
  video_end_y = options['video_end_y']

  return frame[video_start_y:video_end_y, video_start_x:video_end_x]

# Youtube Detection

from googleapiclient.discovery import build

YOUTUBE_API_KEY = getenv('YOUTUBE_API_KEY')

Youtube_API = build('youtube', 'v3', developerKey = YOUTUBE_API_KEY)

def get_channel_uploads_playlist_id(username):
  channel_data = Youtube_API.channels().list(
    part = 'contentDetails',
    forUsername = username
  ).execute()
  uploads_playlist_id = channel_data['items'][0]['contentDetails']['relatedPlaylists']['uploads']

  return uploads_playlist_id

def get_lastest_channel_upload_id(uploads_playlist_id):
  uploads = Youtube_API.playlistItems().list(
    part = 'snippet',
    maxResults = 1,
    playlistId = uploads_playlist_id
  ).execute()
  latest_upload = uploads['items'][0]
  latest_upload_id = latest_upload['snippet']['resourceId']['videoId']

  return latest_upload_id

def has_channel_uploaded(uploads_playlist_id, previous_latest_channel_upload_id):
  latest_channel_upload_id = get_lastest_channel_upload_id(uploads_playlist_id)

  if latest_channel_upload_id != previous_latest_channel_upload_id:
    return latest_channel_upload_id
  else:
    return ''

# Amazon Code Activation

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support    import expected_conditions
from selenium.webdriver.common.by  import By

WAITING_TIMEOUT = 5
CURRENT_ACCOUNT_INDEX = 0

AMAZON_ACCOUNT_EMAILS = getenv('AMAZON_ACCOUNT_EMAILS').split(',')
AMAZON_ACCOUNT_PASSWORDS = getenv('AMAZON_ACCOUNT_PASSWORDS').split(',')
AMAZON_GIFT_CARD_LINK = 'https://www.amazon.co.uk/gc/redeem?ref_=gcui_b_e_r_c_d'

web_driver_options = webdriver.ChromeOptions()
web_driver_options.add_argument('--incognito')

web_driver = webdriver.Chrome(options=web_driver_options)

def open_link(url):
  web_driver.get(url = url)

def wait_until_present_id(element_id):
  WebDriverWait(web_driver, WAITING_TIMEOUT).until(expected_conditions.presence_of_element_located((By.ID, element_id)))

def login(email, password):
  wait_until_present_id('ap_email')

  email_input = web_driver.find_element_by_id('ap_email')
  password_input = web_driver.find_element_by_id('ap_password')
  sign_in_button = web_driver.find_element_by_id('signInSubmit')

  email_input.send_keys(email)
  password_input.send_keys(password)
  sign_in_button.click()

def activate_code(code):
  wait_until_present_id('gc-redemption-input')

  code_input = web_driver.find_element_by_id('gc-redemption-input')
  apply_button = web_driver.find_element_by_id('gc-redemption-apply-button')

  code_input.send_keys(code)
  apply_button.click()

def activate_code_for_current_user(code):
  email = AMAZON_ACCOUNT_EMAILS[CURRENT_ACCOUNT_INDEX]
  password = AMAZON_ACCOUNT_EMAILS[CURRENT_ACCOUNT_INDEX]

  open_link(AMAZON_GIFT_CARD_LINK)
  login(email, password)
  activate_code(code)

  if web_driver.find_element_by_id('gc-captcha-image'):
    CURRENT_ACCOUNT_INDEX = CURRENT_ACCOUNT_INDEX + 1

  web_driver.close()

# Main

from pytesseract import image_to_string

YOUTUBE_CHANNEL_HOST = 'https://www.youtube.com/user/'
YOUTUBE_USERNAME = 'KSIOlajidebtHD'

VIDEO_FILE_NAME = 'video.mp4'
VIDEO_CROP_OPTIONS = {
  'video_start_x': 45,
  'video_start_y': 65,
  'video_end_x': 210,
  'video_end_y': 78
}

AMAZON_CODE_REGEX = '[A-Z0-9]*-[A-Z0-9]*-[A-Z0-9]*'

def search_frames_for_codes_and_activate(frames):
  for i in reversed(range(len(frames))):
    frame = crop_frame(frames[i])
    text  = image_to_string(frame).strip()

    try:
      code = findall(AMAZON_CODE_REGEX, text)[0]
      activate_code_for_current_user(code)
    except:
      continue

def main():
  channel_uploads_playlist_id = get_channel_uploads_playlist_id(YOUTUBE_USERNAME)
  latest_channel_upload = get_lastest_channel_upload_id(channel_uploads_playlist_id)

  while True:
    video_id = has_channel_uploaded(channel_uploads_playlist_id, latest_channel_upload)

    if video_id:
      video_url = YOUTUBE_CHANNEL_HOST + video_id
      download_youtube_video(video_url)
      frames = get_video_frames(VIDEO_FILE_NAME)
      search_frames_for_codes_and_activate(frames)
      latest_channel_upload = video_id

main()
