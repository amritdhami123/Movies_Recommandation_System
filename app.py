import os
import requests
import streamlit as st
from typing import Dict, List, Optional, Tuple
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Movie Recommendation System",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for enhanced styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        font-size: 3rem;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }

    .movie-selector {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem 0;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    }

    .movie-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.5rem;
        margin-top: 2rem;
    }

    .movie-card {
        background: white;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 8px 20px rgba(0,0,0,0.15);
        transition: all 0.3s ease;
        border: 2px solid transparent;
    }

    .movie-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.2);
        border-color: #667eea;
    }

    .movie-poster {
        width: 100%;
        height: 300px;
        object-fit: cover;
    }

    .movie-title {
        padding: 1rem;
        text-align: center;
        font-weight: 600;
        color: #1f2937;
        font-size: 0.9rem;
        line-height: 1.3;
    }

    .stSelectbox > div > div {
        background: white;
        border-radius: 10px;
        border: 2px solid rgba(255,255,255,0.3);
    }

    .stButton > button {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 25px;
        font-weight: 600;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(238, 90, 36, 0.3);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(238, 90, 36, 0.4);
    }

    .recommendation-section {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-top: 2rem;
    }

    .section-title {
        color: white;
        font-size: 1.8rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 1.5rem;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.3);
    }
</style>
""", unsafe_allow_html=True)

# Configuration
try:
    TMDB_API_KEY = st.secrets["TMDB_API_KEY"]
except Exception:
    TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
FALLBACK_POSTER = "https://via.placeholder.com/300x450/667eea/ffffff?text=No+Poster"

if not TMDB_API_KEY:
    st.error(
        "🔑 TMDB API key not found. Please add TMDB_API_KEY to .streamlit/secrets.toml or as an environment variable.")
    st.stop()

# Curated movie database
CURATED_MOVIES = [
    "The Dark Knight", "Inception", "Interstellar", "The Matrix", "Avatar",
    "Avengers: Endgame", "The Shawshank Redemption", "Pulp Fiction", "The Godfather",
    "Forrest Gump", "Fight Club", "The Lord of the Rings: The Fellowship of the Ring",
    "Goodfellas", "The Empire Strikes Back", "One Flew Over the Cuckoo's Nest",
    "Se7en", "Schindler's List", "12 Angry Men", "The Dark Knight Rises",
    "The Lion King", "Gladiator", "Titanic", "Saving Private Ryan",
    "The Departed", "Terminator 2: Judgment Day", "Back to the Future",
    "Spider-Man: Into the Spider-Verse", "Parasite", "Joker", "1917"
]


# API Functions
@st.cache_data(ttl=3600, show_spinner=False)
def tmdb_request(endpoint: str, params: Dict = None) -> Dict:
    """Make authenticated request to TMDB API"""
    url = f"{TMDB_BASE}{endpoint}"
    params = params or {}
    params["api_key"] = TMDB_API_KEY

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return {}


def build_poster_url(poster_path: Optional[str]) -> str:
    """Generate full poster URL or fallback"""
    return f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else FALLBACK_POSTER


@st.cache_data(ttl=3600, show_spinner=False)
def search_movie(title: str) -> Optional[Dict]:
    """Search for movie by title and return best match"""
    data = tmdb_request("/search/movie", {"query": title, "include_adult": "false"})
    results = data.get("results", [])

    if not results:
        return None

    # Return most popular result
    return max(results, key=lambda x: x.get("popularity", 0))


@st.cache_data(ttl=3600, show_spinner=False)
def get_movie_recommendations(movie_id: int, limit: int = 5) -> List[Tuple[str, str]]:
    """Get movie recommendations with posters"""
    data = tmdb_request(f"/movie/{movie_id}/recommendations")
    results = data.get("results", [])

    if not results:
        # Fallback to similar movies
        data = tmdb_request(f"/movie/{movie_id}/similar")
        results = data.get("results", [])

    recommendations = []
    for movie in results[:limit]:
        title = movie.get("title", "Unknown Title")
        poster_url = build_poster_url(movie.get("poster_path"))
        recommendations.append((title, poster_url))

    return recommendations


def generate_recommendations(selected_movie: str) -> List[Tuple[str, str]]:
    """Main recommendation function"""
    movie_data = search_movie(selected_movie)

    if not movie_data:
        return []

    movie_id = movie_data.get("id")
    return get_movie_recommendations(movie_id, 5)


# UI Components
def render_header():
    """Render the main header"""
    st.markdown('<h1 class="main-header">Movie Recommendation System</h1>', unsafe_allow_html=True)


def render_movie_selector():
    """Render movie selection interface"""
    with st.container():
        st.markdown('<div class="movie-selector">', unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            st.markdown("### 🎬 Select a Movie")
            selected_movie = st.selectbox(
                "Choose from our curated collection:",
                options=CURATED_MOVIES,
                index=0,
                label_visibility="collapsed"
            )

            st.markdown("<br>", unsafe_allow_html=True)

            recommend_button = st.button("🎯 Recommend", use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)

        return selected_movie, recommend_button


def render_recommendations(recommendations: List[Tuple[str, str]]):
    """Render movie recommendations in a grid"""
    if not recommendations:
        st.warning("⚠️ No recommendations found. Please try another movie.")
        return

    st.markdown('<div class="recommendation-section">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-title">🎭 Recommended Movies</h2>', unsafe_allow_html=True)

    # Create 5 columns for the recommendations
    cols = st.columns(5)

    for idx, (title, poster_url) in enumerate(recommendations):
        with cols[idx]:
            st.markdown(f'''
            <div class="movie-card">
                <img src="{poster_url}" class="movie-poster" alt="{title}">
                <div class="movie-title">{title}</div>
            </div>
            ''', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# Main Application
def main():
    """Main application logic"""
    render_header()

    # Movie selection section
    selected_movie, recommend_clicked = render_movie_selector()

    # Handle recommendation generation
    if recommend_clicked:
        with st.spinner("🔄 Generating personalized recommendations..."):
            recommendations = generate_recommendations(selected_movie)

            # Store recommendations in session state
            st.session_state.recommendations = recommendations
            st.session_state.selected_movie = selected_movie

    # Display recommendations if available
    if hasattr(st.session_state, 'recommendations') and st.session_state.recommendations:
        render_recommendations(st.session_state.recommendations)

        # Add some spacing and additional info
        st.markdown("---")

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.info(f"✨ Based on your selection: **{st.session_state.selected_movie}**")


if __name__ == "__main__":
    main()
