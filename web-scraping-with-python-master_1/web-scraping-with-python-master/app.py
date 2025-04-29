from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import os
import json
from datetime import datetime
import threading
import tempfile
from pathlib import Path
import shutil
from pytube import YouTube
import asyncio
import aiohttp
from playwright.async_api import async_playwright
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import hashlib

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self):
        self.session = self.create_session()
        self.download_dir = Path(tempfile.mkdtemp())
        self.current_url = ""
        self.scraped_data = {}
        self.cache = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Create subdirectories
        self.images_dir = self.download_dir / "images"
        self.videos_dir = self.download_dir / "videos"
        self.text_dir = self.download_dir / "text"
        self.metadata_dir = self.download_dir / "metadata"
        
        # Create directories if they don't exist
        self.images_dir.mkdir(exist_ok=True)
        self.videos_dir.mkdir(exist_ok=True)
        self.text_dir.mkdir(exist_ok=True)
        self.metadata_dir.mkdir(exist_ok=True)
        
    def create_session(self):
        session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.1,
            status_forcelist=[500, 502, 503, 504]
        )
        session.mount('http://', HTTPAdapter(max_retries=retries, pool_connections=100, pool_maxsize=100))
        session.mount('https://', HTTPAdapter(max_retries=retries, pool_connections=100, pool_maxsize=100))
        return session

    @lru_cache(maxsize=1000)
    def get_page_content(self, url):
        try:
            response = self.session.get(url, timeout=10)
            return response.text
        except Exception as e:
            logger.error(f"Error fetching page: {str(e)}")
            return None

    async def scrape_with_playwright(self, url):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url, wait_until='networkidle', timeout=30000)
            content = await page.content()
            await browser.close()
            return content

    def process_images_parallel(self, soup):
        images = soup.find_all('img')
        image_data = []
        futures = []

        def download_image(img):
            try:
                img_url = img.get('src', '')
                if not img_url:
                    return None
                    
                if not img_url.startswith(('http://', 'https://')):
                    img_url = urljoin(self.current_url, img_url)
                    
                # Check cache first
                cache_key = hashlib.md5(img_url.encode()).hexdigest()
                if cache_key in self.cache:
                    return self.cache[cache_key]
                    
                # Download image
                response = self.session.get(img_url, timeout=10)
                if response.status_code == 200:
                    # Generate unique filename
                    filename = f"{hashlib.md5(img_url.encode()).hexdigest()[:8]}_{os.path.basename(img_url)}"
                    filepath = self.images_dir / filename
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                        
                    result = {
                        'url': img_url,
                        'filename': filename,
                        'path': str(filepath)
                    }
                    self.cache[cache_key] = result
                    return result
            except Exception as e:
                logger.error(f"Error processing image: {str(e)}")
                return None

        # Submit all image downloads to thread pool
        for img in images:
            futures.append(self.executor.submit(download_image, img))

        # Collect results as they complete
        for future in as_completed(futures):
            result = future.result()
            if result:
                image_data.append(result)
                socketio.emit('progress_update', {'type': 'image', 'count': len(image_data)})

        return image_data

    def process_videos_parallel(self, soup):
        videos = soup.find_all(['video', 'iframe'])
        video_data = []
        futures = []

        def process_video(video):
            try:
                if video.name == 'video':
                    src = video.get('src', '')
                    if not src:
                        return None
                else:  # iframe
                    src = video.get('src', '')
                    if not src or 'youtube' not in src.lower():
                        return None
                        
                if not src.startswith(('http://', 'https://')):
                    src = urljoin(self.current_url, src)
                    
                # Generate unique filename
                filename = f"{hashlib.md5(src.encode()).hexdigest()[:8]}_{os.path.basename(src)}"
                filepath = self.videos_dir / filename
                    
                return {
                    'url': src,
                    'type': 'youtube' if 'youtube' in src.lower() else 'video',
                    'filename': filename,
                    'path': str(filepath)
                }
            except Exception as e:
                logger.error(f"Error processing video: {str(e)}")
                return None

        # Process videos in parallel
        for video in videos:
            futures.append(self.executor.submit(process_video, video))

        # Collect results
        for future in as_completed(futures):
            result = future.result()
            if result:
                video_data.append(result)
                socketio.emit('progress_update', {'type': 'video', 'count': len(video_data)})

        return video_data

    def process_text(self, soup):
        text_data = {
            'title': soup.find('title').text if soup.find('title') else '',
            'paragraphs': [p.text.strip() for p in soup.find_all('p')],
            'headings': {
                'h1': [h.text.strip() for h in soup.find_all('h1')],
                'h2': [h.text.strip() for h in soup.find_all('h2')],
                'h3': [h.text.strip() for h in soup.find_all('h3')]
            },
            'links': [{'text': a.text.strip(), 'url': a.get('href', '')} 
                     for a in soup.find_all('a', href=True)]
        }
        
        # Save text data to file
        text_file = self.text_dir / "content.json"
        with open(text_file, 'w', encoding='utf-8') as f:
            json.dump(text_data, f, indent=2, ensure_ascii=False)
            
        return text_data

    def process_metadata(self, soup):
        metadata = {
            'description': soup.find('meta', attrs={'name': 'description'}).get('content', '') 
                         if soup.find('meta', attrs={'name': 'description'}) else '',
            'keywords': soup.find('meta', attrs={'name': 'keywords'}).get('content', '') 
                       if soup.find('meta', attrs={'name': 'keywords'}) else '',
            'author': soup.find('meta', attrs={'name': 'author'}).get('content', '') 
                     if soup.find('meta', attrs={'name': 'author'}) else '',
            'viewport': soup.find('meta', attrs={'name': 'viewport'}).get('content', '') 
                       if soup.find('meta', attrs={'name': 'viewport'}) else ''
        }
        
        # Save metadata to file
        metadata_file = self.metadata_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            
        return metadata

    def scrape_website(self, url, options):
        try:
            self.current_url = url
            self.scraped_data = {}
            
            # Get page content with caching
            content = self.get_page_content(url)
            if not content:
                return False
                
            soup = BeautifulSoup(content, 'html.parser')
            
            # Process content in parallel based on options
            futures = []
            
            if options.get('text', True):
                futures.append(self.executor.submit(self.process_text, soup))
                
            if options.get('images', True):
                futures.append(self.executor.submit(self.process_images_parallel, soup))
                
            if options.get('videos', True):
                futures.append(self.executor.submit(self.process_videos_parallel, soup))
                
            if options.get('metadata', True):
                futures.append(self.executor.submit(self.process_metadata, soup))
            
            # Collect results
            for future in as_completed(futures):
                result = future.result()
                if isinstance(result, dict):
                    self.scraped_data.update(result)
                elif isinstance(result, list):
                    if 'images' in self.scraped_data:
                        self.scraped_data['images'].extend(result)
                    else:
                        self.scraped_data['images'] = result
                    if 'videos' in self.scraped_data:
                        self.scraped_data['videos'].extend(result)
                    else:
                        self.scraped_data['videos'] = result
            
            return True
            
        except Exception as e:
            logger.error(f"Error scraping website: {str(e)}")
            return False

    def save_all_content(self, save_dir):
        try:
            # Create save directory
            save_path = Path(save_dir)
            save_path.mkdir(parents=True, exist_ok=True)
            
            # Copy all downloaded content
            for item in self.download_dir.glob('**/*'):
                if item.is_file():
                    rel_path = item.relative_to(self.download_dir)
                    target_path = save_path / rel_path
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target_path)
                
            # Save scraped data as JSON
            with open(save_path / 'scraped_data.json', 'w') as f:
                json.dump(self.scraped_data, f, indent=2)
                
            return True
            
        except Exception as e:
            logger.error(f"Error saving content: {str(e)}")
            return False

    def __del__(self):
        self.executor.shutdown()
        if self.download_dir.exists():
            shutil.rmtree(self.download_dir)

scraper = WebScraper()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    url = data.get('url')
    options = data.get('options', {})
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
        
    # Start scraping in a separate thread
    def scraping_thread():
        success = scraper.scrape_website(url, options)
        socketio.emit('scraping_complete', {'success': success})
        
    threading.Thread(target=scraping_thread).start()
    return jsonify({'message': 'Scraping started'})

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    save_dir = data.get('save_dir')
    
    if not save_dir:
        return jsonify({'error': 'Save directory is required'}), 400
        
    success = scraper.save_all_content(save_dir)
    if success:
        return jsonify({'message': 'Content saved successfully'})
    else:
        return jsonify({'error': 'Failed to save content'}), 500

@app.route('/download/video', methods=['POST'])
def download_video():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'Video URL is required'}), 400
        
    filename = scraper.download_video(url)
    if filename:
        return jsonify({'message': 'Video downloaded successfully', 'filename': filename})
    else:
        return jsonify({'error': 'Failed to download video'}), 500

if __name__ == '__main__':
    socketio.run(app, debug=True) 