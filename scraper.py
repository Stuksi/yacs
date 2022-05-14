from genericpath import exists
from os import getenv, remove, path
from dotenv import load_dotenv
from re import findall

load_dotenv()

# Video

from pytube import YouTube
from decord import VideoReader

AMAZON_CODE_REGEX = '[A-Z0-9]*-[A-Z0-9]*-[A-Z0-9]*'

VIDEO_FILE_NAME = 'video.mp4'
VIDEO_FRAME_SKIP = 60
VIDEO_CROP_OPTIONS = {
  'video_start_x': 45,
  'video_start_y': 65,
  'video_end_x': 210,
  'video_end_y': 78
}

def download_youtube_video(upload_url):
  if path.exists(VIDEO_FILE_NAME):
    remove(VIDEO_FILE_NAME)

  mp4_video_streams = YouTube(url = upload_url).streams.filter(mime_type = 'video/mp4')
  lowest_quality_stream = mp4_video_streams.order_by('resolution').first()
  lowest_quality_stream.download(filename = VIDEO_FILE_NAME)

def get_video_frames_from_downloaded_video():
  video_reader = VideoReader(VIDEO_FILE_NAME)
  video_reader_batch_indices = range(0, len(video_reader) - 1, VIDEO_FRAME_SKIP)

  return video_reader.get_batch(video_reader_batch_indices).asnumpy()

def crop_frame(frame, options):
  video_start_x = options['video_start_x']
  video_start_y = options['video_start_y']
  video_end_x = options['video_end_x']
  video_end_y = options['video_end_y']

  return frame[video_start_y:video_end_y, video_start_x:video_end_x]

def search_frames_for_codes_and_activate(frames):
  for i in reversed(range(len(frames))):
    frame = crop_frame(frames[i], VIDEO_CROP_OPTIONS)
    text  = image_to_string(frame).strip()

    try:
      code = findall(AMAZON_CODE_REGEX, text)[0]
      activate_code_for_current_user(code)
    except:
      continue

# Youtube

from googleapiclient.discovery import build

YOUTUBE_API_KEY = getenv('YOUTUBE_API_KEY')
YOUTUBE_HOST = 'https://www.youtube.com/'
YOUTUBE_CACHE_FILE = '.youtube-cache'

Youtube_API = build('youtube', 'v3', developerKey = YOUTUBE_API_KEY)

def get_youtube_video_url(video_id):
  return YOUTUBE_HOST + 'watch?v=' + video_id

def get_channel_uploads_playlist_id(channel_id):
  channel_data = Youtube_API.channels().list(
    part = 'contentDetails',
    id = channel_id
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

def has_channel_uploaded(uploads_playlist_id, cached_upload_id):
  latest_channel_upload_id = get_lastest_channel_upload_id(uploads_playlist_id)

  if latest_channel_upload_id != cached_upload_id:
    return latest_channel_upload_id
  else:
    return ''

def get_cached_upload_id():
  if not exists(YOUTUBE_CACHE_FILE):
    return ''

  cache = open(YOUTUBE_CACHE_FILE, 'r')
  upload_id = cache.read()

  return upload_id

def cache_upload_id(upload_id):
  cache = open(YOUTUBE_CACHE_FILE, 'w+')
  cache.truncate()
  cache.write(upload_id)

# Amazon

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support    import expected_conditions
from selenium.webdriver.common.by  import By

WAITING_TIMEOUT = 10
CURRENT_ACCOUNT_INDEX = 0

AMAZON_ACCOUNT_EMAILS = getenv('AMAZON_ACCOUNT_EMAILS').split(',')
AMAZON_ACCOUNT_PASSWORDS = getenv('AMAZON_ACCOUNT_PASSWORDS').split(',')
AMAZON_GIFT_CARD_LINK = 'https://www.amazon.co.uk/gc/redeem?ref_=gcui_b_e_r_c_d'

Web_Driver = None

def open_link(url):
  Web_Driver.get(url = url)

def wait_until_present_id(element_id):
  WebDriverWait(Web_Driver, WAITING_TIMEOUT).until(expected_conditions.presence_of_element_located((By.ID, element_id)))

def login(email, password):
  wait_until_present_id('ap_email')

  email_input = Web_Driver.find_element(by = By.ID, value = 'ap_email')
  password_input = Web_Driver.find_element(by = By.ID, value = 'ap_password')
  sign_in_button = Web_Driver.find_element(by = By.ID, value = 'signInSubmit')

  email_input.send_keys(email)
  password_input.send_keys(password)
  sign_in_button.click()

def activate_code(code):
  wait_until_present_id('gc-redemption-input')

  code_input = Web_Driver.find_element(by = By.ID, value = 'gc-redemption-input')
  apply_button = Web_Driver.find_element(by = By.ID, value = 'gc-redemption-apply-button')

  code_input.send_keys(code)
  apply_button.click()

def activate_code_for_current_user(code):
  global CURRENT_ACCOUNT_INDEX
  global Web_Driver

  web_driver_options = webdriver.ChromeOptions()
  web_driver_options.add_argument('--incognito')
  Web_Driver = webdriver.Chrome(options=web_driver_options)

  email = AMAZON_ACCOUNT_EMAILS[CURRENT_ACCOUNT_INDEX]
  password = AMAZON_ACCOUNT_PASSWORDS[CURRENT_ACCOUNT_INDEX]

  open_link(AMAZON_GIFT_CARD_LINK)
  login(email, password)
  activate_code(code)

  if Web_Driver.find_element(by = By.ID, value = 'gc-captcha-image'):
    CURRENT_ACCOUNT_INDEX = CURRENT_ACCOUNT_INDEX + 1

# Main

from pytesseract import image_to_string

YOUTUBE_CHANNEL_ID = 'UCGmnsW623G1r-Chmo5RB4Yw' # Hard-coded JJ Olatunji channel ID

channel_uploads_playlist_id = get_channel_uploads_playlist_id(YOUTUBE_CHANNEL_ID)

cached_upload_id = get_cached_upload_id()

if not cached_upload_id:
  latest_channel_upload_id = get_lastest_channel_upload_id(channel_uploads_playlist_id)
  cache_upload_id(latest_channel_upload_id)
  cached_upload_id = latest_channel_upload_id

new_upload_id = has_channel_uploaded(channel_uploads_playlist_id, cached_upload_id)

if new_upload_id:
  cache_upload_id(new_upload_id)
  upload_url = get_youtube_video_url(new_upload_id)
  download_youtube_video(upload_url)
  frames = get_video_frames_from_downloaded_video()
  search_frames_for_codes_and_activate(frames)
