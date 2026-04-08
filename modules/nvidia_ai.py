import requests
import json
from config import NVIDIA_API_KEY, NVIDIA_API_URL, MODEL_NAME, AI_PROMPT

class NvidiaAI:
    def __init__(self):
        self.api_key = NVIDIA_API_KEY
        self.api_url = NVIDIA_API_URL
        self.model = MODEL_NAME
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        print(f"🤖 NVIDIA AI Initialized with model: {self.model}")
    
    def get_signal(self, market_data):
        """Get trading signal from NVIDIA AI"""
        
        # Prepare prompt with real data
        prompt = AI_PROMPT
        prompt = prompt.replace('${price}', str(market_data['price']))
        prompt = prompt.replace('${rsi}', str(market_data['rsi']))
        prompt = prompt.replace('${trend}', market_data['ema_trend'].lower())
        prompt = prompt.replace('${confidence}', '75')
        
        # Dynamic SL/TP calculations
        sl_buy = round(market_data['price'] * 0.98, 2)
        tp_buy = round(market_data['price'] * 1.04, 2)
        sl_sell = round(market_data['price'] * 1.02, 2)
        tp_sell = round(market_data['price'] * 0.96, 2)
        
        prompt = prompt.replace('${price*0.98}', str(sl_buy))
        prompt = prompt.replace('${price*1.04}', str(tp_buy))
        prompt = prompt.replace('${price*1.02}', str(sl_sell))
        prompt = prompt.replace('${price*0.96}', str(tp_sell))
        
        # Call NVIDIA API
        try:
            payload = {
                "model": self.model,  # This should be "meta/llama3-70b-instruct"
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are a crypto trading assistant. Always respond with the exact format requested. No explanations, just the data."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 100,
                "top_p": 0.95
            }
            
            print(f"📡 Calling NVIDIA API...")
            print(f"   URL: {self.api_url}")
            print(f"   Model: {self.model}")
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=15
            )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content']
                print(f"   AI Response: {ai_response}")
                return self.parse_response(ai_response)
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ AI request failed: {e}")
            return None
    
    def parse_response(self, ai_response):
        """Parse AI response into structured signal"""
        try:
            # Clean the response
            ai_response = ai_response.strip().upper()
            
            # Look for pipe-delimited format
            if '|' in ai_response:
                lines = ai_response.split('\n')
                for line in lines:
                    if '|' in line:
                        parts = line.split('|')
                        if len(parts) >= 5:
                            signal = parts[0].strip()
                            # Validate signal
                            if signal not in ['BUY', 'SELL', 'HOLD']:
                                signal = 'HOLD'
                            
                            return {
                                'signal': signal,
                                'entry': float(parts[1]) if parts[1] != '0' else 0,
                                'sl': float(parts[2]) if parts[2] != '0' else 0,
                                'tp': float(parts[3]) if parts[3] != '0' else 0,
                                'confidence': int(parts[4])
                            }
            
            # Check for simple BUY/SELL/HOLD
            if 'BUY' in ai_response and 'HOLD' not in ai_response:
                return {
                    'signal': 'BUY',
                    'entry': 0,
                    'sl': 0,
                    'tp': 0,
                    'confidence': 60
                }
            elif 'SELL' in ai_response:
                return {
                    'signal': 'SELL',
                    'entry': 0,
                    'sl': 0,
                    'tp': 0,
                    'confidence': 60
                }
            elif 'HOLD' in ai_response:
                return {
                    'signal': 'HOLD',
                    'entry': 0,
                    'sl': 0,
                    'tp': 0,
                    'confidence': 50
                }
            
            # Default to HOLD
            print(f"⚠️ Could not parse AI response: {ai_response}")
            return {
                'signal': 'HOLD',
                'entry': 0,
                'sl': 0,
                'tp': 0,
                'confidence': 50
            }
            
        except Exception as e:
            print(f"❌ Parse error: {e}")
            return None