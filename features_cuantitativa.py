
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
import streamlit as st
import plotly.graph_objects as go
from collections import Counter
import plotly.express as px


def plot_top_words(df, column, top_n):
    """
    Plots the top N most frequent words in a specified column of a DataFrame.
    
    Parameters:
        df (pd.DataFrame): DataFrame containing the text data.
        column (str): Column name containing the cleaned text.
        top_n (int): Number of top words to display.
    """
    # Flatten all words in the column into a single list
    all_words = " ".join(df[column].tolist()).split()
    
    # Count word frequencies
    word_counts = Counter(all_words)
    most_common = word_counts.most_common(top_n)
    
    # Separate words and counts for plotting
    words, counts = zip(*most_common)
    
    # Create a bar chart using Plotly
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=words,
        y=counts,
        marker=dict(color='lightblue'),
    ))
    
    # Update layout for dark theme
    fig.update_layout(
        title=f"Top {top_n} términos más frecuentes",
        xaxis_title="Términos",
        yaxis_title="Frecuencia",
        template="plotly_dark",
        xaxis=dict(tickangle=45),
        font=dict(size=12),
        height=600,
        width=800,
    )
    
    # Show the figure
    return fig

def plot_word_count_by_period(df, word_to_count, period):
    """
    Generate a bar plot showing the count of a word by period.

    Parameters:
        df (pd.DataFrame): DataFrame containing 'date' and 'Document' columns.
        word_to_count (str): Word to count in the 'Document' column.

    Returns:
        fig: Plotly figure object.
    """

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
    def refactored_period(period):
        if period == 'Mensual':
            return 'M'
        
        elif period == 'Anual':
            return 'Y'
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
                 title=f"Recuento de artículos en que aparece el término '{word_to_count}'",
                 labels={'period': 'Fecha', 'word_present': 'Recuento'},
                 text='word_present',
                 hover_data=['period', 'word_count']
             )
          
             # Customize the layout
             fig.update_traces(textposition='outside')
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
                 title=f"Recuento de artículos en que aparece el término '{word_to_count}'",
                 labels={'date': 'Fecha', 'word_present': 'Recuento'},
                 text='word_present',
                 hover_data=['date', 'word_count']
             )
          
             # Customize the layout
             fig.update_traces(textposition='outside')
             fig.update_layout(
                 xaxis_title="Fecha",
                 yaxis_title="Recuento",
                 xaxis_tickformat="%b %Y",
             )
          
             return fig, sum(df['word_count']), sum(df['word_present'])
