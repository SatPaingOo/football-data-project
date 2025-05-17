from football import load_player_codes, load_player

def main():
    """
    Main function to execute the player codes loading process
    """
    try:
        # First load player codes
        load_player_codes()
        print("Player codes loaded successfully!")
        
        # Only proceed to load players if player codes was successful
        try:
            load_player()
            print("Players loaded successfully!")
            return "success"
        except Exception as e:
            print(f"Error loading players: {e}")
            return None
            
    except Exception as e:
        print(f"Error loading player codes: {e}")
        return None

if __name__ == "__main__":
    main()