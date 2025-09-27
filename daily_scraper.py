import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from pymongo import MongoClient
import os
import re
import json
from datetime import datetime
import locale
locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")


###############################################################################################################################################
# Dictionary with data sources links

keywords = ['droga', 'narco', 'cocaína', 'marihuana', 'drogas', 'narcotraficante', 'monos', 'cantero']

sources = {
    "litoral": {
        "violencia_narco": "https://www.ellitoral.com/tag/violencia-narco",
        "narcotrafico": "https://www.ellitoral.com/tag/narcotrafico",
        "policiales": "https://www.ellitoral.com/temas/santa-fe-policiales"
    },
    "aire": {
        "droga": "https://www.airedesantafe.com.ar/droga-a848/",
        "narcotrafico": "https://www.airedesantafe.com.ar/narcotrafico-a534",
        "cocaina": "https://www.airedesantafe.com.ar/cocaina-a1378",
        "drogas": "https://www.airedesantafe.com.ar/drogas-a4787",
        "policiales" : "https://www.airedesantafe.com.ar/policiales",
    },
    "rosario12": {
        "general": "https://www.pagina12.com.ar/suplementos/rosario12/{date}",
    },
    "lacapital": {
        "los_monos": "https://www.lacapital.com.ar/los-monos-a39391.html",
        "narco": "https://www.lacapital.com.ar/narco-a53261.html",
        "narcotráfico": "https://www.lacapital.com.ar/narcotrafico-a26076.html",
        "drogas": "https://www.lacapital.com.ar/drogas-a41562.html",
        "violencia_narco": "https://www.lacapital.com.ar/violencia-narco-a1012674.html",
        "cocaina": "https://www.lacapital.com.ar/cocaina-a51607.html",
        "estupefacientes": "https://www.lacapital.com.ar/estupefacientes-a40894.html",
        "policiales": "https://www.lacapital.com.ar/secciones/policiales.html"
    }
}

headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }


# Get the directory of the current script
script_dir = os.path.dirname(os.path.realpath(__file__))

# Construct the path to stopwords.json in the same directory as the script
stopwords_path = os.path.join(script_dir, 'stopwords.json')

# Read the stopwords file
with open(stopwords_path, 'r', encoding='utf-8') as f:
    stop_words = set(json.load(f))  # Convert to a set for efficient lookup


# MONGO VARIABLES
mongodb_uri = mongodb_uri = os.getenv("MONGODB_URI")
db_name = "social_listening"
collection_name = "drugtrafficking"
unique_field = "link"

###############################################################################################################################################

# Scraper El Litoral: LINKS AND TITLES

def scrape_links_and_titles_litoral(sources_dict, keywords):
    """
    Scrape articles from El Litoral. Only filter titles for 'sucesos' and 'policiales' by keywords.

    Parameters:
    - sources_dict (dict): Dictionary containing URLs and tags.
    - keywords (list): List of keywords to filter specific articles.

    Returns:
    - pd.DataFrame: DataFrame with columns 'link', 'title', 'tag', 'media'.
    """
    data = []

    urls = list(sources_dict["litoral"].values())
    tags = list(sources_dict["litoral"].keys())

    for url, tag in zip(urls, tags):
        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                print(f"Failed to retrieve {url}. Status code: {response.status_code}")
                continue

            soup = BeautifulSoup(response.content, 'html.parser')
            div = soup.find('div', class_='styles_detail-left__RyXEu')

            if not div:
                print(f"No div with the specified class found on {url}.")
                continue

            links = div.find_all('a', href=True)
            for link in links:
                href = "https://www.ellitoral.com" + link['href']
                h1 = link.find('h1')
                title = h1.get_text(strip=True) if h1 else None

                if title:
                    # Only filter 'sucesos' and 'policiales' by keywords
                    if tag in ['sucesos', 'policiales']:
                        if not any(keyword.lower() in title.lower() for keyword in keywords):
                            continue  # Skip if no keyword matches

                    data.append({'link': href, 'title': title, 'tag': tag, 'media': 'ellitoral'})

        except Exception as e:
            print(f"Error processing {url}: {e}")

    return pd.DataFrame(data)

