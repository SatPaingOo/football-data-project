

from functools import cache
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
from log import log  # Import the log function

db_link="./data/football.db"

def load_player_codes():

    # Create/connect to SQLite database
    conn = sqlite3.connect(db_link)
    cursor = conn.cursor()

    # Drop the existing table first to ensure clean schema
    # cursor.execute('DROP TABLE IF EXISTS players')
    # cursor.execute('DROP TABLE IF EXISTS player_codes')

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
        # Setup Chrome options with additional stability settings
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--headless')  # Run in headless mode
        
        # Use ChromeDriver without specifying version
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        # Set page load timeout
        driver.set_page_load_timeout(30)
        
        # Navigate to the page with retry mechanism
        max_retries = 3
        for attempt in range(max_retries):
            try:
                driver.get(target_link)
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(2)

        # Wait for the page to load completely
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        print(f"Page title: {driver.title}")
        
        # Use a more direct approach - find all links on the page
        all_links = driver.find_elements(By.TAG_NAME, "a")
        
        # Filter links that match the pattern for player letter codes
        for link in all_links:
            href = link.get_attribute('href')
            text = link.text.strip()
            
            # Check if this is a valid player letter code link
            if (href and text and '/en/players/' in href and 
                len(text) == 2 and  # Exactly 2 characters
                text[0].isalpha() and text[1].isalpha() and  # Both characters are letters
                text[0].isupper() and text[1].islower() and  # First uppercase, second lowercase
                href.endswith('/')):  # Ensure URL ends with /
                
                # Extract letter code from URL as backup
                url_letter = href.split('/players/')[1].strip('/')
                letter_code = text
                
                # Check if letter code already exists
                cursor.execute("""
                    SELECT id FROM player_codes 
                    WHERE letter = ?
                """, (letter_code,))
                
                existing_code = cursor.fetchone()
                
                if not existing_code:
                    print(f"Found new letter code: {letter_code}, URL: {href}")
                    player_code = {
                        'letter': letter_code,
                        'url': href
                    }
                    players_codes.append(player_code)
                else:
                    print(f"Letter code {letter_code} already exists, skipping")
        
        print(f"Total new player codes found: {len(players_codes)}")

        if players_codes:
            # Convert players_codes list to DataFrame
            player_codes_df = pd.DataFrame(players_codes)
            print(f"player_codes_df: {player_codes_df.head()}")

            # Save DataFrame to SQLite database without specifying dtypes
            player_codes_df.to_sql('player_codes', conn, 
                                    if_exists='append', 
                                    index=False)
            print("New player_codes_df saved successfully")

        # Get the saved data
        result = pd.read_sql_query("""
            SELECT id, letter, url, created_at 
            FROM player_codes 
            ORDER BY id DESC 
            LIMIT 5
        """, conn)
        
        print("load_player_codes executed successfully")
        print(f"result: {result}")
        return True

    except Exception as e:
        print(f"load_player_codes error occurred: {e}")
        return False

    finally:
        if 'driver' in locals():
            driver.quit()
        conn.close()


def load_player_codes_status_reset():
    """
    Load player codes from fbref.com and save to player_codes table
    """
    # Create/connect to SQLite database
    conn = sqlite3.connect(db_link)
    cursor = conn.cursor()

    try:
        # DROP TABLE IF EXISTS players
        cursor.execute('DROP TABLE IF EXISTS players')


        # After processing all players for this letter
        cursor.execute("""
            UPDATE player_codes 
            SET status = 0 
        """)
        conn.commit()
        print(f"Updated status RESET for all letters")
        print("load_player_codes_status_reset executed successfully")


    except Exception as e:
        print(f"Error updating status RESET for letter")
        conn.rollback()

