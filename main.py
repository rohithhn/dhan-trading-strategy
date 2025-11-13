import os
import time
import logging
import json
from datetime import datetime
from dhanhq import dhanhq
from dotenv import load_dotenv
import requests
from telegram import Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import threading

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get credentials from environment
CLIENT_ID = os.getenv('DHAN_CLIENT_ID')
ACCESS_TOKEN = os.getenv('DHAN_ACCESS_TOKEN')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
# Trading logs for GPT context
trade_logs = []
strategy_context = "NIFTY 50 scalping strategy monitoring market during trading hours 9:15 AM - 3:30 PM IST."

class TelegramNotifier:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        
    def send_message(self, message):
        try:
            if not self.bot_token or not self.chat_id:
                logger.warning("Telegram credentials not configured")
                return
            
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            response = requests.post(url, json=data)
            if response.status_code == 200:
                logger.info("Telegram message sent successfully")
            else:
                logger.error(f"Failed to send Telegram message: {response.text}")
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")

class GPTAssistant:
    def __init__(self, api_key, strategy_instance=None):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.conversation_history = []
        
        
    def chat(self, user_message, detailed=False):
        try:
            # Build context with recent logs
            # Build comprehensive real-time context
            realtime_data = {}
            if self.strategy:
                # Get current market data
                current_price = self.strategy.get_nifty_ltp()
                market_open = self.strategy.check_market_hours()
                
                # Calculate statistics from logs
                total_logs = len(trade_logs)
                recent_logs = trade_logs[-10:] if trade_logs else []
                
                realtime_data = {
                    'current_nifty_price': current_price,
                    'market_status': 'OPEN' if market_open else 'CLOSED',
                    'total_log_entries': total_logs,
                    'recent_logs': recent_logs,
                    'bot_running': self.strategy.is_running
                }
            
            # Enhanced context with real-time data and code awareness
            context = f"""{strategy_context}

REAL-TIME STATUS:
- NIFTY Price: {realtime_data.get('current_nifty_price', 'N/A')}
- Market: {realtime_data.get('market_status', 'Unknown')}
- Total Entries: {realtime_data.get('total_log_entries', 0)}
- Bot Status: {'Active' if realtime_data.get('bot_running', False) else 'Inactive'}

RECENT LOGS (Last 10):
{json.dumps(realtime_data.get('recent_logs', []), indent=2) if realtime_data.get('recent_logs') else 'No recent logs'}

CODE INFO:
- Strategy: NIFTY 50 scalping with Dhan API
- Components: DhanTradingStrategy class, TelegramNotifier, GPTAssistant
- Data Source: Dhan HQ API (real-time market data)
- Trading Hours: Mon-Fri 9:15 AM - 3:30 PM IST
- Analysis Interval: Every 5 minutes
- GitHub: dhan-trading-strategy repository
"""            
            system_prompt = {
                "role": "system",
                "content": f"You are a concise trading assistant. {context}. Keep answers under 50 words unless user asks for detailed explanation. Be direct and precise."
            }
            
            if detailed:
                system_prompt["content"] += " User requested detailed explanation - provide comprehensive analysis."
            
            messages = [system_prompt] + self.conversation_history[-5:] + [{"role": "user", "content": user_message}]
            
            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4-turbo-preview",
                    "messages": messages,
                    "max_tokens": 150 if not detailed else 500,
                    "temperature": 0.7
                }
            )
            
            if response.status_code == 200:
                answer = response.json()['choices'][0]['message']['content']
                self.conversation_history.append({"role": "user", "content": user_message})
                self.conversation_history.append({"role": "assistant", "content": answer})
                return answer
            else:
                logger.error(f"GPT API error: {response.text}")
                return "Sorry, I couldn't process that right now."
        except Exception as e:
            logger.error(f"Error in GPT chat: {e}")
            return f"Error: {str(e)}"

