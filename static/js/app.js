// Global variables
let monitoringActive = false;
let updateInterval = null;
let currentFontSize = 16;
let futuresMode = false;
let currentEditingPair = null;

// Performance optimization variables
let priceCache = new Map();
let lastUpdateTime = 0;
let updateDebounceTimer = null;
let domUpdateQueue = [];
let isUpdatingDOM = false;

// Cache configuration
const CACHE_DURATION = 2000; // 2 seconds
const DOM_UPDATE_BATCH_SIZE = 10;
const DEBOUNCE_DELAY = 100; // 100ms debounce for rapid updates

// Load saved states on page load
document.addEventListener('DOMContentLoaded', function() {
    loadSavedStates();
    checkMonitoringStatus();
    loadTradingPairs();
    loadNtfyConfig();
    initializeSectionStates();
});

// Load saved states from localStorage
function loadSavedStates() {
    // Load font size
    const savedFontSize = localStorage.getItem('fontSize');
    if (savedFontSize) {
        currentFontSize = parseInt(savedFontSize);
        document.getElementById('fontSize').value = currentFontSize;
        document.getElementById('fontSizeValue').textContent = currentFontSize + 'px';
        changeFontSize(currentFontSize);
    }
    
    // Load futures mode
    const savedFuturesMode = localStorage.getItem('futuresMode');
    if (savedFuturesMode !== null) {
        futuresMode = savedFuturesMode === 'true';
        updateFuturesButton();
    }
    
    // Load section states
    const savedSectionStates = localStorage.getItem('sectionStates');
    if (savedSectionStates) {
        const sectionStates = JSON.parse(savedSectionStates);
        Object.keys(sectionStates).forEach(sectionId => {
            if (sectionStates[sectionId]) {
                const content = document.getElementById(sectionId);
                if (content && content.classList.contains('section-content')) {
                    content.classList.add('collapsed');
                    // Find the corresponding toggle icon in the section header
                    const configSection = content.closest('.config-section');
                    if (configSection) {
                        const toggleIcon = configSection.querySelector('.toggle-icon');
                        if (toggleIcon) {
                            toggleIcon.textContent = '▶';
                            toggleIcon.classList.add('collapsed');
                        }
                    }
                }
            }
        });
    } else {
        // Default to collapsed state for all sections
        const sections = ['control-section', 'ntfy-section', 'trading-section'];
        sections.forEach(sectionId => {
            const content = document.getElementById(sectionId);
            if (content && content.classList.contains('section-content')) {
                content.classList.add('collapsed');
                // Find the corresponding toggle icon in the section header
                const configSection = content.closest('.config-section');
                if (configSection) {
                    const toggleIcon = configSection.querySelector('.toggle-icon');
                    if (toggleIcon) {
                        toggleIcon.textContent = '▶';
                        toggleIcon.classList.add('collapsed');
                    }
                }
            }
        });
    }
}

// Save states to localStorage
function saveStates() {
    localStorage.setItem('fontSize', currentFontSize);
    localStorage.setItem('futuresMode', futuresMode);
}

// Update futures button text
function updateFuturesButton() {
    const futuresBtn = document.getElementById('futuresBtn');
    if (futuresBtn) {
        futuresBtn.textContent = `Futures Mode: ${futuresMode ? 'ON' : 'OFF'}`;
    }
}

// Section toggle functionality
function toggleSection(sectionId) {
    console.log('Toggling section:', sectionId);
    
    // Find the section header that was clicked
    const sectionHeader = event.currentTarget;
    if (!sectionHeader) {
        console.error('Section header not found');
        return;
    }
    
    // Find the content within the same config-section
    const configSection = sectionHeader.closest('.config-section');
    if (!configSection) {
        console.error('Config section not found');
        return;
    }
    
    const content = configSection.querySelector('.section-content');
    if (!content) {
        console.error('Content not found for section');
        return;
    }
    
    const toggleIcon = sectionHeader.querySelector('.toggle-icon');
    if (!toggleIcon) {
        console.error('Toggle icon not found for section');
        return;
    }
    
    console.log('Before toggle - collapsed:', content.classList.contains('collapsed'));
    
    if (content.classList.contains('collapsed')) {
        content.classList.remove('collapsed');
        toggleIcon.textContent = '▼';
        console.log('Section expanded');
    } else {
        content.classList.add('collapsed');
        toggleIcon.textContent = '▶';
        console.log('Section collapsed');
    }
    
    console.log('After toggle - collapsed:', content.classList.contains('collapsed'));
    
    // Save section states to localStorage
    saveSectionStates();
}

