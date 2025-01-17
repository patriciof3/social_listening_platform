import plotly.express as px
import plotly.graph_objects as go
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
    'aire': '#F08080'        # Red
}

def plot_cumulative_articles(df):
    """
    Generates a line plot of cumulative articles over time for each media outlet.
    """
    # Group the data and calculate cumulative sum for each media outlet
    grouped_df = df.groupby(['date', 'media']).size().reset_index(name='article_count')
    grouped_df['cumulative_count'] = grouped_df.groupby('media')['article_count'].cumsum()

    # Create the Plotly line plot with cumulative counts
    fig = px.line(
        grouped_df,
        x='date',
        y='cumulative_count',
        color='media',
        title="Cumulative Articles Over Time",
        labels={'cumulative_count': 'Cumulative Articles', 'date': 'Date'},
        color_discrete_map=color_map,
        hover_data=['date', 'cumulative_count']
    )

    # Get the last data points for each media outlet
    last_points = grouped_df.groupby('media').tail(1)

    # Add text annotations for the last data points
    for _, row in last_points.iterrows():
        fig.add_trace(
            go.Scatter(
                x=[row['date']],
                y=[row['cumulative_count']],
                text=[f"{row['media']}: {row['cumulative_count']}"],
                mode='text',
                showlegend=False,
                textposition='top left',
                textfont=font_style
            )
        )

    # Update hovertemplate to format the date as desired
    fig.update_traces(
        hovertemplate='<b>Fecha: %{x|%d-%m-%Y}</b><br>' 
                      + 'Cantidad: %{y}<extra></extra>'
    )

    # Update layout for better readability
    fig.update_layout(
        xaxis_title='Fecha',
        yaxis_title=None,
        showlegend=False,  
        template='plotly_dark',
        font=font_style,
        title="Cantidad de artículos acumulados por fecha",
        title_font=font_style_title,
        #title_xanchor='center',
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
        pull=[0.05] * len(media_counts),  
        opacity=0.9               
    )

    # Customize layout
    fig_pie.update_layout(
        template="plotly_dark",
        showlegend=False,
        title="Distribución de artículos por medio",
        title_font=font_style_title
    )

    return fig_pie


def plot_avg_articles_per_day(df):
    """
    Generates a bar plot of the average number of articles published per day by media outlet.
    """
    # Ensure the 'date' column is in datetime format
    df['date'] = pd.to_datetime(df['date'])

    # Group by 'media' and 'date' and count the articles per day
    media_daily_count = df.groupby(['media', 'date']).size().reset_index(name='article_count')

    # Calculate the average number of articles published per day for each media outlet
    media_avg_per_day = media_daily_count.groupby('media')['article_count'].mean().reset_index()

    # Create the bar plot
    fig_bar = px.bar(
        media_avg_per_day,
        x='media',
        y='article_count',
        title="Average Articles Published Per Day",
        labels={'article_count': 'Promedio de artículos por día'},
        color='media',
        color_discrete_map=color_map
    )

    # Customize layout
    fig_bar.update_layout(
        template="plotly_dark",
        showlegend=False,
        font=font_style,
        title="Promedio de artículos publicados por día",
        xaxis_title=None,
        yaxis_title=None,
        title_font=font_style_title
    )

    return fig_bar
