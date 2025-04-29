import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import json
import requests
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import threading
import os
from PIL import Image, ImageTk
import webbrowser
import pandas as pd
from io import BytesIO
import re

class WebScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Web Scraper")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure('TButton', padding=5)
        self.style.configure('TLabel', padding=5)
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create URL input section
        self.create_url_section()
        
        # Create scraping options section
        self.create_options_section()
        
        # Create results section
        self.create_results_section()
        
        # Create status bar
        self.create_status_bar()
        
        # Initialize variables
        self.scraped_data = {}
        self.current_url = ""
        self.is_scraping = False
        
    def create_url_section(self):
        url_frame = ttk.LabelFrame(self.main_frame, text="URL Input", padding="10")
        url_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(url_frame, text="Enter URL:").pack(side=tk.LEFT, padx=5)
        self.url_entry = ttk.Entry(url_frame, width=50)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.scrape_button = ttk.Button(url_frame, text="Scrape", command=self.start_scraping)
        self.scrape_button.pack(side=tk.LEFT, padx=5)
        
    def create_options_section(self):
        options_frame = ttk.LabelFrame(self.main_frame, text="Scraping Options", padding="10")
        options_frame.pack(fill=tk.X, pady=5)
        
        # Create checkboxes for different data types
        self.options = {
            'text': tk.BooleanVar(value=True),
            'images': tk.BooleanVar(value=True),
            'links': tk.BooleanVar(value=True),
            'tables': tk.BooleanVar(value=True),
            'metadata': tk.BooleanVar(value=True)
        }
        
        for option, var in self.options.items():
            ttk.Checkbutton(options_frame, text=option.capitalize(), variable=var).pack(side=tk.LEFT, padx=10)
            
        # Add depth option
        ttk.Label(options_frame, text="Scraping Depth:").pack(side=tk.LEFT, padx=5)
        self.depth_var = tk.StringVar(value="1")
        depth_spinbox = ttk.Spinbox(options_frame, from_=1, to=5, textvariable=self.depth_var, width=5)
        depth_spinbox.pack(side=tk.LEFT, padx=5)
        
    def create_results_section(self):
        results_frame = ttk.Frame(self.main_frame)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create notebook for different result tabs
        self.notebook = ttk.Notebook(results_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.tabs = {
            'text': self.create_text_tab(),
            'images': self.create_images_tab(),
            'links': self.create_links_tab(),
            'tables': self.create_tables_tab(),
            'metadata': self.create_metadata_tab()
        }
        
    def create_text_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Text Content")
        
        text_widget = scrolledtext.ScrolledText(frame, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        return text_widget
        
    def create_images_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Images")
        
        # Create canvas with scrollbar
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        return scrollable_frame
        
    def create_links_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Links")
        
        # Create treeview for links
        columns = ('url', 'text')
        tree = ttk.Treeview(frame, columns=columns, show='headings')
        
        # Define headings
        tree.heading('url', text='URL')
        tree.heading('text', text='Link Text')
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        return tree
        
    def create_tables_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Tables")
        
        # Create treeview for tables
        tree = ttk.Treeview(frame)
        tree.pack(fill=tk.BOTH, expand=True)
        
        return tree
        
    def create_metadata_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Metadata")
        
        text_widget = scrolledtext.ScrolledText(frame, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        return text_widget
        
    def create_status_bar(self):
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
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
        self.scrape_button.config(state='disabled')
        
        # Start scraping in a separate thread
        threading.Thread(target=self.scrape_website, daemon=True).start()
        
    def scrape_website(self):
        try:
            response = requests.get(self.current_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                self.process_scraped_data(soup)
            else:
                messagebox.showerror("Error", f"Failed to access URL. Status code: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            self.is_scraping = False
            self.status_var.set("Ready")
            self.scrape_button.config(state='normal')
            
    def process_scraped_data(self, soup):
        # Clear previous data
        for widget in self.tabs['images'].winfo_children():
            widget.destroy()
            
        # Process text content
        if self.options['text'].get():
            text_content = self.extract_text_content(soup)
            self.tabs['text'].delete(1.0, tk.END)
            self.tabs['text'].insert(tk.END, text_content)
            
        # Process images
        if self.options['images'].get():
            self.process_images(soup)
            
        # Process links
        if self.options['links'].get():
            self.process_links(soup)
            
        # Process tables
        if self.options['tables'].get():
            self.process_tables(soup)
            
        # Process metadata
        if self.options['metadata'].get():
            self.process_metadata(soup)
            
    def extract_text_content(self, soup):
        text_content = []
        
        # Extract headings
        for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            for heading in soup.find_all(tag):
                text_content.append(f"{tag.upper()}: {heading.get_text().strip()}\n")
                
        # Extract paragraphs
        for paragraph in soup.find_all('p'):
            text_content.append(paragraph.get_text().strip() + "\n")
            
        return "\n".join(text_content)
        
    def process_images(self, soup):
        images = soup.find_all('img')
        row = 0
        col = 0
        max_cols = 3
        
        for img in images:
            try:
                img_url = img.get('src', '')
                if not img_url:
                    continue
                    
                if not img_url.startswith(('http://', 'https://')):
                    img_url = urlparse(self.current_url).scheme + '://' + urlparse(self.current_url).netloc + img_url
                    
                # Download image
                response = requests.get(img_url)
                if response.status_code == 200:
                    # Create image frame
                    img_frame = ttk.Frame(self.tabs['images'])
                    img_frame.grid(row=row, column=col, padx=5, pady=5)
                    
                    # Convert to PhotoImage
                    img_data = Image.open(BytesIO(response.content))
                    img_data.thumbnail((200, 200))
                    photo = ImageTk.PhotoImage(img_data)
                    
                    # Create label with image
                    label = ttk.Label(img_frame, image=photo)
                    label.image = photo  # Keep reference
                    label.pack()
                    
                    # Add URL label
                    ttk.Label(img_frame, text=img_url, wraplength=200).pack()
                    
                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1
            except Exception as e:
                print(f"Error processing image: {str(e)}")
                
    def process_links(self, soup):
        # Clear previous items
        for item in self.tabs['links'].get_children():
            self.tabs['links'].delete(item)
            
        # Add new links
        for link in soup.find_all('a'):
            url = link.get('href', '')
            text = link.get_text().strip()
            
            if url:
                if not url.startswith(('http://', 'https://')):
                    url = urlparse(self.current_url).scheme + '://' + urlparse(self.current_url).netloc + url
                    
                self.tabs['links'].insert('', 'end', values=(url, text))
                
    def process_tables(self, soup):
        # Clear previous items
        for item in self.tabs['tables'].get_children():
            self.tabs['tables'].delete(item)
            
        # Process tables
        tables = soup.find_all('table')
        for i, table in enumerate(tables):
            # Create frame for table
            table_frame = ttk.Frame(self.tabs['tables'])
            table_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Add table number
            ttk.Label(table_frame, text=f"Table {i+1}").pack()
            
            # Create treeview for table data
            columns = []
            for th in table.find_all('th'):
                columns.append(th.get_text().strip())
                
            if not columns:
                # If no headers, use column numbers
                max_cols = max(len(row.find_all(['td', 'th'])) for row in table.find_all('tr'))
                columns = [f"Column {i+1}" for i in range(max_cols)]
                
            tree = ttk.Treeview(table_frame, columns=columns, show='headings')
            
            # Configure columns
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=100)
                
            # Add data
            for row in table.find_all('tr')[1:]:  # Skip header row
                cells = row.find_all(['td', 'th'])
                values = [cell.get_text().strip() for cell in cells]
                tree.insert('', 'end', values=values)
                
            tree.pack(fill=tk.X)
            
    def process_metadata(self, soup):
        metadata = []
        
        # Title
        title = soup.find('title')
        if title:
            metadata.append(f"Title: {title.get_text().strip()}")
            
        # Meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name', '') or meta.get('property', '')
            content = meta.get('content', '')
            if name and content:
                metadata.append(f"{name}: {content}")
                
        # Update metadata tab
        self.tabs['metadata'].delete(1.0, tk.END)
        self.tabs['metadata'].insert(tk.END, "\n".join(metadata))

if __name__ == "__main__":
    root = tk.Tk()
    app = WebScraperGUI(root)
    root.mainloop() 