function saveSectionStates() {
    const sections = ['control-section', 'ntfy-section', 'trading-section'];
    const sectionStates = {};
    
    sections.forEach(sectionId => {
        const content = document.getElementById(sectionId);
        if (content && content.classList.contains('section-content')) {
            sectionStates[sectionId] = content.classList.contains('collapsed');
        }
    });
    
    localStorage.setItem('sectionStates', JSON.stringify(sectionStates));
    console.log('Section states saved:', sectionStates);
}

function initializeSectionStates() {
    const sections = ['control-section', 'ntfy-section', 'trading-section'];
    
    // Check if section states are saved in localStorage
    const savedSectionStates = localStorage.getItem('sectionStates');
    if (savedSectionStates) {
        const sectionStates = JSON.parse(savedSectionStates);
        
        sections.forEach(sectionId => {
            if (sectionStates[sectionId]) {
                const content = document.getElementById(sectionId);
                if (content && content.classList.contains('section-content')) {
                    content.classList.add('collapsed');
                    // Find the corresponding toggle icon in the section header
                    const configSection = content.closest('.config-section');
                    if (configSection) {
                        const toggleIcon = configSection.querySelector('.toggle-icon');
                        if (toggleIcon) {
                            toggleIcon.textContent = '▶';
                            toggleIcon.classList.add('collapsed');
                        }
                    }
                }
            }
        });
    } else {
        // Default to collapsed state for all sections
        sections.forEach(sectionId => {
            const content = document.getElementById(sectionId);
            if (content && content.classList.contains('section-content')) {
                content.classList.add('collapsed');
                // Find the corresponding toggle icon in the section header
                const configSection = content.closest('.config-section');
                if (configSection) {
                    const toggleIcon = configSection.querySelector('.toggle-icon');
                    if (toggleIcon) {
                        toggleIcon.textContent = '▶';
                        toggleIcon.classList.add('collapsed');
                    }
                }
            }
        });
        
        // Save the default collapsed state
        saveSectionStates();
    }
}

function expandAllSections() {
    const sections = ['control-section', 'ntfy-section', 'trading-section'];
    
    // Batch all DOM updates
    const updates = [];
    
    sections.forEach(sectionId => {
        const content = document.getElementById(sectionId);
        if (content && content.classList.contains('section-content')) {
            content.classList.remove('collapsed');
            // Find the corresponding toggle icon in the section header
            const configSection = content.closest('.config-section');
            if (configSection) {
                const toggleIcon = configSection.querySelector('.toggle-icon');
                if (toggleIcon) {
                    toggleIcon.textContent = '▼';
                    toggleIcon.classList.remove('collapsed');
                }
            }
        }
    });
    
    // Save section states
    saveSectionStates();
}

function collapseAllSections() {
    const sections = ['control-section', 'ntfy-section', 'trading-section'];
    
    // Batch all DOM updates
    const updates = [];
    
    sections.forEach(sectionId => {
        const content = document.getElementById(sectionId);
        if (content && content.classList.contains('section-content')) {
            content.classList.add('collapsed');
            // Find the corresponding toggle icon in the section header
            const configSection = content.closest('.config-section');
            if (configSection) {
                const toggleIcon = configSection.querySelector('.toggle-icon');
                if (toggleIcon) {
                    toggleIcon.textContent = '▶';
                    toggleIcon.classList.add('collapsed');
                }
            }
        }
    });
    
    // Save section states
    saveSectionStates();
}

// NTFY Configuration
function loadNtfyConfig() {
    fetch('/api/ntfy_config')
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            document.getElementById('ntfyServer').value = data.config.server || 'https://ntfy.sh';
            document.getElementById('ntfyTopic').value = data.config.topic || '';
            document.getElementById('ntfyPassword').value = data.config.password || '';
        }
    })
    .catch(error => {
        console.error('Error loading NTFY config:', error);
    });
}