# def scrape_links_and_titles_impresa_litoral(url: str):
    
    chrome_service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
    
    chrome_options = Options()
    options = [
        "--headless",
        "--disable-gpu",
        "--window-size=1920,1200",
        "--ignore-certificate-errors",
        "--disable-extensions",
        "--no-sandbox",
        "--disable-dev-shm-usage"
    ]
    for option in options:
        chrome_options.add_argument(option)
    
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    driver.get(url)
    
    # Wait for the page to load (you can adjust the time as needed)
    time.sleep(20)

    # Dictionary to store the links and titles
    links_and_titles = {}
    

    # Find all the <a> tags with the specific class
    a_tags = driver.find_elements(By.CSS_SELECTOR, 'a.styles_note__oZOP3')

    # Loop through the tags to extract titles and links
    for a_tag in a_tags:
        try:
            title = a_tag.find_element(By.CSS_SELECTOR, 'h3.styles_title__ir_9_').text.strip()
            link = a_tag.get_attribute('href')
            # Store in dictionary
            if any(keyword.lower() in title.lower() for keyword in keywords):
                links_and_titles[title] = link
            
        except Exception as e:
            print(f"Error extracting title and link: {e}")

    # Close the browser session
    driver.quit()

    # Convert dictionary to DataFrame
    if links_and_titles:
        df = pd.DataFrame(list(links_and_titles.items()), columns=['title', 'link'])
    else:
        df = pd.DataFrame(columns=['title', 'link'])
        df["media"] = "El Litoral"
        print("No titles with the specified keywords were found in Edición Impresa.")
    
    return df


###############################################################################################################################################

# EL LITORAL: CONTENT AND DATE
def scrape_content_date_ellitoral(df):
    # List to store the scraped data
    scraped_data = []
    
    for link in df['link']:
        try:
            # Request the webpage
            response = requests.get(link, headers=headers)
            response.raise_for_status()  # Raise an exception for HTTP errors
            
            # Parse the webpage content
            soup = BeautifulSoup(response.content.decode('utf-8', errors='ignore'), 'html.parser')
            
            # Extract paragraphs
            paragraphs = soup.findAll('p')
            content_list = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
            
            # Extract datetime attribute
            datetime_element = soup.find(attrs={"datetime": True})
            date = datetime_element['datetime'] if datetime_element else None
            
            # Remove strings related to other parts of the webpage
            target_string = "Los comentarios realizados son de exclusiva responsabilidad de sus autores"
            content_list = [s for s in content_list if target_string not in s]
            
            # Store the result in the list
            scraped_data.append({"content": content_list if content_list else ["No content found"], "date": date})
        
        except requests.exceptions.RequestException as e:
            scraped_data.append({"content": [f"Request error: {e}"], "date": None})
        except Exception as e:
            scraped_data.append({"content": [f"Error: {e}"], "date": None})
    
    # Create a DataFrame from the scraped data
    result_df = pd.DataFrame(scraped_data)
    
    # Ensure both DataFrames align and assign the new columns
    df = df.reset_index(drop=True)  # Reset index to ensure alignment
    df['content'] = result_df['content']
    df['date'] = result_df['date']
    df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.tz_localize(None)

    print("Articles scraped from El Litoral:", len(df))

    return df



###############################################################################################################################################

# AIRE: LINKS AND TITLES

def scrape_links_and_titles_aire(sources_dict, keywords):
    """
    Scrape articles from Aire de Santa Fe. Only filter titles for 'policiales' by keywords.

    Parameters:
    - sources_dict (dict): Dictionary containing URLs and tags.
    - keywords (list): List of keywords to filter 'policiales' articles.

    Returns:
    - pd.DataFrame: DataFrame with columns 'link', 'title', 'tag', 'media'.
    """
    data = []

    urls = list(sources_dict["aire"].values())
    tags = list(sources_dict["aire"].keys())

    for url, tag in zip(urls, tags):
        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                print(f"Failed to retrieve {url}. Status code: {response.status_code}")
                continue

            soup = BeautifulSoup(response.content, 'html.parser')
            divs = soup.find_all('div', class_='article-title')

            if not divs:
                print(f"No div with the specified class found on {url}.")
                continue

            for div in divs:
                a_tag = div.find('a', class_='a-article-link')
                if a_tag:
                    href = a_tag['href']
                    title = a_tag.get_text(strip=True)

                    # Only filter 'policiales' by keywords
                    if tag == "policiales":
                        if not any(keyword.lower() in title.lower() for keyword in keywords):
                            continue  # Skip this article if no keywords match

                    data.append({'link': href, 'title': title, 'tag': tag, 'media': 'aire'})
                else:
                    print(f"No 'a' tag with the specified class found in div on {url}.")

        except Exception as e:
            print(f"Error processing {url}: {e}")

    return pd.DataFrame(data)

