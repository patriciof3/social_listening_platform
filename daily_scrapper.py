import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

###############################################################################################################################################
# Dictionary with data sources links

sources = {
    "litoral": {
        "violencia_narco": "https://www.ellitoral.com/tag/violencia-narco",
        "narcotrafico": "https://www.ellitoral.com/tag/narcotrafico",
    },
    "aire": {
        "droga": "https://www.airedesantafe.com.ar/droga-a848/",
        "narcotrafico": "https://www.airedesantafe.com.ar/narcotrafico-a534",
        "cocaina": "https://www.airedesantafe.com.ar/cocaina-a1378",
        "drogas": "https://www.airedesantafe.com.ar/drogas-a4787",
    },
    "rosario12": {
        "general": "https://www.pagina12.com.ar/suplementos/rosario12/{date}",
    },
}

###############################################################################################################################################

#STEPS: 
# 1. Scrape data from each source
# 2. Clean data
# 3. Check duplicates
# 4. Save data to mongodb


# Scrapper El Litoral: LINKS AND TITLES

def scrape_links_and_titles_litoral(sources_dict):

    # List to store all scraped data
    data = []

    # Extract URLs and tags
    urls = list(sources_dict["litoral"].values())
    tags = list(sources_dict["litoral"].keys())

    for url, tag in zip(urls, tags):

         response = requests.get(url)
     
         # Check if the request was successful
         if response.status_code == 200:
             # Parse the webpage content with BeautifulSoup

             soup = BeautifulSoup(response.content, 'html.parser')
     
             div = soup.find('div', class_='styles_detail-left__RyXEu')
     
             if div:
                 # Find all <a> tags within the div
                 links = div.find_all('a', href=True)

                 for link in links:
                     href = "https://www.ellitoral.com/sucesos" + link['href']  # Prepend the URL prefix to the href attribute
     
                     # Find the <h1> inside the <a> tag (if it exists)
                     h1 = link.find('h1')
                     title = h1.get_text(strip=True) if h1 else None  # Extract text or use None if not found
     
                     # Append the link, title, and additional info to the data list
                     data.append({'link': href, 'title': title, 'tag': tag, 'media': 'El Litoral'})
     
             else:
                 print(f"No div with the specified class found on {url}.")

     
         # Create a DataFrame from the data list
    df = pd.DataFrame(data)

    return df

###############################################################################################################################################

# EL LITORAL: CONTENT AND DATE
def scrape_content_date_ellitoral(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content.decode('utf-8', errors='ignore'), 'html.parser')
        
        # Extract paragraphs
        paragraphs = soup.findAll('p')
        content_list = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
        
        # Extract datetime attribute
        datetime_element = soup.find(attrs={"datetime": True})
        date = datetime_element['datetime'] if datetime_element else None

        # Return a tuple of content and date
        return {"content": content_list if content_list else ["No content found"], "date": date}
    except requests.exceptions.RequestException as e:
        return {"content": [f"Request error: {e}"], "date": None}
    except Exception as e:
        return {"content": [f"Error: {e}"], "date": None}

###############################################################################################################################################
###############################################################################################################################################

# AIRE: LINKS AND TITLES

def scrape_links_and_titles_aire(sources_dict):

    # List to store all scraped data
    data = []

    headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }

    # Extract URLs and tags
    urls = list(sources_dict["aire"].values())
    tags = list(sources_dict["aire"].keys())

    for url, tag in zip(urls, tags):

        response = requests.get(url, headers=headers)
     
         # Check if the request was successful
        if response.status_code == 200:
             # Parse the webpage content with BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')

            divs = soup.find_all('div', class_='article-title')
            if divs:
                print(f"Found {len(divs)} divs with the specified class on {url}.")
                for div in divs:
                    a_tag = div.find('a', class_='a-article-link')
                    if a_tag:
                        href = a_tag['href']
                        title = a_tag.get_text(strip=True)
                        data.append({'link': href, 'title': title, 'tag': tag, 'media': 'aire'})
                    else:
                        print(f"No 'a' tag with the specified class found in div on {url}.")
            else:
                print(f"No div with the specified class found on {url}.")

        else:
            print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
    
    return pd.DataFrame(data)

###############################################################################################################################################

# AIRE: CONTENT AND DATE

def scrape_content_date_aire(url):

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content.decode('utf-8', errors='ignore'), 'html.parser')
        
        # Extract paragraphs
        paragraphs = soup.findAll('p')
        content_list = [p.get_text() for p in paragraphs if p.get_text()]
        content_list = content_list[:-5]
        # Extract the <div> with the class 'article-date'
        date_div = soup.find('div', class_='article-date')

        # Extract datetime attribute
        if date_div:
            # Find the <time> tag within that div
            datetime_element = date_div.find('time', attrs={"datetime": True})
            if datetime_element:
                extracted_date = datetime_element['datetime']  # Extract the value of the datetime attribute
            else:
                extracted_date = "Date not found in time tag"
        else:
            extracted_date = "No article-date div found"

        # Return a dictionary with both content and date
        return {"content": content_list if content_list else ["No content found"], "date": extracted_date}
    

def main():
    #df_litoral = scrape_links_and_titles_litoral(sources)

    #df_extracted = df_litoral['link'].apply(scrape_content_date_ellitoral)
    
    # Create separate columns for 'content' and 'date'
    #df_litoral['content'] = df_extracted.apply(lambda x: x['content'])
    #df_litoral['date'] = df_extracted.apply(lambda x: x['date'])
    df_aire = scrape_links_and_titles_aire(sources)

    # Apply the function to the 'Link' column
    df_extracted = df_aire['link'].apply(scrape_content_date_aire)
    
    # Create separate columns for 'content' and 'date'
    df_aire['content'] = df_extracted.apply(lambda x: x['content'])
    df_aire['date'] = df_extracted.apply(lambda x: x['date'])

    print(df_aire.head())
    print(len(df_aire))
    df_aire.to_csv("data/df_aire_historic_content.csv", index=False)
if __name__ == "__main__":
    main()