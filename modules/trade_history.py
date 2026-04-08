import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from modules.logger import setup_logger

class TradeHistory:
    def __init__(self, json_file='data/trades.json', state_file='data/bot_state.json'):
        self.json_file = json_file
        self.state_file = state_file
        self.logger = setup_logger()
        
        # Initialize files if they don't exist
        self._init_files()
    
    def _init_files(self):
        """Create JSON files if they don't exist"""
        # Create data directory if needed
        os.makedirs('data', exist_ok=True)
        
        # Initialize trades.json
        if not os.path.exists(self.json_file):
            self._save_trades([])
        
        # Initialize bot_state.json
        if not os.path.exists(self.state_file):
            self._save_state({
                'active_position': None,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_pnl': 0.0,
                'last_update': datetime.now().isoformat()
            })
    
    def _load_trades(self) -> List[Dict]:
        """Load all trades from JSON"""
        try:
            with open(self.json_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_trades(self, trades: List[Dict]):
        """Save trades to JSON"""
        with open(self.json_file, 'w') as f:
            json.dump(trades, f, indent=2)
    
    def _load_state(self) -> Dict:
        """Load bot state"""
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                'active_position': None,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_pnl': 0.0
            }
    
    def _save_state(self, state: Dict):
        """Save bot state"""
        state['last_update'] = datetime.now().isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def add_trade(self, trade_data: Dict):
        """Add a completed trade to history"""
        trades = self._load_trades()
        
        # Add timestamp if not present
        if 'timestamp' not in trade_data:
            trade_data['timestamp'] = datetime.now().isoformat()
        
        # Add trade ID
        trade_data['trade_id'] = len(trades) + 1
        
        trades.append(trade_data)
        self._save_trades(trades)
        
        # Update stats
        self._update_stats(trade_data)
        
        self.logger.info(f"📝 Trade #{trade_data['trade_id']} saved to JSON: {trade_data['signal']} {trade_data['entry']} -> {trade_data.get('exit_price', 'open')}")
    
    def _update_stats(self, trade_data: Dict):
        """Update bot statistics"""
        state = self._load_state()
        
        state['total_trades'] += 1
        
        # Check if trade is closed
        if 'exit_price' in trade_data and 'pnl' in trade_data:
            if trade_data['pnl'] > 0:
                state['winning_trades'] += 1
            else:
                state['losing_trades'] += 1
            
            state['total_pnl'] += trade_data['pnl']
        
        self._save_state(state)
    
    def update_position(self, position_data: Dict):
        """Update current active position in state"""
        state = self._load_state()
        state['active_position'] = position_data
        self._save_state(state)
    
    def close_position(self, exit_price: float, pnl: float, exit_reason: str):
        """Close current position and record trade"""
        state = self._load_state()
        
        if state['active_position']:
            # Create trade record
            trade_record = {
                **state['active_position'],
                'exit_price': exit_price,
                'pnl': pnl,
                'exit_reason': exit_reason,
                'exit_time': datetime.now().isoformat(),
                'duration_seconds': (
                    datetime.now() - datetime.fromisoformat(state['active_position']['entry_time'])
                ).total_seconds()
            }
            
            # Add to history
            self.add_trade(trade_record)
            
            # Clear active position
            state['active_position'] = None
            self._save_state(state)
            
            return trade_record
        
        return None
    
    def get_active_position(self) -> Optional[Dict]:
        """Get current active position"""
        state = self._load_state()
        return state.get('active_position')
    
    def get_stats(self) -> Dict:
        """Get bot statistics"""
        state = self._load_state()
        trades = self._load_trades()
        
        # Calculate additional stats
        if state['total_trades'] > 0:
            win_rate = (state['winning_trades'] / state['total_trades']) * 100
        else:
            win_rate = 0
        
        # Calculate average PnL
        closed_trades = [t for t in trades if 'pnl' in t]
        if closed_trades:
            avg_pnl = sum(t['pnl'] for t in closed_trades) / len(closed_trades)
        else:
            avg_pnl = 0
        
        return {
            'total_trades': state['total_trades'],
            'winning_trades': state['winning_trades'],
            'losing_trades': state['losing_trades'],
            'win_rate': round(win_rate, 2),
            'total_pnl': round(state['total_pnl'], 2),
            'avg_pnl': round(avg_pnl, 2),
            'active_position': state.get('active_position') is not None,
            'last_update': state.get('last_update')
        }
    
    def get_recent_trades(self, limit: int = 10) -> List[Dict]:
        """Get recent trades"""
        trades = self._load_trades()
        return trades[-limit:][::-1]  # Most recent first
    
    def export_to_csv(self, csv_file='data/trades.csv'):
        """Export trade history to CSV for analysis"""
        import csv
        
        trades = self._load_trades()
        if not trades:
            self.logger.info("No trades to export")
            return
        
        # Get all unique keys
        keys = set()
        for trade in trades:
            keys.update(trade.keys())
        
        keys = sorted(list(keys))
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(trades)
        
        self.logger.info(f"📊 Trade history exported to {csv_file}")
    
    def print_summary(self):
        """Print trade summary to console"""
        stats = self.get_stats()
        recent = self.get_recent_trades(5)
        
        print("\n" + "="*60)
        print("📊 TRADE HISTORY SUMMARY")
        print("="*60)
        print(f"Total Trades: {stats['total_trades']}")
        print(f"Winning Trades: {stats['winning_trades']}")
        print(f"Losing Trades: {stats['losing_trades']}")
        print(f"Win Rate: {stats['win_rate']}%")
        print(f"Total PnL: ${stats['total_pnl']:.2f}")
        print(f"Average PnL: ${stats['avg_pnl']:.2f}")
        print(f"Active Position: {'Yes' if stats['active_position'] else 'No'}")
        
        if recent:
            print("\n📋 Recent Trades:")
            print("-"*60)
            for trade in recent:
                signal = trade.get('signal', 'N/A')
                entry = trade.get('entry', 0)
                exit_price = trade.get('exit_price', 'Open')
                pnl = trade.get('pnl', 0)
                result = "✅" if pnl > 0 else "❌" if pnl < 0 else "⏸️"
                print(f"  {result} #{trade.get('trade_id')}: {signal} @ ${entry:.2f} -> ${exit_price:.2f} | PnL: ${pnl:.2f}")
        
        print("="*60 + "\n")