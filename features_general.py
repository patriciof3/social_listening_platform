import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import pandas as pd

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

def wordcloud_previous_week(df):
    """
    Generates a Word Cloud from articles published in the previous week and returns the figure.
    """
    # Ensure 'date' is datetime
    df['date'] = pd.to_datetime(df['date'])

    # Filter for last week's articles
    today = pd.Timestamp.today()
    start_last_week = today - pd.Timedelta(days=today.weekday() + 7)  # Last week's Monday
    df_last_week = df[df['date'] >= start_last_week]
    # Combine all article content
    text = " ".join(df_last_week['cleaned_content'].dropna().astype(str).tolist())

    # Generate the word cloud
    wc = WordCloud(
        width=1000,
        height=520,
        background_color='black',
        colormap='Set2',
        max_words=200
    ).generate(text)

    # Create figure
    fig, ax = plt.subplots(figsize=(12,6))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')

    # Remove extra padding/margins
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

    return fig
