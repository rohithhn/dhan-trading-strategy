import os
import time
import logging
from datetime import datetime
from dhanhq import dhanhq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get Dhan API credentials from environment
CLIENT_ID = os.getenv('DHAN_CLIENT_ID', '1100717930')
ACCESS_TOKEN = os.getenv('DHAN_ACCESS_TOKEN')

class DhanTradingStrategy:
    def __init__(self):
        self.dhan = None
        self.is_running = False
        
    def initialize(self):
        """Initialize Dhan API client"""
        try:
            self.dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)
            logger.info("Dhan API client initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Dhan API: {e}")
            return False
    
    def get_nifty_ltp(self):
        """Get NIFTY 50 Last Traded Price"""
        try:
            # NIFTY 50 security ID in Dhan
            security_id = "13"  
            quote = self.dhan.get_quote(
                security_id=security_id,
                exchange_segment="NSE"
            )
            if quote and 'data' in quote:
                ltp = quote['data'].get('LTP', 0)
                logger.info(f"NIFTY 50 LTP: {ltp}")
                return ltp
            return None
        except Exception as e:
            logger.error(f"Error fetching NIFTY LTP: {e}")
            return None
    
    def check_market_hours(self):
        """Check if current time is within market hours"""
        now = datetime.now()
        current_time = now.time()
        
        # Market hours: 9:15 AM to 3:30 PM IST
        market_open = now.replace(hour=9, minute=15, second=0).time()
        market_close = now.replace(hour=15, minute=30, second=0).time()
        
        is_market_open = market_open <= current_time <= market_close
        
        # Check if it's a weekday (Monday=0, Sunday=6)
        is_weekday = now.weekday() < 5
        
        return is_market_open and is_weekday
    
    def analyze_market(self):
        """Analyze market conditions"""
        logger.info("Analyzing market conditions...")
        
        # Get NIFTY price
        nifty_price = self.get_nifty_ltp()
        
        if nifty_price:
            logger.info(f"Current NIFTY 50: {nifty_price}")
            
            # Add your analysis logic here
            # For now, just logging the data
            return {
                'nifty_price': nifty_price,
                'timestamp': datetime.now(),
                'signal': 'NEUTRAL'
            }
        
        return None
    
    def run(self):
        """Main execution loop"""
        logger.info("Starting Dhan Trading Strategy...")
        
        if not self.initialize():
            logger.error("Failed to initialize. Exiting.")
            return
        
        self.is_running = True
        logger.info("Strategy is now running. Press Ctrl+C to stop.")
        
        iteration = 0
        
        while self.is_running:
            try:
                iteration += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"Iteration: {iteration} | Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'='*60}")
                
                # Check if market is open
                if self.check_market_hours():
                    logger.info("Market is OPEN - Running analysis")
                    
                    # Analyze market
                    analysis = self.analyze_market()
                    
                    if analysis:
                        logger.info(f"Analysis complete: Signal = {analysis['signal']}")
                    else:
                        logger.warning("Analysis returned no data")
                else:
                    logger.info("Market is CLOSED - Waiting for market hours")
                    logger.info("Market hours: Monday-Friday, 9:15 AM - 3:30 PM IST")
                
                # Sleep for 5 minutes before next iteration
                logger.info("Sleeping for 5 minutes...")
                time.sleep(300)
                
            except KeyboardInterrupt:
                logger.info("\nReceived stop signal from user")
                self.is_running = False
                break
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                logger.info("Waiting 60 seconds before retry...")
                time.sleep(60)
        
        logger.info("Trading strategy stopped")

def main():
    """Entry point"""
    logger.info("="*60)
    logger.info("DHAN NIFTY 50 TRADING STRATEGY")
    logger.info("="*60)
    logger.info(f"Client ID: {CLIENT_ID}")
    logger.info(f"Token configured: {'Yes' if ACCESS_TOKEN else 'No'}")
    logger.info("="*60)
    
    strategy = DhanTradingStrategy()
    strategy.run()

if __name__ == "__main__":
    main()