def load_player():
    """
    Load player information from player_codes table URLs and save to players table
    """
    
    # Create/connect to SQLite database
    conn = sqlite3.connect(db_link)
    cursor = conn.cursor()

    # Create players table if it doesn't exist (without dropping it)
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
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')

        # Setup Chrome driver with webdriver-manager
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        # Get unprocessed player codes from the database
        player_codes = pd.read_sql_query("""
            SELECT * FROM player_codes 
            WHERE status = 0 
            ORDER BY id 
            LIMIT 100
        """, conn)
        
        log(f"Processing {len(player_codes)} player codes")
        
        if len(player_codes) == 0:
            log("No unprocessed player codes found")
            return True
            
        players_data = []
        
        # Process each URL from player_codes
        for _, row in player_codes.iterrows():
            max_retries = 3
            retry_count = 0
            success = False
            
            while retry_count < max_retries and not success:
                try:
                    log(f"Processing letter code: {row['letter']} (ID: {row['id']}) - Attempt {retry_count + 1}")
                    driver.get(row['url'])
                    
                    # Add explicit wait with longer timeout
                    wait = WebDriverWait(driver, 30)
                    wait.until(
                        EC.presence_of_element_located((By.CLASS_NAME, "section_content"))
                    )
                    
                    # Add small delay after page load
                    time.sleep(2)
                    
                    # Find all player rows
                    player_rows = driver.find_elements(By.CSS_SELECTOR, ".section_content p")
                    
                    players_count = 0
                    for player_row in player_rows:
                        try:
                            player_text = player_row.text.strip()
                            if player_text:
                                parts = player_text.split('·')
                                
                                if len(parts) >= 3:
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
                                    players_count += 1
                        except Exception as e:
                            log(f"Error processing player row: {str(e)[:100]}")  # Limit error message length
                            continue
                    
                    log(f"Found {players_count} players for letter code {row['letter']}")
                    
                    # Update database in a single transaction
                    if players_count > 0:
                        cursor.execute("""
                            UPDATE player_codes 
                            SET status = 1 
                            WHERE id = ?
                        """, (row['id'],))
                        conn.commit()
                        log(f"Updated status for letter {row['letter']} (ID: {row['id']})")
                    
                    success = True
                    
                except sqlite3.OperationalError as e:
                    if "database is locked" in str(e):
                        retry_count += 1
                        log(f"Database locked, retrying in 5 seconds... (Attempt {retry_count})")
                        time.sleep(5)
                    else:
                        log(f"Database error: {str(e)[:100]}")
                        raise e
                except Exception as e:
                    retry_count += 1
                    log(f"Error processing letter {row['letter']}: {str(e)[:100]}")
                    if retry_count == max_retries:
                        log(f"Failed to process letter {row['letter']} after {max_retries} attempts")
                    time.sleep(5)
        
        if players_data:
            # Convert to DataFrame and save to database
            players_df = pd.DataFrame(players_data)
            players_df.to_sql('players', conn, if_exists='append', index=False)
            log(f"Successfully saved {len(players_data)} players to database")
        
        log("load_player executed successfully")
        return True

    except Exception as e:
        log(f"Error in load_player: {str(e)[:100]}")
        return False

    finally:
        if 'driver' in locals():
            driver.quit()
        conn.close()


def get_players(page=1, page_size=10, sort_column='id', sort_order='asc'):
    """
    Get player information from the players table in the database with pagination and sorting
    
    Args:
        page (int): Page number (starting from 1)
        page_size (int): Number of records per page
        sort_column (str): Column to sort by
        sort_order (str): Sort direction ('asc' or 'desc')
        
    Returns:
        tuple: (DataFrame of players, total_records)
    """
    # Create/connect to SQLite database
    conn = sqlite3.connect(db_link)
    cursor = conn.cursor()

    try:
        # Validate and sanitize inputs to prevent SQL injection
        valid_columns = ['id', 'name', 'years', 'position', 'additional_info', 
                        'player_code_id', 'url', 'letter']
        
        if sort_column not in valid_columns:
            sort_column = 'id'  # Default to id if invalid column
            
        sort_direction = 'DESC' if sort_order.lower() == 'desc' else 'ASC'
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get total count first
        cursor.execute("SELECT COUNT(*) FROM players")
        total_records = cursor.fetchone()[0]
        
        # Query to get paginated players from the database
        query = f"""
        SELECT p.id, p.name, p.years, p.position, p.additional_info, 
            p.player_code_id, p.url, pc.letter
        FROM players p
        JOIN player_codes pc ON p.player_code_id = pc.id
        ORDER BY p.{sort_column} {sort_direction}
        LIMIT ? OFFSET ?
        """
        
        # Execute the query with parameters
        cursor.execute(query, (page_size, offset))
        players = cursor.fetchall()
        
        # Column names for the result
        columns = ['id', 'name', 'years', 'position', 'additional_info', 
                    'player_code_id', 'url', 'letter']
        
        # Convert the results to a list of dictionaries
        players_data = []
        for player in players:
            player_dict = {columns[i]: player[i] for i in range(len(columns))}
            players_data.append(player_dict)
        
        # Convert to DataFrame
        players_df = pd.DataFrame(players_data)
        
        print(f"Retrieved {len(players_data)} players from database (page {page})")
        return players_df, total_records
        
    except Exception as e:
        print(f"Error in get_players: {e}")
        return pd.DataFrame(), 0

    finally:
        conn.close()