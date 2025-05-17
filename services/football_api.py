import os
from dotenv import load_dotenv
import requests

load_dotenv()  # Load environment variables from .env file
API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")

HEADERS = {
    "x-apisports-key": API_KEY
}

def get_live_matches():
    response = requests.get(f"{BASE_URL}fixtures?live=all", headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Failed to fetch live matches"}

def update_players_data(page=1, per_page=100):
    """
    Fetch and update player data in batches of 100 players per request.
    
    Args:
        page (int): The page number to fetch (default: 1)
        per_page (int): Number of players per page (default: 100)
    
    Returns:
        dict: Response containing player data or error message
    """
    response = requests.get(
        f"{BASE_URL}players",
        headers=HEADERS,
        params={
            "page": page,
            "per_page": per_page
        }
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Failed to fetch players data. Status code: {response.status_code}"}

def update_all_players():
    """
    Update all players data by fetching them in batches of 100.
    Handles pagination automatically.
    """
    page = 1
    all_players = []
    
    while True:
        result = update_players_data(page=page)
        
        if "error" in result:
            print(f"Error occurred at page {page}: {result['error']}")
            break
            
        players = result.get("response", [])
        if not players:  # No more players to fetch
            break
            
        all_players.extend(players)
        print(f"Fetched {len(players)} players from page {page}")
        
        # Check if we've reached the last page
        paging = result.get("paging", {})
        if page >= paging.get("total", page):
            break
            
        page += 1
    
    return all_players