function saveNtfyConfig() {
    const server = document.getElementById('ntfyServer').value.trim();
    const topic = document.getElementById('ntfyTopic').value.trim();
    const password = document.getElementById('ntfyPassword').value.trim();

    if (!server || !topic) {
        showAlert('Please fill in server and topic fields!', 'error');
        return;
    }

    fetch('/api/ntfy_config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            server: server,
            topic: topic,
            password: password
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showAlert('NTFY configuration saved successfully!', 'success');
        } else {
            showAlert(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error saving NTFY config:', error);
        showAlert('Error saving NTFY configuration', 'error');
    });
}

function testNtfyNotification() {
    const server = document.getElementById('ntfyServer').value.trim();
    const topic = document.getElementById('ntfyTopic').value.trim();
    const password = document.getElementById('ntfyPassword').value.trim();

    if (!server || !topic) {
        showAlert('Please configure NTFY server and topic first!', 'error');
        return;
    }

    fetch('/api/test_ntfy', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            server: server,
            topic: topic,
            password: password
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showAlert('Test notification sent successfully! Check your NTFY app/browser.', 'success');
        } else {
            showAlert(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error testing NTFY:', error);
        showAlert('Error sending test notification', 'error');
    });
}

// Check if monitoring is already active (persistent state)
function checkMonitoringStatus() {
    // Check cache first
    const now = Date.now();
    if (isCacheValid(lastUpdateTime)) {
        return;
    }
    
    fetch('/api/monitoring_status')
    .then(response => response.json())
    .then(data => {
        monitoringActive = data.monitoring_active;
        futuresMode = data.futures_mode;
        
        // Update UI based on status
        if (monitoringActive) {
            queueDOMUpdate(() => {
                document.getElementById('startBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
                document.getElementById('status').textContent = 'Status: Monitoring Active';
            });
            
            // Start price updates if not already running
            if (!updateInterval) {
                updateInterval = setInterval(updatePrices, 1500);
                updatePrices(); // Initial update
            }
        } else {
            queueDOMUpdate(() => {
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
                document.getElementById('status').textContent = 'Status: Stopped';
            });
            
            // Stop price updates
            if (updateInterval) {
                clearInterval(updateInterval);
                updateInterval = null;
            }
        }
        
        updateFuturesButton();
    })
    .catch(error => {
        console.error('Error checking monitoring status:', error);
    });
}

// Font size control
function changeFontSize(size) {
    currentFontSize = parseInt(size);
    
    // Debounced font size update to prevent rapid DOM updates
    const debouncedFontUpdate = debounce(() => {
        const priceCards = document.querySelectorAll('.price-card');
        priceCards.forEach(card => {
            card.style.fontSize = currentFontSize + 'px';
        });
        
        // Save to localStorage
        localStorage.setItem('fontSize', currentFontSize);
    }, 150); // Slightly longer delay for font changes
    
    debouncedFontUpdate();
    
    // Update display immediately
    document.getElementById('fontSizeValue').textContent = currentFontSize + 'px';
}

// Monitoring controls
function startMonitoring() {
    // Clear any existing cache
    priceCache.clear();
    lastUpdateTime = 0;
    
    fetch('/api/start_monitoring', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            monitoringActive = true;
            
            // Update UI immediately
            queueDOMUpdate(() => {
                document.getElementById('startBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
                document.getElementById('status').textContent = 'Status: Monitoring Active';
            });
            
            // Start price updates with optimized interval
            if (updateInterval) {
                clearInterval(updateInterval);
            }
            updateInterval = setInterval(updatePrices, 1500);
            
            // Initial price update
            updatePrices();
            
            showAlert('Monitoring started successfully!', 'success');
        } else {
            showAlert(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error starting monitoring:', error);
        showAlert('Error starting monitoring', 'error');
    });
}

function stopMonitoring() {
    fetch('/api/stop_monitoring', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            monitoringActive = false;
            
            // Clear interval
            if (updateInterval) {
                clearInterval(updateInterval);
                updateInterval = null;
            }
            
            // Update UI immediately
            queueDOMUpdate(() => {
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
                document.getElementById('status').textContent = 'Status: Stopped';
            });
            
            showAlert('Monitoring stopped!', 'success');
        } else {
            showAlert(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error stopping monitoring:', error);
        showAlert('Error stopping monitoring', 'error');
    });
}

function toggleFutures() {
    fetch('/api/toggle_futures', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            futuresMode = data.futures_mode;
            updateFuturesButton();
            
            // Clear price cache when switching modes
            priceCache.clear();
            lastUpdateTime = 0;
            
            // Refresh prices if monitoring is active
            if (monitoringActive) {
                updatePrices();
            }
            
            showAlert(data.message, 'success');
        } else {
            showAlert(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error toggling futures mode:', error);
        showAlert('Error toggling futures mode', 'error');
    });
}

// Price updates
function updatePrices() {
    // Check cache first
    const now = Date.now();
    if (isCacheValid(lastUpdateTime)) {
        return;
    }
    
    // Check if we're already updating
    if (isUpdatingDOM) {
        return;
    }
    
    fetch('/api/prices')
    .then(response => response.json())
    .then(data => {
        // Update global timestamp in Vietnam timezone
        const vietnamTime = new Date().toLocaleString('en-US', {
            timeZone: 'Asia/Ho_Chi_Minh',
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
        
        queueDOMUpdate(() => {
            document.getElementById('globalTimestamp').textContent = `Last updated: ${vietnamTime}`;
        });
        
        // Update price cache
        lastUpdateTime = now;
        priceCache.clear();
        
        if (data.prices && Object.keys(data.prices).length > 0) {
            const priceGrid = document.getElementById('priceGrid');
            
            // Batch DOM updates for better performance
            const fragment = document.createDocumentFragment();
            
            Object.entries(data.prices).forEach(([pair, price]) => {
                if (price !== null) {
                    const priceCard = document.createElement('div');
                    priceCard.className = 'price-card';
                    priceCard.style.fontSize = currentFontSize + 'px';
                    
                    const coinName = pair.split('/')[0];
                    const formattedPrice = formatPrice(parseFloat(price), pair);
                    
                    priceCard.innerHTML = `
                        <div class="coin-info">
                            <span class="coin-symbol">${coinName}</span>
                            <span class="coin-name">${pair}</span>
                        </div>
                        <div class="price-info">
                            <span class="price-value">$${formattedPrice}</span>
                        </div>
                    `;
                    
                    // Add hover effect
                    priceCard.addEventListener('mouseenter', () => {
                        priceCard.style.opacity = '0.7';
                    });
                    
                    priceCard.addEventListener('mouseleave', () => {
                        priceCard.style.opacity = '1';
                    });
                    
                    fragment.appendChild(priceCard);
                }
            });
            
            // Single DOM update for better performance
            queueDOMUpdate(() => {
                priceGrid.innerHTML = '';
                priceGrid.appendChild(fragment);
            });
        } else {
            queueDOMUpdate(() => {
                document.getElementById('priceGrid').innerHTML = '<div class="loading">No trading pairs configured. Add some pairs to see prices here.</div>';
            });
        }
    })
    .catch(error => {
        console.error('Error updating prices:', error);
        queueDOMUpdate(() => {
            document.getElementById('priceGrid').innerHTML = '<div class="loading">Error loading prices. Please try again.</div>';
        });
    });
}

// Price formatting with caching for better performance
const priceFormatCache = new Map();

function formatPrice(price, pair = '') {
    if (price === null || price === undefined || isNaN(price)) {
        return '0.00';
    }
    
    // Check cache first
    const cacheKey = `${price}_${pair}`;
    if (priceFormatCache.has(cacheKey)) {
        return priceFormatCache.get(cacheKey);
    }
    
    // Determine decimal places based on coin type
    let decimalPlaces;
    if (pair && pair.includes('BTC')) {
        decimalPlaces = 6; // BTC: 6 decimal places
    } else {
        decimalPlaces = 3; // Other coins: 3 decimal places
    }
    
    // Format price with appropriate decimal places
    let priceStr = price.toFixed(decimalPlaces);
    
    // Remove trailing zeros after decimal
    priceStr = priceStr.replace(/\.?0+$/, '');
    
    // Add commas for thousands
    if (priceStr.includes('.')) {
        const parts = priceStr.split('.');
        parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        priceStr = parts.join('.');
    } else {
        priceStr = priceStr.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }
    
    // Cache the result
    priceFormatCache.set(cacheKey, priceStr);
    
    // Limit cache size to prevent memory issues
    if (priceFormatCache.size > 1000) {
        const firstKey = priceFormatCache.keys().next().value;
        priceFormatCache.delete(firstKey);
    }
    
    return priceStr;
}

function refreshPrices() {
    // Clear cache to force fresh data
    priceCache.clear();
    lastUpdateTime = 0;
    
    // Debounced update to prevent rapid calls
    const debouncedUpdate = debounce(() => {
        updatePrices();
    }, DEBOUNCE_DELAY);
    
    debouncedUpdate();
    
    showAlert('Prices refreshed!', 'success');
}

// Trading pairs management
function loadTradingPairs() {
    fetch('/api/trading_pairs')
    .then(response => response.json())
    .then(data => {
        const pairsList = document.getElementById('pairsList');
        
        if (!data.pairs || data.pairs.length === 0) {
            queueDOMUpdate(() => {
                pairsList.innerHTML = '<div class="loading">No trading pairs configured</div>';
            });
            return;
        }
        
        // Use DocumentFragment for better performance
        const fragment = document.createDocumentFragment();
        
        data.pairs.forEach(({pair, upper, lower}) => {
            const pairItem = document.createElement('div');
            pairItem.className = 'pair-item';
            
            pairItem.innerHTML = `
                <div class="pair-info">
                    <span class="pair-name">${pair}</span>
                    <span class="pair-thresholds">
                        Upper: $${upper || 'Not set'} | Lower: $${lower || 'Not set'}
                    </span>
                </div>
                <div class="pair-actions">
                    <button class="edit-btn" onclick="editTradingPair('${pair}', ${upper || 0}, ${lower || 0})">Edit</button>
                    <button class="delete-btn" onclick="deleteTradingPair('${pair}')">Delete</button>
                </div>
            `;
            
            fragment.appendChild(pairItem);
        });
        
        // Single DOM update for better performance
        queueDOMUpdate(() => {
            pairsList.innerHTML = '';
            pairsList.appendChild(fragment);
        });
    })
    .catch(error => {
        console.error('Error loading trading pairs:', error);
        queueDOMUpdate(() => {
            document.getElementById('pairsList').innerHTML = '<div class="loading">Error loading trading pairs</div>';
        });
    });
}

function addTradingPair() {
    let pair = document.getElementById('pairInput').value.trim().toUpperCase();
    const upper = parseFloat(document.getElementById('upperInput').value);
    const lower = parseFloat(document.getElementById('lowerInput').value);

    if (!pair || !upper || !lower) {
        showAlert('Please fill all required fields!', 'error');
        return;
    }

    if (upper <= lower) {
        showAlert('Upper price must be greater than lower price!', 'error');
        return;
    }

    // Convert input format to standard format
    pair = normalizePairFormat(pair);

    fetch('/api/add_pair', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            pair: pair,
            upper: upper,
            lower: lower
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Clear form
            queueDOMUpdate(() => {
                document.getElementById('pairInput').value = '';
                document.getElementById('upperInput').value = '';
                document.getElementById('lowerInput').value = '';
            });
            
            // Reload trading pairs
            loadTradingPairs();
            
            // Clear cache and refresh prices if monitoring is active
            if (monitoringActive) {
                priceCache.clear();
                lastUpdateTime = 0;
                updatePrices();
            }
            
            showAlert(data.message, 'success');
        } else {
            showAlert(data.message, 'error');
        }
    });
}

// Helper function to normalize pair format
function normalizePairFormat(input) {
    // Remove any spaces
    input = input.replace(/\s/g, '');
    
    // If it's just a coin name (e.g., "DOT"), add "/USDT"
    if (!input.includes('/') && !input.includes('-')) {
        return input + '/USDT';
    }
    
    // If it's in format "DOT-USDT", convert to "DOT/USDT"
    if (input.includes('-')) {
        return input.replace('-', '/');
    }
    
    // If it's already in format "DOT/USDT", return as is
    return input;
}

function editTradingPair(pair, upper, lower) {
    currentEditingPair = pair;
    document.getElementById('editPairName').value = pair;
    document.getElementById('editUpperInput').value = upper;
    document.getElementById('editLowerInput').value = lower;
    document.getElementById('editModal').style.display = 'block';
}

function closeEditModal() {
    document.getElementById('editModal').style.display = 'none';
    currentEditingPair = null;
}

function saveEdit() {
    const upper = parseFloat(document.getElementById('editUpperInput').value);
    const lower = parseFloat(document.getElementById('editLowerInput').value);

    if (!upper || !lower) {
        showAlert('Please fill all required fields!', 'error');
        return;
    }

    if (upper <= lower) {
        showAlert('Upper price must be greater than lower price!', 'error');
        return;
    }

    fetch('/api/edit_pair', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            pair: currentEditingPair,
            upper: upper,
            lower: lower
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            closeEditModal();
            loadTradingPairs();
            
            // Clear cache and refresh prices if monitoring is active
            if (monitoringActive) {
                priceCache.clear();
                lastUpdateTime = 0;
                updatePrices();
            }
            
            showAlert(data.message, 'success');
        } else {
            showAlert(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error editing trading pair:', error);
        showAlert('Error editing trading pair', 'error');
    });
}

function deleteTradingPair(pair) {
    if (!confirm(`Are you sure you want to delete ${pair}?`)) {
        return;
    }

    fetch('/api/delete_pair', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({pair: pair})
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            loadTradingPairs();
            
            // Clear cache and refresh prices if monitoring is active
            if (monitoringActive) {
                priceCache.clear();
                lastUpdateTime = 0;
                updatePrices();
            }
            
            showAlert(data.message, 'success');
        } else {
            showAlert(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error deleting trading pair:', error);
        showAlert('Error deleting trading pair', 'error');
    });
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('editModal');
    if (event.target === modal) {
        closeEditModal();
    }
}

// Utility functions
function showAlert(message, type) {
    // Remove existing alerts first
    const existingAlerts = document.querySelectorAll('.alert');
    existingAlerts.forEach(alert => alert.remove());
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    
    // Add to DOM
    queueDOMUpdate(() => {
        document.body.appendChild(alert);
    });
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            queueDOMUpdate(() => {
                alert.remove();
            });
        }
    }, 3000);
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey || e.metaKey) {
        switch(e.key) {
            case 's':
                e.preventDefault();
                if (!monitoringActive) {
                    startMonitoring();
                } else {
                    stopMonitoring();
                }
                break;
            case 'r':
                e.preventDefault();
                refreshPrices();
                break;
            case 'f':
                e.preventDefault();
                toggleFutures();
                break;
        }
    }
    
    // Close modal with Escape key
    if (e.key === 'Escape') {
        closeEditModal();
    }
}); 