class DhanTradingStrategy:
    def __init__(self):
        self.dhan = None
        self.is_running = False
        self.telegram = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        self.gpt = GPTAssistant(OPENAI_API_KEY)
        
    def initialize(self):
        try:
            self.dhan = dhanhq(CLIENT_ID, ACCE, self)S_TOKEN)
            logger.info("Dhan API client initialized successfully")
            self.telegram.send_message("🚀 *Dhan Trading Bot Started*\n\nBot is now monitoring NIFTY 50")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Dhan API: {e}")
            return False
    
    def get_nifty_ltp(self):
        try:
            # NIFTY 50 security ID is 13, exchange is IDX_I (Index)
            response = self.dhan.get_ltp_data(                securities={"IDX_I": ["13"]}
                exchange_segment=self.dhan.IDX_I,
                            security_id="13"
                        )
            if response and 'data' in response:                nifty_data = response['data']['IDX_I'].get('13', {})
                ltp = response['data']['IDX_I']['13']['last_price']                logger.info(f"NIFTY 50 LTP: {ltp}")
                logger.info(f"NIFTY 50 LTP: {ltp}")
                            return ltp
            logger.warning("Could not fetch NIFTY LTP from response")
            return None
        except Exception as e:
            logger.error(f"Error fetching NIFTY LTP: {e}")
            return None
    
    def check_market_hours(self):
        now = datetime.now()
        current_time = now.time()
        
        market_open = now.replace(hour=9, minute=15, second=0).time()
        market_close = now.replace(hour=15, minute=30, second=0).time()
        
        is_market_open = market_open <= current_time <= market_close
        is_weekday = now.weekday() < 5
        
        return is_market_open and is_weekday
    
    def analyze_market(self):
        logger.info("Analyzing market conditions...")
        
        nifty_price = self.get_nifty_ltp()
        
        if nifty_price:
            logger.info(f"Current NIFTY 50: {nifty_price}")
            
            analysis = {
                'timestamp': datetime.now().isoformat(),
                'nifty_price': nifty_price,
                'signal': 'NEUTRAL',
                'market_open': self.check_market_hours()
            }
            
            trade_logs.append(analysis)
            if len(trade_logs) > 100:
                trade_logs.pop(0)
            
            return analysis
        
        return None
    
    def handle_telegram_message(self, update, context):
        try:
            user_message = update.message.text
            chat_id = update.message.chat_id
            
            # Check if detailed explanation requested
            detailed = any(word in user_message.lower() for word in ['explain', 'detail', 'elaborate', 'why', 'how'])
            
            # Get GPT response
            gpt_response = self.gpt.chat(user_message, detailed=detailed)
            
            context.bot.send_message(chat_id=chat_id, text=gpt_response)
        except Exception as e:
            logger.error(f"Error handling Telegram message: {e}")
    
    def start_telegram_bot(self):
        try:
            if not TELEGRAM_BOT_TOKEN:
                logger.warning("Telegram bot token not configured")
                return
            
            updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
            dp = updater.dispatcher
            
            dp.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_telegram_message))
            
            updater.start_polling()
            logger.info("Telegram bot started for GPT chat")
        except Exception as e:
            logger.error(f"Error starting Telegram bot: {e}")
    
    def run(self):
        logger.info("Starting Dhan Trading Strategy...")
        
        if not self.initialize():
            logger.error("Failed to initialize. Exiting.")
            return
        
        # Start Telegram bot in separate thread
        telegram_thread = threading.Thread(target=self.start_telegram_bot, daemon=True)
        telegram_thread.start()
        
        self.is_running = True
        logger.info("Strategy is now running. Press Ctrl+C to stop.")
        
        iteration = 0
        
        while self.is_running:
            try:
                iteration += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"Iteration: {iteration} | Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'='*60}")
                
                if self.check_market_hours():
                    logger.info("Market is OPEN - Running analysis")
                    
                    analysis = self.analyze_market()
                    
                    if analysis:
                        logger.info(f"Analysis complete: Signal = {analysis['signal']}")
                        
                        # Send periodic update to Telegram
                        if iteration % 12 == 1:  # Every hour (12 * 5 min)
                            message = f"📊 *NIFTY Update*\nPrice: {analysis['nifty_price']}\nSignal: {analysis['signal']}"
                            self.telegram.send_message(message)
                    else:
                        logger.warning("Analysis returned no data")
                else:
                    logger.info("Market is CLOSED - Waiting for market hours")
                    logger.info("Market hours: Monday-Friday, 9:15 AM - 3:30 PM IST")
                
                logger.info("Sleeping for 5 minutes...")
                time.sleep(300)
                
            except KeyboardInterrupt:
                logger.info("\nReceived stop signal from user")
                self.telegram.send_message("⚠️ *Bot Stopped*\nTrading bot has been stopped")
                self.is_running = False
                break
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                logger.info("Waiting 60 seconds before retry...")
                time.sleep(60)
        
        logger.info("Trading strategy stopped")

def main():
    logger.info("="*60)
    logger.info("DHAN NIFTY 50 TRADING STRATEGY")
    logger.info("="*60)
    logger.info(f"Client ID: {CLIENT_ID}")
    logger.info(f"Token configured: {'Yes' if ACCESS_TOKEN else 'No'}")
    logger.info(f"Telegram configured: {'Yes' if TELEGRAM_BOT_TOKEN else 'No'}")
    logger.info(f"GPT configured: {'Yes' if OPENAI_API_KEY else 'No'}")
    logger.info("="*60)
    
    strategy = DhanTradingStrategy()
    strategy.run()

if __name__ == "__main__":
    main()