###############################################################################################################################################

# AIRE: CONTENT AND DATE

def scrape_content_date_aire(df):

    scraped_data = []
    headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
    for link in df['link']:
        
        try:
            
            response = requests.get(link, headers=headers, timeout=10)
            response.raise_for_status()
    
            soup = BeautifulSoup(response.content.decode('utf-8', errors='ignore'), 'html.parser')
            
            # Extract paragraphs
            paragraphs = soup.findAll('p')
            content_list = [p.get_text() for p in paragraphs if p.get_text()]
            content_list = content_list[:-5]

            #remove p elements that direct to other articles
            target_strings = ["LEER MÁS", " LEER MÁS"]
            content_list = [s for s in content_list if not any(s.startswith(t) or t in s for t in target_strings)]

            # Extract the <div> with the class 'article-date'
            date_div = soup.find('div', class_='article-date')
    
            # Extract datetime attribute
            if date_div:
                # Find the <time> tag within that div
                datetime_element = date_div.find('time', attrs={"datetime": True})
                if datetime_element:
                    date = datetime_element['datetime']  # Extract the value of the datetime attribute
                else:
                    date = "Date not found in time tag"
            else:
                date = "No article-date div found"
                # Store the result in the list

            scraped_data.append({"content": content_list if content_list else ["No content found"], "date": date})
        
        except requests.exceptions.RequestException as e:
            scraped_data.append({"content": [f"Request error: {e}"], "date": None})
        except Exception as e:
            scraped_data.append({"content": [f"Error: {e}"], "date": None})
    
    # Create a DataFrame from the scraped data
    result_df = pd.DataFrame(scraped_data)
       
    # Ensure both DataFrames align and assign the new columns
    df = df.reset_index(drop=True)  # Reset index to ensure alignment
    df['content'] = result_df['content']
    df['date'] = result_df['date']

    df['content'] = df['content'].apply(
        lambda lst: [s.replace('\xa0', '') for s in lst]
        )
    
    df['content'] = df['content'].apply(
    lambda lst: [s.replace('LEER MÁS ►', '') for s in lst]
    )

    df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.tz_localize(None)
    
    print("Articles scraped from Aire:", len(df))
    return df
    
###############################################################################################################################################
# SCRAPE LINKS LA CAPITAL
def scrape_links_and_titles_lacapital(sources, keywords_for_policiales):
    """
    Scrapes the given URLs from La Capital. For 'policiales', filters titles containing specific keywords.

    Parameters:
    - sources (dict): Dictionary containing source URLs and their corresponding tags.
    - keywords_for_policiales (list): List of keywords to filter news titles for the 'policiales' tag.

    Returns:
    - pd.DataFrame: DataFrame containing scraped data with columns: 'link', 'title', 'tag', 'media'.
    """
    # List to store all scraped data
    data = []
    visited_links = set()  # To track (Link, Tag) combinations and check for duplicates

    # Extract URLs and tags
    urls = list(sources["lacapital"].values())
    tags = list(sources["lacapital"].keys())

    # Iterate through each URL and tag
    for url, tag in zip(urls, tags):
        try:
            # Send a GET request to the base URL
            response = requests.get(url, headers=headers)

            # Check if the response is valid
            if response.status_code != 200:
                print(f"Failed to fetch {url}: Status code {response.status_code}")
                continue

            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            section = soup.find('section', class_="last-entrys")

            # If no entries found, skip this URL
            if not section:
                print("No entries found. Skipping this URL.")
                continue

            # Extract links and titles
            a_tags = section.find_all('a', class_="cover-link")
            for a in a_tags:
                href = a['href']
                title = a.get('title', '').strip()

                # For 'policiales', filter by keywords
                if tag == 'policiales':
                    if not any(keyword.lower() in title.lower() for keyword in keywords_for_policiales):
                        continue  # Skip titles without the keywords

                # Check for duplicate (Link, Tag)
                if (href, tag) in visited_links:
                    print("Duplicate Link and Tag found. Skipping this link.")
                    continue

                visited_links.add((href, tag))
                data.append({'link': href, 'title': title, 'tag': tag, 'media': 'lacapital'})

        except Exception as e:
            print(f"Error processing {url}: {e}")

    # Create a DataFrame from the data list
    print("Links scraped from La Capital:", len(data))
    return pd.DataFrame(data)


