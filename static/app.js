// Socket.IO connection
const socket = io();

// State
let startTime = null;

// DOM elements
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');
const modeBadge = document.getElementById('mode-badge');
const targetName = document.getElementById('target-name');
const targetAddress = document.getElementById('target-address');
const uptime = document.getElementById('uptime');
const statDetected = document.getElementById('stat-detected');
const statCopied = document.getElementById('stat-copied');
const statSkipped = document.getElementById('stat-skipped');
const statLatency = document.getElementById('stat-latency');
const tradesBody = document.getElementById('trades-body');
const currentTime = document.getElementById('current-time');

// Format address for display
function formatAddress(addr) {
    if (!addr || addr.length < 10) return addr || '--';
    return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
}

// Format uptime
function formatUptime(startTimeStr) {
    if (!startTimeStr) return '00:00:00';
    const start = new Date(startTimeStr);
    const now = new Date();
    const diff = Math.floor((now - start) / 1000);
    
    const hours = String(Math.floor(diff / 3600)).padStart(2, '0');
    const mins = String(Math.floor((diff % 3600) / 60)).padStart(2, '0');
    const secs = String(diff % 60).padStart(2, '0');
    
    return `${hours}:${mins}:${secs}`;
}

// Update UI with state
function updateUI(state) {
    // Connection status
    if (state.connected) {
        statusDot.className = 'status-dot online';
        statusText.textContent = 'LIVE';
    } else {
        statusDot.className = 'status-dot offline';
        statusText.textContent = 'OFFLINE';
    }
    
    // Mode
    modeBadge.textContent = state.mode || 'DRY RUN';
    modeBadge.className = state.mode === 'LIVE' ? 'mode-badge live' : 'mode-badge';
    
    // Target info
    targetName.textContent = state.target_name || '--';
    targetAddress.textContent = formatAddress(state.target_address);
    
    // Stats
    if (state.stats) {
        statDetected.textContent = state.stats.trades_detected || 0;
        statCopied.textContent = state.stats.trades_copied || 0;
        statSkipped.textContent = state.stats.trades_skipped || 0;
        statLatency.textContent = `${state.stats.avg_latency || 0}ms`;
    }
    
    // Trades
    updateTradesTable(state.trades || []);
    
    // Store start time
    if (state.start_time) {
        startTime = state.start_time;
    }
}

// Update trades table
function updateTradesTable(trades) {
    tradesBody.innerHTML = '';
    
    // Fill with trades
    trades.forEach((trade, i) => {
        const row = document.createElement('tr');
        if (i === 0) row.classList.add('flash');
        
        const sideClass = trade.side === 'BUY' ? 'buy' : 'sell';
        const statusClass = trade.copied ? 'copied' : 'skipped';
        const statusText = trade.copied ? 'COPIED' : 'SKIP';
        
        row.innerHTML = `
            <td>${trade.time}</td>
            <td>${trade.title}</td>
            <td>${trade.outcome}</td>
            <td class="${sideClass}">${trade.side}</td>
            <td>${trade.size}</td>
            <td>$${trade.price}</td>
            <td>${trade.latency}ms</td>
            <td class="${statusClass}">${statusText}</td>
        `;
        tradesBody.appendChild(row);
    });
    
    // Fill empty rows
    for (let i = trades.length; i < 10; i++) {
        const row = document.createElement('tr');
        row.className = 'empty-row';
        row.innerHTML = `
            <td>--</td>
            <td>--</td>
            <td>--</td>
            <td>--</td>
            <td>--</td>
            <td>--</td>
            <td>--</td>
            <td>--</td>
        `;
        tradesBody.appendChild(row);
    }
}

// Add single trade to table (for real-time updates)
function addTrade(trade) {
    statDetected.textContent = parseInt(statDetected.textContent) + 1;
    
    if (trade.copied) {
        statCopied.textContent = parseInt(statCopied.textContent) + 1;
    } else {
        statSkipped.textContent = parseInt(statSkipped.textContent) + 1;
    }
}

// Socket events
socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('initial_state', (state) => {
    console.log('Initial state:', state);
    updateUI(state);
});

socket.on('connection_status', (data) => {
    if (data.connected) {
        statusDot.className = 'status-dot online';
        statusText.textContent = 'LIVE';
    }
});

socket.on('trade_update', (data) => {
    console.log('Trade update:', data);
    
    // Update stats
    if (data.stats) {
        statDetected.textContent = data.stats.trades_detected || 0;
        statCopied.textContent = data.stats.trades_copied || 0;
        statSkipped.textContent = data.stats.trades_skipped || 0;
        statLatency.textContent = `${data.stats.avg_latency || 0}ms`;
    }
    
    // Add trade to table
    if (data.trade) {
        const trade = data.trade;
        const firstRow = tradesBody.firstChild;
        const row = document.createElement('tr');
        row.classList.add('flash');
        
        const sideClass = trade.side === 'BUY' ? 'buy' : 'sell';
        const statusClass = trade.copied ? 'copied' : 'skipped';
        const statusText = trade.copied ? 'COPIED' : 'SKIP';
        
        row.innerHTML = `
            <td>${trade.time}</td>
            <td>${trade.title}</td>
            <td>${trade.outcome}</td>
            <td class="${sideClass}">${trade.side}</td>
            <td>${trade.size}</td>
            <td>$${trade.price}</td>
            <td>${trade.latency}ms</td>
            <td class="${statusClass}">${statusText}</td>
        `;
        
        tradesBody.insertBefore(row, firstRow);
        
        // Remove last row if more than 10
        while (tradesBody.children.length > 10) {
            tradesBody.removeChild(tradesBody.lastChild);
        }
    }
});

// Update time and uptime every second
setInterval(() => {
    currentTime.textContent = new Date().toLocaleString();
    if (startTime) {
        uptime.textContent = formatUptime(startTime);
    }
}, 1000);

// Initial time
currentTime.textContent = new Date().toLocaleString();
