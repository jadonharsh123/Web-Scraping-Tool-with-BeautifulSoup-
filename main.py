import requests
from bs4 import BeautifulSoup
import csv

# URL of the Wikipedia page to scrape
URL = 'https://en.wikipedia.org/wiki/List_of_countries_and_dependencies_by_population'

# Headers for the HTTP request
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def fetch_html(url):
    """Fetch the HTML content of the given URL."""
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
        return None

def parse_html(html):
    """Parse the HTML content using BeautifulSoup."""
    soup = BeautifulSoup(html, 'html.parser')
    return soup

def extract_data(soup):
    """Extract data from the parsed HTML content."""
    data = []
    # Example: Extracting data from the first table on the page
    table = soup.find('table', {'class': 'wikitable'})
    if table:
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all(['th', 'td'])
            cols = [ele.text.strip() for ele in cols]
            data.append(cols)
    else:
        print("No table found with the specified class.")
    return data

def save_to_csv(data, filename='output.csv'):
    """Save extracted data to a CSV file."""
    if data:
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(data)
        print(f"Data has been saved to {filename}")
    else:
        print("No data to save.")

def main():
    filename = 'output.csv'  # Define the filename variable
    html = fetch_html(URL)
    if html:
        soup = parse_html(html)
        data = extract_data(soup)
        save_to_csv(data, filename)
    else:
        print("Failed to retrieve the webpage.")

if __name__ == '__main__':
    main()