// Performance optimization functions
function debounce(func, delay) {
    return function(...args) {
        clearTimeout(updateDebounceTimer);
        updateDebounceTimer = setTimeout(() => func.apply(this, args), delay);
    };
}

function isCacheValid(timestamp) {
    return Date.now() - timestamp < CACHE_DURATION;
}

function batchDOMUpdates() {
    if (isUpdatingDOM || domUpdateQueue.length === 0) return;
    
    isUpdatingDOM = true;
    const updates = domUpdateQueue.splice(0, DOM_UPDATE_BATCH_SIZE);
    
    // Use requestAnimationFrame for smooth updates
    requestAnimationFrame(() => {
        updates.forEach(update => {
            try {
                update();
            } catch (error) {
                console.error('DOM update error:', error);
            }
        });
        
        isUpdatingDOM = false;
        
        // Process remaining updates if any
        if (domUpdateQueue.length > 0) {
            setTimeout(batchDOMUpdates, 16); // ~60fps
        }
    });
}

function queueDOMUpdate(updateFunction) {
    domUpdateQueue.push(updateFunction);
    if (!isUpdatingDOM) {
        batchDOMUpdates();
    }
} 

// Cleanup function to prevent memory leaks
function cleanup() {
    // Clear all intervals
    if (updateInterval) {
        clearInterval(updateInterval);
        updateInterval = null;
    }
    
    // Clear all timeouts
    if (updateDebounceTimer) {
        clearTimeout(updateDebounceTimer);
        updateDebounceTimer = null;
    }
    
    // Clear caches
    priceCache.clear();
    priceFormatCache.clear();
    
    // Clear DOM update queue
    domUpdateQueue.length = 0;
    isUpdatingDOM = false;
}

// Add cleanup on page unload
window.addEventListener('beforeunload', cleanup);

// Add cleanup on page visibility change
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Page is hidden, reduce update frequency
        if (updateInterval) {
            clearInterval(updateInterval);
            updateInterval = setInterval(updatePrices, 5000); // Slower updates when hidden
        }
    } else {
        // Page is visible, restore normal update frequency
        if (monitoringActive && updateInterval) {
            clearInterval(updateInterval);
            updateInterval = setInterval(updatePrices, 1500);
        }
    }
}); 