from fastapi import FastAPI
from services.football_api import get_live_matches
from football import get_player_codes

app = FastAPI()

get

@app.get("/")
def read_root():
    return {"message": "Football Data API is running!"}
    
@app.get("/hello/{name}")   
def read_item(name: str):
    return {"message": f"Hello {name}"}

@app.get("/player-codes")
def player_codes():
    return get_player_codes()
