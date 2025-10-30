import json
import requests
import math

# --- Configuration ---
COIN_IDS = {
    "XRP": "ripple",
    "UNI": "uniswap",
    "SOL": "solana",
    "LINK": "chainlink",
}
VS_CURRENCY = "usd"
DAYS = 90 # Period for historical data (90 days)

# --- Optimized Pure Python RSI Calculation ---
def calculate_rsi_optimized(prices, period=90):
    """Calculates the Relative Strength Index (RSI) using pure Python."""
    if len(prices) < period + 1:
        return 0.0 # Not enough data
    
    # Calculate price changes
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    
    # Calculate initial average gain and loss
    gains = [d if d > 0 else 0 for d in deltas[:period]]
    losses = [-d if d < 0 else 0 for d in deltas[:period]]
    
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    
    # Calculate subsequent average gain and loss (Wilder's smoothing)
    for i in range(period, len(deltas)):
        delta = deltas[i]
        gain = delta if delta > 0 else 0
        loss = -delta if delta < 0 else 0
        
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        
    # Calculate RS and RSI
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# --- Main Data Fetch and Processing ---
def get_real_time_data():
    """Fetches historical data, calculates 90-day RSI and Peak, and returns real-time price."""
    
    results = {}
    
    for ticker, coin_id in COIN_IDS.items():
        try:
            # Fetch 90 days of historical data (daily candles)
            # We fetch 91 days to ensure we have enough data for the 90-day RSI calculation
            history_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
            history_response = requests.get(
                history_url,
                params={
                    "vs_currency": VS_CURRENCY,
                    "days": DAYS + 1, # Fetch 91 days
                    "interval": "daily"
                },
                timeout=8 # Reduce timeout slightly for faster execution
            )
            history_response.raise_for_status()
            history_data = history_response.json()
            
            # Extract prices
            prices = [item[1] for item in history_data.get('prices', [])]
            if not prices:
                results[ticker] = {"error": "No historical price data."}
                continue
            
            # 1. Calculate 90-Day RSI
            rsi_90 = calculate_rsi_optimized(prices, period=DAYS)
            
            # 2. Find 90-Day Peak
            peak_90 = max(prices)
            
            # 3. Get Real-Time Price
            current_price = prices[-1]

            # 4. Calculate Correction
            correction_pct = ((peak_90 - current_price) / peak_90) * 100
            
            results[ticker] = {
                "price": round(current_price, 2),
                "peak": round(peak_90, 2),
                "rsi": round(rsi_90, 2),
                "correction": round(correction_pct, 2),
            }

        except requests.exceptions.RequestException as e:
            results[ticker] = {"error": str(e)}
        except Exception as e:
            results[ticker] = {"error": f"Processing error: {str(e)}"}
            
    # Simulate Fear & Greed Index
    fear_greed_index = 30 

    return {
        "statusCode": 200,
        "body": json.dumps({
            "data": results,
            "sentiment": fear_greed_index,
            "status": "success"
        })
    }

# Netlify function handler
def handler(event, context):
    return get_real_time_data()

if __name__ == "__main__":
    # Local test execution
    print(get_real_time_data())
