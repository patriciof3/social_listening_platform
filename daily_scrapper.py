import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.chrome.options import Options


###############################################################################################################################################
# Dictionary with data sources links

keywords = ['droga', 'narco', 'narcotráfico', 'cocaína', 'marihuana', 'drogas']

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

headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
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
                     href = "https://www.ellitoral.com" + link['href']  # Prepend the URL prefix to the href attribute
     
                     # Find the <h1> inside the <a> tag (if it exists)
                     h1 = link.find('h1')

                     title = h1.get_text(strip=True) if h1 else None  # Extract text or use None if not found
     
                     # Append the link, title, and additional info to the data list
                     data.append({'link': href, 'title': title, 'tag': tag, 'media': 'El Litoral'})
     
             else:
                 print(f"No div with the specified class found on {url}.")

     
         # Create a DataFrame from the data list
    df = pd.DataFrame(data)
    print("Links scraped: ", len(df))
    return df

def scrape_links_and_titles_impresa_litoral(url: str):

    driver = webdriver.Chrome()
    

    # Load the webpage using Selenium
    driver.get(url)

    # Wait for the page to load (you can adjust the time as needed)
    time.sleep(5)

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
        print("No titles with the specified keywords were found.")
    
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
    
    # Convert 'date' to datetime and keep only the date part
    result_df['date'] = pd.to_datetime(result_df['date'], errors='coerce').dt.date
    
    # Ensure both DataFrames align and assign the new columns
    df = df.reset_index(drop=True)  # Reset index to ensure alignment
    df['content'] = result_df['content']
    df['date'] = result_df['date']

    return df



###############################################################################################################################################
###############################################################################################################################################

# AIRE: LINKS AND TITLES

def scrape_links_and_titles_aire(sources_dict):

    # List to store all scraped data
    data = []

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
    
###############################################################################################################################################

 # MERGE LITORAL AND AIRE DATAFRAMES

def merge_dataframes(df_litoral, df_aire):
    merged_df = pd.concat([df_litoral, df_aire], ignore_index=True)
    return merged_df

# REMOVE SHORT ITEMS IN CONTENT AND MERGE INTO SINGLE STRING

def remove_short_items(content_list):
    return ' '.join([item for item in content_list if len(item) > 10])




def main():
    df_links_litoral = scrape_links_and_titles_litoral(sources)
    df_links_impresa_litoral = scrape_links_and_titles_impresa_litoral("https://www.ellitoral.com/edicion-impresa/20240902")
    df_litoral_merged = merge_dataframes(df_links_litoral, df_links_impresa_litoral)
    df_content_date_litoral = scrape_content_date_ellitoral(df_litoral_merged)
    print(df_content_date_litoral.tail())
    print(len(df_content_date_litoral))

    
    #df_content_date_litoral.to_excel("data/df_litoral_test.xlsx", index=False)
    #df_aire = scrape_links_and_titles_aire(sources)

    # Apply the function to the 'Link' column
    # df_extracted = df_aire['link'].apply(scrape_content_date_aire)
    
    # # Create separate columns for 'content' and 'date'
    # df_aire['content'] = df_extracted.apply(lambda x: x['content'])
    # df_aire['date'] = df_extracted.apply(lambda x: x['date'])

    # df_aire['content'] = df_aire['content'].apply(
    #     lambda lst: [s.replace('\xa0', '') for s in lst]
    #     )
    #print(df_aire.content[34])


if __name__ == "__main__":
    main()