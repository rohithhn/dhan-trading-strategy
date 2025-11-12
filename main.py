import os
import time
from dhanhq import dhanhq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Dhan API credentials from environment
CLIENT_ID = os.getenv('DHAN_CLIENT_ID')
ACCESS_TOKEN = os.getenv('DHAN_ACCESS_TOKEN')

def main():
    print("Starting Dhan Trading Strategy...")
    
    # Initialize Dhan client
    dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)
    
    print("Trading strategy initialized successfully!")
    print("Add your trading logic here.")
    
    # Keep the script running
    while True:
        try:
            print("Strategy is running... (Add your logic)")
            time.sleep(300)  # Sleep for 5 minutes
        except KeyboardInterrupt:
            print("Strategy stopped by user")
            break
        except Exception as e:
            print(f"Error occurred: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
