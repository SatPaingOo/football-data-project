from datetime import datetime
import os
def log(message):
    """
    Log message to console and save to log file
    """
    # Get current date for log file name
    
    date = datetime.now().strftime('%Y-%m-%d')
    log_dir = 'log'
    
    # Create log directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    # Log file path with current date
    log_file = os.path.join(log_dir, f'{date}.log')
    
    # Print to console
    print(message)
    
    # Save to log file
    with open(log_file, 'a') as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f'[{timestamp}] {message}\n')
