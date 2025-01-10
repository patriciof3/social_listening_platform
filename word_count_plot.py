import plotly.express as px
import pandas as pd
import spacy
import re
# Load Spanish language model in SpaCy
nlp = spacy.load("es_core_news_sm")
# Define Spanish stopwords
STOP_WORDS = spacy.lang.es.stop_words.STOP_WORDS


def reading_data():
    # Convert 'date' to datetime
    df = pd.read_json("scraped_content.json", lines=True)

    df['date'] = pd.to_datetime(df['date'])

    df['content'] = df['content'].astype(str)
    df['content'] = df['content'].str.replace('\n', ' ')
    df['content'] = df['content'].str.replace(r"[\[\]\'/\\]", "", regex=True)

    return df

def remove_stopwords(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Záéíóúñü0-9\s]', '', text)
    doc = nlp(text)  # Process the text with SpaCy
    # Filter out stopwords and return the cleaned text
    return " ".join([token.text for token in doc if token.text.lower() not in STOP_WORDS])

def refactored_period(period):
    if period == 'Mensual':
        return 'M'
    
    elif period == 'Anual':
        return 'Y'


def plot_word_count_by_period(word_to_count, period):
    """
    Generate a bar plot showing the count of a word by period.

    Parameters:
        df (pd.DataFrame): DataFrame containing 'date' and 'Document' columns.
        word_to_count (str): Word to count in the 'Document' column.

    Returns:
        fig: Plotly figure object.
    """

    df = reading_data()

    df['cleaned_content'] = df['content'].apply(remove_stopwords)

    # Ensure 'date' is in datetime format
    df['date'] = pd.to_datetime(df['date'])

    # Count occurrences of the word in 'Document'
    def count_word(text, word):
        return text.lower().split().count(word.lower())

    df['word_count'] = df['cleaned_content'].apply(lambda text: count_word(text, word_to_count))

    def count_word(text, word):
    # Convert text to lowercase and split into words
        words = text.lower().split()
    # Count occurrences of the word
        word_count = words.count(word.lower())
    # Check if the word is present (1 if present, 0 if not)
        word_present = 1 if word.lower() in words else 0
        return word_count, word_present

# Apply the function to the 'cleaned_content' column
    df[['word_count', 'word_present']] = df['cleaned_content'].apply(
        lambda text: pd.Series(count_word(text, word_to_count))
    )

    # Group by period and sum the counts
    
    if period == 'Mensual' or period == 'Anual': 
             period_refactored = refactored_period(period)
             df['period'] = df['date'].dt.to_period(period_refactored)
             word_counts_by_period = df.groupby('period')[['word_present', 'word_count']].sum().reset_index()
             word_counts_by_period['period'] = word_counts_by_period['period'].dt.to_timestamp()

             # Create a bar chart using Plotly
             fig = px.bar(
                 word_counts_by_period,
                 x='period',
                 y='word_present',
                 title=f"Recuento de la palabra '{word_to_count}'",
                 labels={'period': 'Fecha', 'word_present': 'Recuento'},
                 text='word_present',
                 hover_data=['period', 'word_count']
             )
          
             # Customize the layout
             fig.update_traces(textposition='outside', marker_color='blue')
             fig.update_layout(
                 xaxis_title="Fecha",
                 yaxis_title="Recuento",
                 xaxis_tickformat="%Y",
             )

             return fig, sum(df['word_count']), sum(df['word_present'])
    
    elif period == 'Diario':
                     # Create a bar chart using Plotly
             fig = px.bar(
                 df,
                 x='date',
                 y='word_present',
                 title=f"Recuento de la palabra '{word_to_count}'",
                 labels={'date': 'Fecha', 'word_present': 'Recuento'},
                 text='word_present',
                 hover_data=['date', 'word_count']
             )
          
             # Customize the layout
             fig.update_traces(textposition='outside', marker_color='blue')
             fig.update_layout(
                 xaxis_title="Fecha",
                 yaxis_title="Recuento",
                 xaxis_tickformat="%b %Y",
             )
          
             return fig, sum(df['word_count']), sum(df['word_present'])