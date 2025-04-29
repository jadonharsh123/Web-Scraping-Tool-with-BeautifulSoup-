import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import json
import requests
from datetime import datetime
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import threading
import os
from PIL import Image, ImageTk
import webbrowser
import pandas as pd
from io import BytesIO
import re
import asyncio
import aiohttp
from playwright.async_api import async_playwright
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import spacy
from transformers import pipeline
import cv2
import pytesseract
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np
from pytube import YouTube
import moviepy.editor as mp
import cssselect
import lxml.html
import html5lib
from webdriver_manager.chrome import ChromeDriverManager
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import logging
from pathlib import Path
import shutil
import tempfile
import mimetypes
import magic
import chardet
import concurrent.futures
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import time
import random
import string

# Load environment variables
load_dotenv()

class ModernWebScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Ultimate Web Scraper")
        self.root.geometry("1600x1000")
        self.root.minsize(1400, 900)
        
        # Set theme colors
        self.bg_color = "#f0f0f0"
        self.accent_color = "#4a90e2"
        self.text_color = "#333333"
        
        # Configure root window
        self.root.configure(bg=self.bg_color)
        
        # Initialize AI models and scraping tools
        self.initialize_ai_models()
        self.initialize_scraping_tools()
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure('TButton', padding=5, background=self.accent_color, foreground='white')
        self.style.configure('TLabel', padding=5, background=self.bg_color, foreground=self.text_color)
        self.style.configure('TLabelframe', background=self.bg_color)
        self.style.configure('TLabelframe.Label', background=self.bg_color, foreground=self.accent_color)
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create header
        self.create_header()
        
        # Create sections
        self.create_url_section()
        self.create_options_section()
        self.create_results_section()
        self.create_status_bar()
        
        # Initialize variables
        self.scraped_data = {}
        self.current_url = ""
        self.is_scraping = False
        self.selenium_driver = None
        self.playwright_browser = None
        self.download_dir = Path(tempfile.mkdtemp())
        self.session = self.create_session()
        
    def create_header(self):
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Title
        title_label = ttk.Label(header_frame, text="Ultimate Web Scraper", 
                              font=('Helvetica', 24, 'bold'), 
                              foreground=self.accent_color)
        title_label.pack(side=tk.LEFT)
        
        # Version
        version_label = ttk.Label(header_frame, text="v2.0", 
                                font=('Helvetica', 12),
                                foreground=self.text_color)
        version_label.pack(side=tk.LEFT, padx=10)
        
    def create_url_section(self):
        url_frame = ttk.LabelFrame(self.main_frame, text="URL Input", padding="15")
        url_frame.pack(fill=tk.X, pady=10)
        
        # URL input with icon
        input_frame = ttk.Frame(url_frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(input_frame, text="🌐", font=('Helvetica', 14)).pack(side=tk.LEFT, padx=5)
        self.url_entry = ttk.Entry(input_frame, width=50, font=('Helvetica', 12))
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Buttons with icons
        button_frame = ttk.Frame(url_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        self.scrape_button = ttk.Button(button_frame, text="🔍 Scrape", 
                                      command=self.start_scraping,
                                      style='Accent.TButton')
        self.scrape_button.pack(side=tk.LEFT, padx=5)
        
        self.save_button = ttk.Button(button_frame, text="💾 Save All", 
                                    command=self.save_all_content)
        self.save_button.pack(side=tk.LEFT, padx=5)
        
    def create_options_section(self):
        options_frame = ttk.LabelFrame(self.main_frame, text="Scraping Options", padding="15")
        options_frame.pack(fill=tk.X, pady=10)
        
        # Create two columns of checkboxes
        left_frame = ttk.Frame(options_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        right_frame = ttk.Frame(options_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        # Create checkboxes with icons
        self.options = {
            'text': ('📝', tk.BooleanVar(value=True)),
            'images': ('🖼️', tk.BooleanVar(value=True)),
            'videos': ('🎥', tk.BooleanVar(value=True)),
            'audio': ('🔊', tk.BooleanVar(value=True)),
            'links': ('🔗', tk.BooleanVar(value=True)),
            'tables': ('📊', tk.BooleanVar(value=True)),
            'metadata': ('ℹ️', tk.BooleanVar(value=True)),
            'javascript': ('⚡', tk.BooleanVar(value=True)),
            'forms': ('📋', tk.BooleanVar(value=True)),
            'comments': ('💬', tk.BooleanVar(value=True)),
            'dynamic_content': ('🔄', tk.BooleanVar(value=True)),
            'css': ('🎨', tk.BooleanVar(value=True)),
            'fonts': ('🔤', tk.BooleanVar(value=True)),
            'icons': ('✨', tk.BooleanVar(value=True)),
            'logos': ('🏢', tk.BooleanVar(value=True)),
            'social_media': ('📱', tk.BooleanVar(value=True)),
            'contact_info': ('📞', tk.BooleanVar(value=True)),
            'prices': ('💰', tk.BooleanVar(value=True)),
            'reviews': ('⭐', tk.BooleanVar(value=True)),
            'products': ('🛍️', tk.BooleanVar(value=True))
        }
        
        # Split options between columns
        half = len(self.options) // 2
        for i, (option, (icon, var)) in enumerate(self.options.items()):
            frame = left_frame if i < half else right_frame
            cb = ttk.Checkbutton(frame, text=f"{icon} {option.replace('_', ' ').title()}", 
                               variable=var, style='TCheckbutton')
            cb.pack(side=tk.TOP, anchor=tk.W, pady=2)
            
        # Add depth option
        depth_frame = ttk.Frame(options_frame)
        depth_frame.pack(side=tk.RIGHT, padx=20)
        ttk.Label(depth_frame, text="🔍 Scraping Depth:").pack(side=tk.LEFT)
        self.depth_var = tk.StringVar(value="1")
        depth_spinbox = ttk.Spinbox(depth_frame, from_=1, to=5, 
                                  textvariable=self.depth_var, width=5)
        depth_spinbox.pack(side=tk.LEFT)
        
    def create_results_section(self):
        results_frame = ttk.Frame(self.main_frame)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create notebook for different result tabs
        self.notebook = ttk.Notebook(results_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs with icons
        self.tabs = {
            'text': self.create_text_tab(),
            'images': self.create_images_tab(),
            'videos': self.create_videos_tab(),
            'audio': self.create_audio_tab(),
            'links': self.create_links_tab(),
            'tables': self.create_tables_tab(),
            'metadata': self.create_metadata_tab(),
            'ai_analysis': self.create_ai_analysis_tab(),
            'dynamic_content': self.create_dynamic_content_tab(),
            'resources': self.create_resources_tab(),
            'social_media': self.create_social_media_tab(),
            'ecommerce': self.create_ecommerce_tab()
        }
        
    def create_images_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🖼️ Images")
        
        # Create canvas with scrollbar
        canvas = tk.Canvas(frame, bg=self.bg_color)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, padding=10)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        return scrollable_frame
        
    def process_images(self, soup):
        images = soup.find_all('img')
        row = 0
        col = 0
        max_cols = 4
        
        for img in images:
            try:
                img_url = img.get('src', '')
                if not img_url:
                    continue
                    
                if not img_url.startswith(('http://', 'https://')):
                    img_url = urljoin(self.current_url, img_url)
                    
                # Create image card
                card_frame = ttk.Frame(self.tabs['images'], padding=10, 
                                     style='Card.TFrame')
                card_frame.grid(row=row, column=col, padx=10, pady=10, 
                              sticky="nsew")
                
                # Download image
                response = self.session.get(img_url)
                if response.status_code == 200:
                    # Convert to PhotoImage
                    img_data = Image.open(BytesIO(response.content))
                    img_data.thumbnail((200, 200))
                    photo = ImageTk.PhotoImage(img_data)
                    
                    # Create label with image
                    label = ttk.Label(card_frame, image=photo)
                    label.image = photo  # Keep reference
                    label.pack()
                    
                    # Add URL label
                    url_label = ttk.Label(card_frame, text=img_url, 
                                        wraplength=200)
                    url_label.pack()
                    
                    # Add download button
                    download_btn = ttk.Button(card_frame, text="⬇️ Download",
                                           command=lambda u=img_url: self.download_image(u))
                    download_btn.pack(pady=5)
                    
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
                    
            except Exception as e:
                print(f"Error processing image: {str(e)}")
                
    def download_image(self, url):
        try:
            response = self.session.get(url, stream=True)
            if response.status_code == 200:
                filename = os.path.basename(url)
                with open(self.download_dir / filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                messagebox.showinfo("Success", "Image downloaded successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to download image: {str(e)}")
            
    def create_videos_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🎥 Videos")
        
        # Create canvas with scrollbar
        canvas = tk.Canvas(frame, bg=self.bg_color)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, padding=10)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        return scrollable_frame
        
    def process_videos(self, soup):
        videos = soup.find_all(['video', 'iframe'])
        
        for video in videos:
            try:
                if video.name == 'video':
                    src = video.get('src', '')
                    if not src:
                        continue
                else:  # iframe
                    src = video.get('src', '')
                    if not src or 'youtube' not in src.lower():
                        continue
                        
                if not src.startswith(('http://', 'https://')):
                    src = urljoin(self.current_url, src)
                    
                # Create video card
                card_frame = ttk.Frame(self.tabs['videos'], padding=10,
                                     style='Card.TFrame')
                card_frame.pack(fill=tk.X, padx=10, pady=10)
                
                # Add video preview (thumbnail for YouTube)
                if 'youtube' in src.lower():
                    try:
                        yt = YouTube(src)
                        thumbnail_url = yt.thumbnail_url
                        response = self.session.get(thumbnail_url)
                        if response.status_code == 200:
                            img_data = Image.open(BytesIO(response.content))
                            img_data.thumbnail((300, 200))
                            photo = ImageTk.PhotoImage(img_data)
                            label = ttk.Label(card_frame, image=photo)
                            label.image = photo
                            label.pack()
                    except:
                        pass
                
                # Add video URL
                url_label = ttk.Label(card_frame, text=src, wraplength=600)
                url_label.pack(pady=5)
                
                # Add download button
                download_btn = ttk.Button(card_frame, text="⬇️ Download",
                                       command=lambda s=src: self.download_video(s))
                download_btn.pack(pady=5)
                
            except Exception as e:
                print(f"Error processing video: {str(e)}")
                
    def create_status_bar(self):
        status_frame = ttk.Frame(self.main_frame)
        status_frame.pack(fill=tk.X, pady=10)
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var,
                               font=('Helvetica', 10))
        status_label.pack(side=tk.LEFT)
        
        # Add progress bar
        self.progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var,
                                     mode='determinate')
        progress_bar.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)
        
    def start_scraping(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a URL")
            return
            
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        self.current_url = url
        self.is_scraping = True
        self.status_var.set("Scraping...")
        self.progress_var.set(0)
        self.scrape_button.config(state='disabled')
        
        # Start scraping in a separate thread
        threading.Thread(target=self.scrape_website, daemon=True).start()
        
    def scrape_website(self):
        try:
            # Get page content using appropriate method
            if self.options['javascript'].get():
                content = self.scrape_with_selenium()
            else:
                response = self.session.get(self.current_url)
                content = response.text
                
            soup = BeautifulSoup(content, 'html.parser')
            
            # Process all content types
            self.process_all_content(soup)
            
            # Update progress
            self.progress_var.set(100)
            self.status_var.set("Scraping completed!")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.status_var.set("Error occurred")
        finally:
            self.is_scraping = False
            self.scrape_button.config(state='normal')
            
    def __del__(self):
        # Clean up resources
        if self.selenium_driver:
            self.selenium_driver.quit()
        if self.playwright_browser:
            asyncio.run(self.playwright_browser.close())
        # Clean up download directory
        if self.download_dir.exists():
            shutil.rmtree(self.download_dir)

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernWebScraperGUI(root)
    root.mainloop() 