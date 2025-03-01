import os
import re
import requests
from urllib.parse import urlparse, parse_qs
from tqdm import tqdm
from typing import Optional
import subprocess
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Initialize the MediaDownloader
class MediaDownloader:
    """Multi-platform media downloader for social media content without ffmpeg dependency."""

    QUALITY_OPTIONS = {
        "1": {"resolution": "144p", "format_id": "best[height<=144]/worst"},
        "2": {"resolution": "240p", "format_id": "best[height<=240]/worst"},
        "3": {"resolution": "360p", "format_id": "best[height<=360]/worst"},
        "4": {"resolution": "480p", "format_id": "best[height<=480]/worst"},
        "5": {"resolution": "720p", "format_id": "best[height<=720]/worst"},
        "6": {"resolution": "1080p", "format_id": "best[height<=1080]/worst"},
        "7": {"resolution": "Best available", "format_id": "best"}
    }

    def __init__(self, output_dir: str = "downloads"):
        """Initialize the downloader with configuration."""
        self.output_dir = output_dir
        self.create_output_dir()
        self.selected_quality = "7"  # Default to best quality

    def create_output_dir(self):
        """Create output directory if it doesn't exist."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def detect_platform(self, url: str) -> str:
        """Detect which platform the URL belongs to."""
        domain = urlparse(url).netloc.lower()
        path = urlparse(url).path.lower()

        if "reddit.com" in domain or "/r/" in path:
            return "reddit"
        elif any(x in domain for x in ["instagram", "instagr.am"]):
            return "instagram"
        elif any(x in domain for x in ["facebook", "fb.com", "fb.watch"]):
            return "facebook"
        elif any(x in domain for x in ["twitter", "x.com", "t.co"]):
            return "twitter"
        elif any(x in domain for x in ["tiktok", "tiktok.com", "vm.tiktok"]):
            return "tiktok"
        elif any(x in domain for x in ["youtube", "youtu.be"]):
            return "youtube"
        elif "pinterest" in domain:
            return "pinterest"
        else:
            raise ValueError(f"Unsupported platform: {domain}")

    def get_original_filename(self, url: str, platform: str, response_content: str = None) -> str:
        """Extract original filename from URL or metadata."""
        original_name = None

        try:
            if platform == "youtube":
                # Get original YouTube video title using yt-dlp
                try:
                    command = [
                        'yt-dlp',
                        '--get-title',
                        '--no-playlist',
                        url
                    ]
                    result = subprocess.run(command, capture_output=True, text=True)
                    if result.returncode == 0 and result.stdout.strip():
                        original_name = result.stdout.strip()
                        original_name = re.sub(r'[\\/*?:"<>|]', "", original_name)
                        print(f"Extracted YouTube title: {original_name}")
                    else:
                        print(f"yt-dlp title extraction failed: {result.stderr}")
                        # Fall back to YouTube API if installed
                        try:
                            from pytube import YouTube
                            yt = YouTube(url)
                            original_name = yt.title
                            original_name = re.sub(r'[\\/*?:"<>|]', "", original_name)
                            print(f"Extracted YouTube title using pytube: {original_name}")
                        except Exception as e:
                            print(f"pytube title extraction failed: {e}")
                except Exception as e:
                    print(f"Command-line title extraction failed: {e}")

            elif platform == "instagram":
                if response_content:
                    title_match = re.search(r'<meta property="og:title" content="([^"]+)"', response_content)
                    if title_match:
                        original_name = title_match.group(1).split(" on Instagram")[0].strip()
                        original_name = f"instagram_{original_name}"

            elif platform == "twitter":
                if response_content:
                    title_match = re.search(r'<meta property="og:description" content="([^"]+)"', response_content)
                    if title_match:
                        words = title_match.group(1).split()[:5]
                        original_name = f"twitter_{'_'.join(words)}"
                        original_name = re.sub(r'[\\/*?:"<>|]', "", original_name)

            elif platform == "reddit":
                if response_content:
                    title_match = re.search(r'<meta property="og:title" content="([^"]+)"', response_content)
                    if title_match:
                        words = title_match.group(1).split()[:5]
                        original_name = f"reddit_{'_'.join(words)}"
                        original_name = re.sub(r'[\\/*?:"<>|]', "", original_name)
                else:
                    parsed_url = urlparse(url)
                    path_parts = parsed_url.path.strip("/").split("/")
                    if len(path_parts) >= 3 and path_parts[0] == "r":
                        subreddit = path_parts[1]
                        post_id = path_parts[3] if len(path_parts) >= 4 else "post"
                        original_name = f"reddit_{subreddit}_{post_id}"

            if not original_name:
                parsed_url = urlparse(url)
                path_parts = parsed_url.path.strip("/").split("/")

                if len(path_parts) > 0:
                    last_part = path_parts[-1]
                    if last_part and len(last_part) > 0:
                        original_name = f"{platform}_{last_part}"

        except Exception as e:
            print(f"Could not extract original filename: {e}")

        if not original_name:
            parsed_url = urlparse(url)
            path_parts = parsed_url.path.strip("/").split("/")
            if platform == "youtube":
                video_id = parse_qs(parsed_url.query).get('v', [''])[0]
                if not video_id and 'youtu.be' in url:
                    video_id = parsed_url.path.strip('/')
                elif not video_id:
                    video_id = path_parts[-1]
                original_name = f"youtube_{video_id}"
            else:
                original_name = f"{platform}_{path_parts[-1] if path_parts else 'media'}"

        original_name = re.sub(r'[\\/*?:"<>|]', "_", original_name)
        if len(original_name) > 100:
            original_name = original_name[:100]

        return original_name

    def download(self, url: str, selected_quality: str = "7", output_name: Optional[str] = None) -> str:
        """Main download method that routes to appropriate platform handler."""
        self.selected_quality = selected_quality
        platform = self.detect_platform(url)
        print(f"Detected platform: {platform}")

        if platform == "youtube" and "/shorts/" in url:
            print("Detected YouTube Shorts video")
            video_id = url.split("/shorts/")[1].split("?")[0]
            url = f"https://www.youtube.com/watch?v={video_id}"
            print(f"Converted to standard YouTube URL: {url}")

        response_content = None
        if platform in ["instagram", "facebook", "twitter", "reddit"] and not output_name:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(url, headers=headers)
                response_content = response.text
            except Exception as e:
                print(f"Could not fetch preliminary data: {e}")

        if not output_name:
            output_name = self.get_original_filename(url, platform, response_content)

        platform_dir = os.path.join(self.output_dir, platform)
        if not os.path.exists(platform_dir):
            os.makedirs(platform_dir)

        output_path = os.path.join(platform_dir, output_name)

        try:
            return self._use_youtube_dl(url, output_path)
        except Exception as e:
            print(f"youtube-dl method failed: {e}")
            print("Falling back to platform-specific method...")
            if platform == "instagram":
                return self.download_instagram(url, output_path, response_content)
            elif platform == "facebook":
                return self.download_facebook(url, output_path, response_content)
            elif platform == "twitter":
                return self.download_twitter(url, output_path, response_content)
            elif platform == "tiktok":
                return self.download_tiktok(url, output_path)
            elif platform == "pinterest":
                return self.download_pinterest(url, output_path)
            elif platform == "reddit":
                return self.download_reddit(url, output_path, response_content)
            elif platform == "youtube":
                try:
                    return self.download_youtube(url, output_path)
                except Exception as e2:
                    return f"All download methods failed: {e2}"

    def download_instagram(self, url: str, output_path: str, response_content: str = None) -> str:
        """Download media from Instagram without authentication."""
        try:
            if not response_content:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(url, headers=headers)
                response_content = response.text

            video_urls = re.findall(r'<meta property="og:video" content="([^"]+)"', response_content)
            if video_urls:
                video_path = f"{output_path}.mp4"
                self._download_file(video_urls[0], video_path)
                return f"Downloaded Instagram video to {video_path}"

            image_urls = re.findall(r'<meta property="og:image" content="([^"]+)"', response_content)
            if image_urls:
                image_path = f"{output_path}.jpg"
                self._download_file(image_urls[0], image_path)
                return f"Downloaded Instagram image to {image_path}"

            return "No media found in Instagram post"

        except Exception as e:
            return f"Instagram download error: {e}"

    def download_facebook(self, url: str, output_path: str, response_content: str = None) -> str:
        """Download media from Facebook without authentication."""
        try:
            if not response_content:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(url, headers=headers)
                response_content = response.text

            video_urls = re.findall(r'<meta property="og:video" content="([^"]+)"', response_content)
            if video_urls:
                video_path = f"{output_path}.mp4"
                self._download_file(video_urls[0], video_path)
                return f"Downloaded Facebook video to {video_path}"

            image_urls = re.findall(r'<meta property="og:image" content="([^"]+)"', response_content)
            if image_urls:
                image_path = f"{output_path}.jpg"
                self._download_file(image_urls[0], image_path)
                return f"Downloaded Facebook image to {image_path}"

            return "No media found in Facebook post"

        except Exception as e:
            return f"Facebook download error: {e}"

    def download_twitter(self, url: str, output_path: str, response_content: str = None) -> str:
        """Download media from Twitter/X without authentication."""
        try:
            if not response_content:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(url, headers=headers)
                response_content = response.text

            video_urls = re.findall(r'<meta property="og:video" content="([^"]+)"', response_content)
            if video_urls:
                video_path = f"{output_path}.mp4"
                self._download_file(video_urls[0], video_path)
                return f"Downloaded Twitter/X video to {video_path}"

            image_urls = re.findall(r'<meta property="og:image" content="([^"]+)"', response_content)
            if image_urls:
                media_urls = [url for url in image_urls if 'profile_images' not in url]
                if media_urls:
                    image_path = f"{output_path}.jpg"
                    self._download_file(media_urls[0], image_path)
                    return f"Downloaded Twitter/X image to {image_path}"
            return "No media found in Twitter/X post"

        except Exception as e:
            return f"Twitter/X download error: {e}"

    def download_tiktok(self, url: str, output_path: str) -> str:
        """Download videos from TikTok without authentication."""
        try:
            tiktok_api_url = f"https://www.tikwm.com/api/?url={url}"
            response = requests.get(tiktok_api_url)
            data = response.json()

            if data.get("success"):
                video_url = data.get("data", {}).get("play")
                if video_url:
                    video_path = f"{output_path}.mp4"
                    self._download_file(video_url, video_path)
                    return f"Downloaded TikTok video to {video_path}"

            return "Failed to download TikTok video. Try using youtube-dl directly."

        except Exception as e:
            return f"TikTok download error: {e}"

    def download_youtube(self, url: str, output_path: str) -> str:
        """Download videos from YouTube using pytube as an alternative."""
        try:
            from pytube import YouTube
        except ImportError:
            print("pytube not found. Installing...")
            os.system("pip install pytube")
            from pytube import YouTube

        try:
            yt = YouTube(url)
            # Get the original title first
            original_name = yt.title
            original_name = re.sub(r'[\\/*?:"<>|]', "_", original_name)
            if len(original_name) > 100:
                original_name = original_name[:100]
                
            # Set output path with original title
            new_output_path = os.path.dirname(output_path) + os.sep + original_name
            
            # Download the video
            stream = yt.streams.get_highest_resolution()
            stream.download(filename=new_output_path)
            return f"Downloaded YouTube video to {new_output_path}"
        except Exception as e:
            print(f"pytube download error: {e}")
            raise

    def download_reddit(self, url: str, output_path: str, response_content: str = None) -> str:
        """Download media from Reddit without authentication."""
        try:
            if not response_content:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(url, headers=headers)
                response_content = response.text

            video_urls = re.findall(r'<meta property="og:video" content="([^"]+)"', response_content)
            video_urls += re.findall(r'<meta property="og:video:secure_url" content="([^"]+)"', response_content)

            if video_urls:
                video_path = f"{output_path}.mp4"
                self._download_file(video_urls[0], video_path)
                return f"Downloaded Reddit video to {video_path}"

            image_urls = re.findall(r'<meta property="og:image" content="([^"]+)"', response_content)
            if image_urls:
                media_urls = [url for url in image_urls if 'external-preview' in url or 'i.redd.it' in url]
                if media_urls:
                    image_path = f"{output_path}.jpg"
                    self._download_file(media_urls[0], image_path)
                    return f"Downloaded Reddit image to {image_path}"

            return "No media found in Reddit post. Try using youtube-dl with --verbose flag to debug."

        except Exception as e:
            return f"Reddit download error: {e}"

    def download_pinterest(self, url: str, output_path: str) -> str:
        """Download images from Pinterest."""
        return "Pinterest download not implemented. Try using youtube-dl directly."

    def _download_file(self, url: str, output_path: str):
        """Helper method to download a file from a URL with progress bar."""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            block_size = 8192

            with tqdm(total=total_size, unit='B', unit_scale=True, desc=output_path, ascii=True) as pbar:
                with open(output_path, 'wb') as file:
                    for data in response.iter_content(block_size):
                        file.write(data)
                        pbar.update(len(data))
        except requests.exceptions.RequestException as e:
            print(f"Download failed: {e}")
            raise
        except IOError as e:
            print(f"IOError: {e}")
            raise

    def _use_youtube_dl(self, url: str, output_path: str) -> str:
        """Use yt-dlp to download media from various platforms, capturing output."""
        try:
            quality_format = self.QUALITY_OPTIONS[self.selected_quality]['format_id']

            # Get original filename for YouTube first
            if "youtube.com" in url or "youtu.be" in url:
                # Extract title first using get-title
                title_command = [
                    'yt-dlp',
                    '--get-title',
                    '--no-playlist',
                    url
                ]
                try:
                    title_result = subprocess.run(title_command, capture_output=True, text=True)
                    if title_result.returncode == 0 and title_result.stdout.strip():
                        original_title = title_result.stdout.strip()
                        original_title = re.sub(r'[\\/*?:"<>|]', "_", original_title)
                        if len(original_title) > 100:
                            original_title = original_title[:100]
                        output_path = os.path.dirname(output_path) + os.sep + original_title
                        print(f"Using YouTube original title: {original_title}")
                except Exception as e:
                    print(f"Failed to get YouTube title: {e}")

            output_template = f'{output_path}.%(ext)s'

            if "reddit.com" in url:
                command = [
                    'yt-dlp',
                    '--verbose',
                    '--merge-output-format', 'mp4',
                    '--embed-metadata',
                    '--add-metadata',
                    '-o', output_template,
                    url
                ]
            else:
                command = [
                    'yt-dlp',
                    '-o', output_template,
                    '--format', quality_format,
                    '--merge-output-format', 'mp4',
                    url
                ]

            print(f"Running command: {' '.join(command)}")
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()

            print("yt-dlp stdout:\n", stdout.decode('utf-8'))
            print("yt-dlp stderr:\n", stderr.decode('utf-8'))

            if process.returncode != 0:
                print("Selected format not available. Trying without format specification...")
                command.remove('--format')
                if quality_format in command:
                    command.remove(quality_format)

                print(f"Running fallback command: {' '.join(command)}")
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()

                print("yt-dlp stdout (fallback):\n", stdout.decode('utf-8'))
                print("yt-dlp stderr (fallback):\n", stderr.decode('utf-8'))

                if process.returncode != 0:
                    raise Exception(f"yt-dlp exited with code {process.returncode}")

            return f"Downloaded to {output_path}"
        except Exception as e:
            print(f"yt-dlp download error: {e}")
            raise

downloader = MediaDownloader()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    selected_quality = request.form.get('selected_quality', '7')
    try:
        result = downloader.download(url, selected_quality)
        return render_template('index.html', result=result)
    except Exception as e:
        return render_template('index.html', result=f"Download failed: {e}")

if __name__ == '__main__':
    app.run(debug=True)