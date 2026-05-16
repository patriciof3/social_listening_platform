import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import pandas as pd
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
from mongodb_features import reading_data
import streamlit as st

def get_data():
    if "df" not in st.session_state:
        df = reading_data("social_listening", "drugtrafficking")
        strings_to_remove = ["santa_fe", "rosario", "argentina", "años", "narcotráfico", "drogas"]
        for s in strings_to_remove:
            df["cleaned_content"] = df["cleaned_content"].str.replace(s, "", regex=False)
        df["cleaned_content"] = df["cleaned_content"].str.replace(r"\s+", " ", regex=True).str.strip()
        st.session_state["df"] = df
    return st.session_state["df"]



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


def get_weekly_avg_per_media(df):
    """
    Returns a dict with average articles per week (last 52 weeks) per media.
    Also returns week-over-week change.
    """
    df['date'] = pd.to_datetime(df['date'])
    one_year_ago = df['date'].max() - pd.Timedelta(weeks=52)
    df_year = df[df['date'] >= one_year_ago].copy()
    df_year['week'] = df_year['date'].dt.to_period('W')

    weekly = df_year.groupby(['week', 'media']).size().reset_index(name='count')
    avg = weekly.groupby('media')['count'].mean().round(1)

    # Week over week change
    last_week = df['date'].max() - pd.Timedelta(days=7)
    prev_week = last_week - pd.Timedelta(days=7)

    current = df[df['date'] >= last_week].groupby('media').size()
    previous = df[(df['date'] >= prev_week) & (df['date'] < last_week)].groupby('media').size()
    change = (current - previous).fillna(0)

    return avg, change


def plot_weekly_trend(df):
    """
    Line chart of weekly article count per media for the last 12 weeks.
    """
    df['date'] = pd.to_datetime(df['date'])
    twelve_weeks_ago = df['date'].max() - pd.Timedelta(weeks=24)
    df_recent = df[df['date'] >= twelve_weeks_ago].copy()
    df_recent['week'] = df_recent['date'].dt.to_period('W').dt.start_time

    weekly = df_recent.groupby(['week', 'media']).size().reset_index(name='article_count')

    fig = px.line(
        weekly,
        x='week',
        y='article_count',
        color='media',
        title="Tendencia semanal de artículos (últimos 6 meses)",
        markers=True,
        color_discrete_map=color_map
    )
    fig.update_layout(
        template='plotly_dark',
        font=font_style,
        title_font=font_style_title,
        xaxis_title='Semana',
        yaxis_title='Artículos',
        hovermode='x unified',
        legend_title_text=None
    )
    fig.update_traces(line=dict(width=2.5), marker=dict(size=7))

    return fig