###############################################################################################################################################
# SCRAPE CONTENT AND DATE LA CAPITAL
def scrape_content_date_lacapital(df):
    """
    Scrapes content and date for each link in the DataFrame.
    Drops rows where 'date' is missing or 'content' has an error.
    
    Parameters:
    - df (pd.DataFrame): DataFrame containing a 'link' column.

    Returns:
    - pd.DataFrame: DataFrame with added 'content' and 'date' columns, cleaned of invalid rows.
    """
    # List to store the scraped data
    scraped_data = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for i, link in enumerate(df['link']):
        try:
            # Request the webpage
            response = requests.get(link, headers=headers)
            response.raise_for_status()  # Raise an exception for HTTP errors

            # Parse the webpage content
            soup = BeautifulSoup(response.content.decode('utf-8', errors='ignore'), 'html.parser')

            # Extract divs with the class "article-body"
            article_body_divs = soup.find_all('div', class_='article-body')

            # Extract paragraphs within those divs
            content_list = [
                p.get_text(separator=" ", strip=True)
                for div in article_body_divs
                for p in div.find_all('p')
                if p.get_text(separator=" ", strip=True) and not p.get_text(strip=True).startswith('>>')
            ]

            # Extract datetime attribute
            date_element = soup.find('span', class_='nota-fecha')
            date = date_element.text.strip() if date_element else None

            # Handle cases where no content was found
            if not content_list:
                print(f"No content found for {link}")
                content_list = ["No content found"]

            # Store the result in the list
            scraped_data.append({"content": content_list, "date": date})

        except requests.exceptions.RequestException as e:
            print(f"Request error for link {link}: {e}")
            scraped_data.append({"content": [f"Request error: {e}"], "date": None})
        except Exception as e:
            print(f"Error for link {link}: {e}")
            scraped_data.append({"content": [f"Error: {e}"], "date": None})

    # Create a DataFrame from the scraped data
    result_df = pd.DataFrame(scraped_data)

    # Ensure both DataFrames align and assign the new columns
    df = df.reset_index(drop=True)  # Reset index to ensure alignment
    df['content'] = result_df['content']
    df['date'] = result_df['date']

    # Drop rows where 'date' is None or 'content' contains "No content found" or an error
    df = df.dropna(subset=['date'])
    df = df[~df['content'].apply(lambda x: any("No content found" in item or "Error" in item for item in x))]

    # Convert date to datetime format
    try:
        df["date"] = df["date"].apply(lambda x: datetime.strptime(x, "%d de %B %Y"))
    except Exception as e:
        print(f"Error parsing date: {e}")

    print("Articles scraped from La Capital:", len(df))

    return df

###############################################################################################################################################

 # MERGE LITORAL AND AIRE DATAFRAMES

def merge_dataframes(df1, df2, df3):
    """
    Merge two DataFrames, df1 and df2, into one and return the merged DataFrame.
    
    Parameters
    ----------
    df1 : pd.DataFrame
        The DataFrame containing the scraped data from El Litoral.
    df2 : pd.DataFrame
        The DataFrame containing the scraped data from Aire de Santa Fe.
    
    Returns
    -------
    pd.DataFrame
        The merged DataFrame containing the data from both sources.
    """
    
    merged_df = pd.concat([df1, df2, df3], ignore_index=True)

    merged_df = merged_df.drop_duplicates(subset=['link'], keep='first')

    return merged_df

