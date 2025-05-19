

import requests
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import sqlite3
from datetime import datetime

db_link="football_1.db"

def load_player_codes():

    # Create/connect to SQLite database
    conn = sqlite3.connect(db_link)
    cursor = conn.cursor()

    # Create player_codes table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS player_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        letter TEXT NOT NULL,
        url TEXT NOT NULL,
        status BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    target_link = "https://fbref.com/en/players/"
    players_codes = []

    try:
        # Setup Chrome options
        chrome_options = Options()
        # chrome_options.add_argument('--headless')  # Run in headless mode if needed

        # Setup Chrome driver with webdriver-manager
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(target_link)

        # Wait for the element to be present
        section_content = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "div_4717887657"))
        )

        # Now you can work with the content
        player_links = section_content.find_elements(By.TAG_NAME, "a")

        # Process the links
        for link in player_links:
            player_code = {
                'letter': link.text.strip(),
                'url': link.get_attribute('href')
            }
            players_codes.append(player_code)

        # Convert players_codes list to DataFrame
        player_codes_df = pd.DataFrame(players_codes)

        # Drop the existing table first to ensure clean schema
        cursor.execute('DROP TABLE IF EXISTS players')
        cursor.execute('DROP TABLE IF EXISTS player_codes')

        # Recreate the table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            letter TEXT NOT NULL,
            url TEXT NOT NULL,
            status BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Save DataFrame to SQLite database
        player_codes_df.to_sql('player_codes', conn, 
                          if_exists='append', 
                          index=False,
                          dtype={
                              'letter': 'TEXT',
                              'url': 'TEXT'
                          })
        print("player_codes_df saved successfully")

        # Get the saved data
        result = pd.read_sql_query("""
            SELECT id, letter, url, created_at 
            FROM player_codes 
            ORDER BY id DESC 
            LIMIT 5
        """, conn)
        
        # return {"status": "success", "data": result.to_dict('records')}
        print("load_player_codes executed successfully")
        print(f"result: {result}")

    except Exception as e:
        # return {"status": "error", "message": str(e)}
        print(f"load_player_codes error occurred: {e}")

    finally:
        if 'driver' in locals():
            driver.quit()
        conn.close()


def load_player():
    """
    Load player information from player_codes table URLs and save to players table
    """
    # Create/connect to SQLite database
    conn = sqlite3.connect(db_link)
    cursor = conn.cursor()

    # Drop the existing table first to ensure clean schema
    cursor.execute('DROP TABLE IF EXISTS players')

    # Create players table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        other_name TEXT,
        date_of_birth TEXT,
        place_of_birth TEXT,
        height TEXT,
        weight TEXT,
        nationality TEXT,
        club TEXT,
        league TEXT,
        years TEXT,
        position TEXT,
        additional_info TEXT,
        about TEXT,
        player_code_id INTEGER,
        url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (player_code_id) REFERENCES player_codes(id)
    )
    ''')

    try:
        # Setup Chrome options
        chrome_options = Options()
        # chrome_options.add_argument('--headless')  # Run in headless mode if needed

        # Setup Chrome driver with webdriver-manager
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        # Get all player codes from the database
        player_codes = pd.read_sql_query("SELECT * FROM player_codes", conn)
        
        players_data = []
        
        # Process each URL from player_codes
        for _, row in player_codes.iterrows():
            try:
                ## now testing for 100 players
                # Visit each player's page
                # Check the actual id column from the database
                if int(row['id']) > 100:  # Convert to int for safe comparison
                    print(f"Reached 100 players limit at id: {row['id']}")
                    break
                
                driver.get(row['url'])
                
                # Wait for player content to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "section_content"))
                )
                
                # Find all player rows
                player_rows = driver.find_elements(By.CSS_SELECTOR, ".section_content p")
                
                for player_row in player_rows:
                    try:
                        player_text = player_row.text.strip()
                        if player_text:
                            # Split the text into components
                            parts = player_text.split('·')
                            
                            if len(parts) >= 3:
                                # Get the URL from the player row's anchor tag
                                player_url = player_row.find_element(By.TAG_NAME, 'a').get_attribute('href')
                                
                                player_info = {
                                    'name': parts[0].strip(),
                                    'years': parts[1].strip(),
                                    'position': parts[2].strip(),
                                    'additional_info': ' '.join(parts[3:]).strip() if len(parts) > 3 else '',
                                    'player_code_id': row['id'],
                                    'url': player_url
                                }
                                players_data.append(player_info)
                    except Exception as e:
                        print(f"Error processing player row: {e}")
                        continue
                
                # After processing all players for this letter
                cursor.execute("""
                    UPDATE player_codes 
                    SET status = 1 
                    WHERE id = ?
                """, (row['id'],))
                conn.commit()
                print(f"Updated status for letter {row['letter']} (ID: {row['id']})")
                
            except Exception as e:
                print(f"Error processing URL {row['url']}: {e}")
                continue
        
        if players_data:
            # Convert to DataFrame and save to database
            players_df = pd.DataFrame(players_data)
            players_df.to_sql('players', conn, if_exists='append', index=False)
            print(f"Successfully saved {len(players_data)} players to database")
        
        print("load_player executed successfully")

    except Exception as e:
        print(f"Error in load_player: {e}")

    finally:
        if 'driver' in locals():
            driver.quit()
        conn.close()