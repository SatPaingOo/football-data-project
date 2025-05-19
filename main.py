from football import load_player_codes, load_player_codes_status_reset, load_player, get_players
from flask import Flask, jsonify
from api.controllers.player import get_players_list

app = Flask(__name__)


# @app.route('/api/')
# def api_init():
#     """API endpoint start"""
#     try:
#         return jsonify({"status": "success", "message": "API successfully"})
#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 500

# @app.route('/api/players/get-list', methods=['GET'])
# def api_players_get_list():
#     return get_players_list()

def main():
    """
    Main function to execute the player codes loading process
    """
    try:
        # # First load player codes
        load_player_codes()
        print("Player codes loaded successfully!")
        # # Then load player codes status reset
        # load_player_codes_status_reset()
        print("Player codes status reset loaded successfully!")
        
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
    # Run the Flask app when script is executed directly
    # app.run(debug=True, host='0.0.0.0', port=5000)
    main()  # Commented out as we're now using the API endpoints