# REMOVE SHORT ITEMS IN CONTENT AND MERGE INTO SINGLE STRING


def remove_short_items_from_column(df, column_name):
    """
    Remove items from a specified column of a DataFrame that have less than 30 characters.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the column to filter.
    column_name : str
        Name of the column to filter.

    Returns
    -------
    pd.DataFrame
        DataFrame with the specified column updated, where short items have been removed, 
        and the remaining items joined with spaces.
    """

    # Apply filtering to the specified column
    df[column_name] = df[column_name].apply(
        lambda content_list: ' '.join([item for item in content_list if len(item) > 30])
        if isinstance(content_list, list) else content_list
    )

    return df

def remove_stopwords_from_column(df, column, stop_words):
    """
    Removes stopwords from the specified column of a DataFrame.
    
    Parameters:
        df (pd.DataFrame): The input DataFrame.
        column (str): The name of the column containing text.
        stop_words (set): A set of stopwords to remove.
        
    Returns:
        pd.DataFrame: A new DataFrame with the cleaned column.
    """
    def clean_text(text):
        text = str(text).lower()  # Convert to lowercase
        text = re.sub(r'[^a-záéíóúñü0-9\s]', '', text)  # Remove punctuation
        words = text.split()  # Split text into words
        return " ".join(word for word in words if word not in stop_words)

    # Apply the cleaning function to the specified column
    df["cleaned_content"] = df[column].apply(clean_text)
    return df
###############################################################################################################################################
# UPLOAD DATA TO MONGODB

def upload_dataframe_to_mongodb(df, mongodb_uri, db_name, collection_name, unique_field):
    """
    Uploads data from a DataFrame to a MongoDB collection, ensuring no duplicates 
    based on the specified unique field.

    Parameters:
    - df (pd.DataFrame): The DataFrame containing data to upload.
    - mongodb_uri (str): The MongoDB connection URI.
    - db_name (str): The name of the database.
    - collection_name (str): The name of the collection.
    - unique_field (str): The field to check for duplicates (e.g., 'link').

    Returns:
    - dict: A summary of the operation with counts of inserted and skipped documents.
    """
    # Connect to MongoDB
    client = MongoClient(mongodb_uri)
    db = client[db_name]
    collection = db[collection_name]

    # Fetch existing unique field values
    existing_values = set(doc[unique_field] for doc in collection.find({}, {unique_field: 1, "_id": 0}))

    # Filter the DataFrame to exclude duplicates
    df_to_insert = df[~df[unique_field].isin(existing_values)]

    # Insert new documents
    if not df_to_insert.empty:
        collection.insert_many(df_to_insert.to_dict(orient="records"))

    # Return a summary of the operation
    return {
        "inserted_count": len(df_to_insert),
        "skipped_count": len(df) - len(df_to_insert)
    }

###############################################################################################################################################
# MAIN FUNCTION

def main():
    
    df_links_litoral = scrape_links_and_titles_litoral(sources, keywords)
    
    # df_links_impresa_litoral = scrape_links_and_titles_impresa_litoral("https://www.ellitoral.com/edicion-impresa")
    
    # df_litoral_merged = merge_dataframes(df_links_litoral, df_links_impresa_litoral)
    
    df_content_date_litoral = scrape_content_date_ellitoral(df_links_litoral)

    df_links_aire = scrape_links_and_titles_aire(sources, keywords)

    df_content_date_aire = scrape_content_date_aire(df_links_aire)

    df_links_lacapital = scrape_links_and_titles_lacapital(sources, keywords)

    df_content_date_lacapital = scrape_content_date_lacapital(df_links_lacapital)
   
    df_merged = merge_dataframes(df_content_date_litoral, df_content_date_aire, df_content_date_lacapital)
   
    df_merged = remove_short_items_from_column(df_merged, 'content')

    df_cleaned = remove_stopwords_from_column(df_merged, 'content', stop_words)
    
    result = upload_dataframe_to_mongodb(df_cleaned, mongodb_uri, db_name, collection_name, unique_field)
    
    print(result)


if __name__ == "__main__":
    main()