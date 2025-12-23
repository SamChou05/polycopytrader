"""
Bloomberg-style Terminal Dashboard for Polymarket Copy Trader
Uses the 'rich' library for a professional trading terminal look.
"""

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich.style import Style
from datetime import datetime
import threading
import time

# Bloomberg-inspired color scheme
COLORS = {
    'bg': 'black',
    'header': 'bold white on blue',
    'positive': 'bold green',
    'negative': 'bold red',
    'neutral': 'yellow',
    'muted': 'dim white',
    'highlight': 'bold cyan',
}


class Dashboard:
    def __init__(self):
        self.console = Console()
        self.running = False
        
        # State
        self.connection_status = "DISCONNECTED"
        self.target_address = ""
        self.target_name = "Unknown"
        self.trades = []  # List of recent trades
        self.stats = {
            'trades_detected': 0,
            'trades_copied': 0,
            'trades_skipped': 0,
            'total_latency_ms': 0,
        }
        self.mode = "DRY RUN"
        self.start_time = datetime.now()
        
    def set_connected(self, status=True):
        self.connection_status = "CONNECTED" if status else "DISCONNECTED"
        
    def set_target(self, address, name="Unknown"):
        self.target_address = address
        self.target_name = name
        
    def set_mode(self, mode):
        self.mode = mode
        
    def add_trade(self, trade):
        """Add a trade to the display list."""
        self.trades.insert(0, {
            'time': datetime.now().strftime('%H:%M:%S'),
            'title': trade.get('title', 'Unknown')[:20],
            'outcome': trade.get('outcome', '?')[:10],
            'side': trade.get('side', 'BUY'),
            'size': trade.get('size', 0),
            'price': trade.get('price', 0),
            'latency': trade.get('latency_ms', 0),
            'copied': False
        })
        # Keep only last 10 trades
        self.trades = self.trades[:10]
        self.stats['trades_detected'] += 1
        if trade.get('latency_ms'):
            self.stats['total_latency_ms'] += trade['latency_ms']
            
    def mark_trade_copied(self, index=0):
        if self.trades:
            self.trades[index]['copied'] = True
            self.stats['trades_copied'] += 1
            
    def mark_trade_skipped(self):
        self.stats['trades_skipped'] += 1
        
    def _make_header(self) -> Panel:
        """Create the header panel."""
        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="center", ratio=2)
        grid.add_column(justify="right", ratio=1)
        
        # Status indicator
        if self.connection_status == "CONNECTED":
            status = Text("● LIVE", style=COLORS['positive'])
        else:
            status = Text("● OFFLINE", style=COLORS['negative'])
            
        # Title
        title = Text("POLYMARKET COPY TRADER", style="bold white")
        
        # Mode
        mode_style = COLORS['neutral'] if self.mode == "DRY RUN" else COLORS['positive']
        mode = Text(f"[{self.mode}]", style=mode_style)
        
        grid.add_row(status, title, mode)
        
        return Panel(grid, style="white on blue", height=3)
    
    def _make_target_panel(self) -> Panel:
        """Create the target info panel."""
        content = Table.grid(padding=1)
        content.add_column(style=COLORS['muted'])
        content.add_column(style=COLORS['highlight'])
        
        short_addr = f"{self.target_address[:6]}...{self.target_address[-4:]}" if len(self.target_address) > 10 else self.target_address
        
        content.add_row("TARGET:", self.target_name)
        content.add_row("ADDRESS:", short_addr)
        
        uptime = datetime.now() - self.start_time
        content.add_row("UPTIME:", str(uptime).split('.')[0])
        
        return Panel(content, title="[bold]TRACKING", border_style="blue")
    
    def _make_stats_panel(self) -> Panel:
        """Create the statistics panel."""
        content = Table.grid(padding=1)
        content.add_column(style=COLORS['muted'])
        content.add_column(justify="right")
        
        content.add_row("Detected:", Text(str(self.stats['trades_detected']), style=COLORS['highlight']))
        content.add_row("Copied:", Text(str(self.stats['trades_copied']), style=COLORS['positive']))
        content.add_row("Skipped:", Text(str(self.stats['trades_skipped']), style=COLORS['neutral']))
        
        avg_latency = 0
        if self.stats['trades_detected'] > 0:
            avg_latency = self.stats['total_latency_ms'] // self.stats['trades_detected']
        content.add_row("Avg Latency:", Text(f"{avg_latency}ms", style=COLORS['highlight']))
        
        return Panel(content, title="[bold]STATS", border_style="blue")
    
    def _make_trades_table(self) -> Panel:
        """Create the trades table."""
        table = Table(expand=True, box=None, padding=(0, 1))
        
        table.add_column("TIME", style=COLORS['muted'], width=8)
        table.add_column("MARKET", style="white", width=20)
        table.add_column("OUTCOME", style="white", width=10)
        table.add_column("SIDE", width=5)
        table.add_column("SIZE", justify="right", width=8)
        table.add_column("PRICE", justify="right", width=7)
        table.add_column("LAT", justify="right", width=6)
        table.add_column("STATUS", width=8)
        
        for trade in self.trades:
            side_style = COLORS['positive'] if trade['side'] == 'BUY' else COLORS['negative']
            status_style = COLORS['positive'] if trade['copied'] else COLORS['neutral']
            status_text = "COPIED" if trade['copied'] else "SKIP"
            
            table.add_row(
                trade['time'],
                trade['title'],
                trade['outcome'],
                Text(trade['side'], style=side_style),
                f"{trade['size']:.2f}",
                f"${trade['price']:.2f}",
                f"{trade['latency']}ms",
                Text(status_text, style=status_style)
            )
        
        # Fill empty rows
        for _ in range(10 - len(self.trades)):
            table.add_row("-", "-", "-", "-", "-", "-", "-", "-")
            
        return Panel(table, title="[bold]RECENT TRADES", border_style="blue")
    
    def _make_footer(self) -> Panel:
        """Create the footer panel."""
        text = Text()
        text.append("Press ", style=COLORS['muted'])
        text.append("Ctrl+C", style=COLORS['highlight'])
        text.append(" to exit", style=COLORS['muted'])
        text.append("  |  ", style=COLORS['muted'])
        text.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), style=COLORS['muted'])
        
        return Panel(text, style="dim", height=3)
    
    def make_layout(self) -> Layout:
        """Create the full dashboard layout."""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        layout["body"].split_row(
            Layout(name="sidebar", size=30),
            Layout(name="main")
        )
        
        layout["sidebar"].split_column(
            Layout(name="target"),
            Layout(name="stats")
        )
        
        # Assign panels
        layout["header"].update(self._make_header())
        layout["target"].update(self._make_target_panel())
        layout["stats"].update(self._make_stats_panel())
        layout["main"].update(self._make_trades_table())
        layout["footer"].update(self._make_footer())
        
        return layout
    
    def run(self, refresh_rate=1):
        """Run the dashboard in a live update loop."""
        self.running = True
        with Live(self.make_layout(), console=self.console, refresh_per_second=refresh_rate, screen=True) as live:
            while self.running:
                live.update(self.make_layout())
                time.sleep(1 / refresh_rate)
                
    def stop(self):
        self.running = False


# Singleton instance for easy access from other modules
_dashboard = None

def get_dashboard() -> Dashboard:
    global _dashboard
    if _dashboard is None:
        _dashboard = Dashboard()
    return _dashboard
