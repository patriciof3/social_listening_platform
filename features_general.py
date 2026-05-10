import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

# Set font style and color map variables
font_style = dict(
    family="Arial",  
    size=14,         
    weight='bold', 
)
font_style_title = dict(
    family="Arial",  
    size=20,         
    weight='bold', 
)

color_map = {
    'ellitoral': '#5dade2',  # Blue
    'aire': '#F08080', # Red
    'lacapital' : '#f1e85c' # Green        
}

text_positions = {
    'ellitoral': 'top left',
    'aire': 'top left',
    'lacapital': 'bottom center',
}

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def plot_cumulative_articles_monthly(df):
    """
    Generates a stacked area chart of cumulative articles per month by media outlet.
    """
    # Ensure 'date' column is datetime
    df['date'] = pd.to_datetime(df['date'])

    # Create a 'month' column (first day of the month)
    df['month'] = df['date'].values.astype('datetime64[M]')

    # Group by month and media, count articles
    monthly_counts = df.groupby(['month', 'media']).size().reset_index(name='article_count')

    # Compute cumulative sum for each media
    monthly_counts['cumulative_count'] = monthly_counts.groupby('media')['article_count'].cumsum()

    # Create stacked area chart
    fig = px.area(
        monthly_counts,
        x='month',
        y='cumulative_count',
        color='media',
        title="Cantidad de artículos acumulados",
        labels={'cumulative_count': 'Artículos acumulados'},
        color_discrete_map=color_map
    )

    # Customize layout
    fig.update_layout(
        template='plotly_dark',
        font=font_style,
        showlegend=True,
        xaxis_title='Mes',
        yaxis_title='Artículos acumulados',
        title_font=font_style_title,
        hovermode='x unified'
    )

    return fig





def plot_article_distribution(df):
    """
    Generates a pie chart showing the distribution of articles by media outlet.
    """
    # Group by 'media' and count the number of articles
    media_counts = df['media'].value_counts().reset_index()
    media_counts.columns = ['media', 'article_count']

    # Create the Pie chart
    fig_pie = px.pie(
        media_counts,
        names='media',
        values='article_count',
        title="Article Distribution by Media",
        color='media',
        color_discrete_map=color_map
    )

    # Improve chart appearance
    fig_pie.update_traces(
        textinfo='percent+label', 
        textfont=font_style,
        hoverinfo='label+percent', 
        pull=[0.025] * len(media_counts),  
        #opacity=0.9,
        marker=dict(line=dict(color='white', width=1))  # add white edges
    )

    # Customize layout
    fig_pie.update_layout(
        template="plotly_dark",
        showlegend=False,
        title="Distribución de artículos por medio",
        title_font=font_style_title
    )

    return fig_pie



def plot_articles_last_week(df):
    """
    Generates a bar plot of the total number of articles published by media outlet in the last month.
    """
    # Ensure 'date' is datetime
    df['date'] = pd.to_datetime(df['date'])

    # Filter for articles from the last 30 days
    last_month = df['date'].max() - pd.Timedelta(days=7)
    df_last_month = df[df['date'] >= last_month]

    # Count articles per media
    media_count = df_last_month.groupby('media').size().reset_index(name='article_count')

    # Create the bar plot
    fig_bar = px.bar(
        media_count,
        x='media',
        y='article_count',
        title="Artículos publicados en la última semana",
        labels={'article_count': 'Cantidad de artículos'},
        color='media',
        color_discrete_map=color_map
    )
    fig_bar.update_traces(marker=dict(line=dict(color='white', width=1)))
    # Customize layout
    fig_bar.update_layout(
        template="plotly_dark",
        showlegend=False,
        font=font_style,
        xaxis_title=None,
        yaxis_title=None,
        title_font=font_style_title
    )

    return fig_bar


def plot_top_tfidf_last_week(df, top_n=20):
    """
    Generates a bar chart of top TF-IDF terms from articles in the last 7 days.
    """
    # Ensure 'date' is datetime
    df['date'] = pd.to_datetime(df['date'])



    # Filter for the last 7 days
    last_7_days = df['date'].max() - pd.Timedelta(days=7)
    df_last_week = df[df['date'] >= last_7_days]

    # Combine all article content
    corpus = df_last_week['cleaned_content'].dropna().astype(str).tolist()

    if len(corpus) == 0:
        return go.Figure()  # return empty figure if no data

    # Create TF-IDF vectorizer
    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 1),
        min_df = 2  # include unigrams and bigrams
    )
    tfidf = vectorizer.fit_transform(corpus)

    # Compute mean TF-IDF per term
    terms = vectorizer.get_feature_names_out()
    mean_tfidf = np.asarray(tfidf.mean(axis=0)).ravel()

    # Create DataFrame and sort
    tfidf_df = pd.DataFrame({
        'term': terms,
        'mean_tfidf': mean_tfidf
    }).sort_values('mean_tfidf', ascending=False)

    top_terms = tfidf_df.head(top_n)

    # Create bar chart
    fig = px.bar(
        top_terms[::-1],  # reverse for descending order in plot
        x='mean_tfidf',
        y='term',
        orientation='h',
        labels={'mean_tfidf': 'Relevancia (TF-IDF)', 'term': 'Término'},
    )

    # Apply dark theme and styling
    fig.update_traces(marker=dict(color='#5dade2', line=dict(color='white', width=1)))
    fig.update_layout(
        template='plotly_dark',
        font=font_style,
        title_font=font_style_title,
        xaxis_title=None,
        yaxis_title=None,
        showlegend=False,
        margin=dict(l=0, r=0, t=50, b=0),
    )

    return fig
