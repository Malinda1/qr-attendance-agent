// ===== QR ATTENDANCE AGENT - FRONTEND APPLICATION =====

// Configuration
const CONFIG = {
    API_BASE_URL: window.location.origin,
    ENDPOINTS: {
        CONVERT_EXPIRED: '/api/convert-expired-qr',
        CREATE_EVENING: '/api/create-evening-qr',
        HEALTH: '/health'
    }
};

// State Management
const state = {
    currentMode: 'expired',
    isProcessing: false,
    attendanceMarkingInProgress: false
};

// DOM Elements
const elements = {
    modeButtons: document.querySelectorAll('.mode-btn'),
    form: document.getElementById('qrForm'),
    moduleName: document.getElementById('moduleName'),
    qrLink: document.getElementById('qrLink'),
    username: document.getElementById('username'),
    password: document.getElementById('password'),
    qrLinkLabel: document.getElementById('qrLinkLabel'),
    submitBtn: document.getElementById('submitBtn'),
    statusMessages: document.getElementById('statusMessages'),
    resultsContainer: document.getElementById('resultsContainer'),
    loadingOverlay: document.getElementById('loadingOverlay'),
    loadingSubtext: document.getElementById('loadingSubtext'),
    qrDisplay: document.getElementById('qrDisplay'),
    qrLinkOutput: document.getElementById('qrLinkOutput'),
    screenshotDisplay: document.getElementById('screenshotDisplay'),
    downloadQR: document.getElementById('downloadQR'),
    downloadScreenshot: document.getElementById('downloadScreenshot'),
    copyBtn: document.getElementById('copyBtn')
};

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    attachEventListeners();
    checkHealth();
});

function initializeApp() {
    console.log('🚀 QR Attendance Agent initialized');
    updateModeUI();
}

// ===== EVENT LISTENERS =====
function attachEventListeners() {
    // Mode selection
    elements.modeButtons.forEach(btn => {
        btn.addEventListener('click', () => handleModeChange(btn.dataset.mode));
    });
    
    // Form submission
    elements.form.addEventListener('submit', handleFormSubmit);
    
    // Copy button
    elements.copyBtn.addEventListener('click', copyToClipboard);
    
    // Download buttons
    elements.downloadQR.addEventListener('click', () => downloadFile(elements.downloadQR.dataset.path));
    elements.downloadScreenshot.addEventListener('click', () => downloadFile(elements.downloadScreenshot.dataset.path));
}

// ===== MODE MANAGEMENT =====
function handleModeChange(mode) {
    if (state.isProcessing) return;
    
    state.currentMode = mode;
    
    elements.modeButtons.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === mode);
    });
    
    updateModeUI();
    clearResults();
}

function updateModeUI() {
    if (state.currentMode === 'expired') {
        elements.qrLinkLabel.textContent = 'Expired QR Code Link *';
        elements.qrLink.placeholder = 'https://students.nsbm.ac.lk/attendence/index.php?id=...';
        elements.submitBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"/>
            </svg>
            <span>Convert Expired QR</span>
        `;
    } else {
        elements.qrLinkLabel.textContent = 'Morning QR Code Link *';
        elements.qrLink.placeholder = 'https://students.nsbm.ac.lk/attendence/index.php?id=... (Morning session)';
        elements.submitBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
            </svg>
            <span>Create Evening QR</span>
        `;
    }
}

// ===== FORM HANDLING =====
async function handleFormSubmit(e) {
    e.preventDefault();
    
    if (state.isProcessing) return;
    
    // Validate inputs
    const formData = {
        module_name: elements.moduleName.value.trim(),
        qr_link: elements.qrLink.value.trim(),
        username: elements.username.value.trim() || null,
        password: elements.password.value.trim() || null
    };
    
    if (!formData.module_name || !formData.qr_link) {
        showStatus('Please fill in all required fields', 'error');
        return;
    }
    
    // Validate QR link format
    if (!formData.qr_link.includes('students.nsbm.ac.lk/attendence/')) {
        showStatus('Invalid NSBM QR code link format', 'error');
        return;
    }
    
    // Process based on mode
    if (state.currentMode === 'expired') {
        await processExpiredQR(formData);
    } else {
        await processEveningQR(formData);
    }
}

// ===== API CALLS =====
async function processExpiredQR(data) {
    showLoading('Converting expired QR code...');
    clearResults();
    
    try {
        showStatus('🔄 Converting QR code...', 'info');
        
        const response = await fetch(CONFIG.API_BASE_URL + CONFIG.ENDPOINTS.CONVERT_EXPIRED, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.detail || 'Conversion failed');
        }
        
        // Phase 1 Complete - QR Code ready!
        hideLoading();
        showStatus('✅ QR code converted successfully!', 'success');
        
        // Display results immediately
        displayResults(result);
        
        // Show info that attendance marking is in progress
        showStatus('🔄 Marking attendance in background...', 'info');
        state.attendanceMarkingInProgress = true;
        
        // Poll for screenshot after a delay (since it's being processed in background)
        setTimeout(() => pollForScreenshot(result.converted_qr), 5000);
        
    } catch (error) {
        hideLoading();
        showStatus(`❌ Error: ${error.message}`, 'error');
        console.error('Process error:', error);
    }
}

async function processEveningQR(data) {
    showLoading('Creating evening QR code...');
    clearResults();
    
    try {
        showStatus('🔄 Creating evening QR...', 'info');
        
        const requestData = {
            morning_qr_link: data.qr_link,
            module_name: data.module_name,
            username: data.username,
            password: data.password
        };
        
        const response = await fetch(CONFIG.API_BASE_URL + CONFIG.ENDPOINTS.CREATE_EVENING, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.detail || 'Evening QR creation failed');
        }
        
        // Phase 1 Complete - Evening QR ready!
        hideLoading();
        showStatus('✅ Evening QR code created successfully!', 'success');
        
        // Display results immediately
        displayResults(result);
        
        // Show info that attendance marking is in progress
        showStatus('🔄 Marking attendance in background...', 'info');
        state.attendanceMarkingInProgress = true;
        
        // Poll for screenshot after a delay
        setTimeout(() => pollForScreenshot(result.evening_qr || result.converted_qr), 5000);
        
    } catch (error) {
        hideLoading();
        showStatus(`❌ Error: ${error.message}`, 'error');
        console.error('Process error:', error);
    }
}

// ===== POLLING FOR BACKGROUND TASKS =====
async function pollForScreenshot(qrCode, attempts = 0) {
    const maxAttempts = 12; // Try for 1 minute (5 seconds * 12)
    
    if (attempts >= maxAttempts) {
        showStatus('⚠️ Attendance marking is taking longer than expected. Check records later.', 'warning');
        state.attendanceMarkingInProgress = false;
        return;
    }
    
    try {
        // Get today's records to check if screenshot is available
        const response = await fetch(CONFIG.API_BASE_URL + '/api/records/today');
        const data = await response.json();
        
        if (data.success && data.records && data.records.length > 0) {
            // Find the record with our QR code
            const record = data.records.find(r => 
                r.converted_qr_link === qrCode || 
                r.evening_qr_link === qrCode
            );
            
            if (record && record.status === 'success') {
                // Attendance marked successfully!
                showStatus('✅ Attendance marked successfully!', 'success');
                state.attendanceMarkingInProgress = false;
                
                // Try to update screenshot display
                updateScreenshotIfAvailable();
                return;
            }
        }
        
        // Continue polling
        setTimeout(() => pollForScreenshot(qrCode, attempts + 1), 5000);
        
    } catch (error) {
        console.error('Polling error:', error);
        // Continue polling despite error
        setTimeout(() => pollForScreenshot(qrCode, attempts + 1), 5000);
    }
}

async function updateScreenshotIfAvailable() {
    // This would need the screenshot filename from the background task
    // For now, we'll show a message that screenshot will be available in records
    showStatus('📸 Screenshot saved to records', 'info');
}

// ===== RESULTS DISPLAY =====
function displayResults(result) {
    elements.resultsContainer.classList.remove('hidden');
    
    // Display QR Code Link
    const qrLink = result.converted_qr || result.evening_qr || result.original_qr;
    elements.qrLinkOutput.value = qrLink;
    
    // Display QR Code Image
    if (result.qr_image_path) {
        const qrImageUrl = CONFIG.API_BASE_URL + result.qr_image_path;
        elements.qrDisplay.innerHTML = `<img src="${qrImageUrl}" alt="QR Code">`;
        elements.downloadQR.style.display = 'flex';
        elements.downloadQR.dataset.path = result.qr_image_path;
    }
    
    // Screenshot section - show placeholder with message
    elements.screenshotDisplay.innerHTML = `
        <div class="screenshot-placeholder">
            <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 6v6l4 2"/>
            </svg>
            <p>Marking attendance...</p>
            <p style="font-size: 0.8rem; color: var(--text-muted);">Screenshot will appear here</p>
        </div>
    `;
    
    // Show summary
    const summary = state.currentMode === 'expired' 
        ? `Original: ${result.original_qr}\nConverted: ${result.converted_qr}`
        : `Morning: ${result.original_qr}\nEvening: ${result.evening_qr}`;
    
    console.log('Phase 1 complete - QR Ready:', summary);
}

function clearResults() {
    elements.resultsContainer.classList.add('hidden');
    elements.qrLinkOutput.value = '';
    elements.qrDisplay.innerHTML = `
        <div class="qr-placeholder">
            <svg width="100" height="100" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                <rect x="3" y="3" width="7" height="7"/>
                <rect x="14" y="3" width="7" height="7"/>
                <rect x="3" y="14" width="7" height="7"/>
                <rect x="14" y="14" width="7" height="7"/>
            </svg>
            <p>QR Code will appear here</p>
        </div>
    `;
    elements.screenshotDisplay.innerHTML = `
        <div class="screenshot-placeholder">
            <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                <rect x="3" y="3" width="18" height="18" rx="2"/>
                <circle cx="8.5" cy="8.5" r="1.5"/>
                <path d="M21 15l-5-5L5 21"/>
            </svg>
            <p>Screenshot will appear here</p>
        </div>
    `;
    elements.downloadQR.style.display = 'none';
    elements.downloadScreenshot.style.display = 'none';
}

// ===== STATUS MESSAGES =====
function showStatus(message, type = 'info') {
    const statusDiv = document.createElement('div');
    statusDiv.className = `status-message ${type}`;
    statusDiv.textContent = message;
    
    elements.statusMessages.appendChild(statusDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        statusDiv.style.opacity = '0';
        setTimeout(() => statusDiv.remove(), 300);
    }, 5000);
    
    // Keep only last 5 messages
    const messages = elements.statusMessages.children;
    while (messages.length > 5) {
        messages[0].remove();
    }
}

// ===== LOADING OVERLAY =====
function showLoading(text) {
    state.isProcessing = true;
    elements.loadingOverlay.classList.remove('hidden');
    elements.loadingSubtext.textContent = text;
    elements.submitBtn.disabled = true;
}

function hideLoading() {
    state.isProcessing = false;
    elements.loadingOverlay.classList.add('hidden');
    elements.submitBtn.disabled = false;
}

function updateLoadingText(text) {
    elements.loadingSubtext.textContent = text;
}

// ===== UTILITIES =====
async function copyToClipboard() {
    const text = elements.qrLinkOutput.value;
    
    try {
        await navigator.clipboard.writeText(text);
        showStatus('✅ Link copied to clipboard!', 'success');
        
        // Visual feedback
        elements.copyBtn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"/>
            </svg>
        `;
        
        setTimeout(() => {
            elements.copyBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                </svg>
            `;
        }, 2000);
    } catch (error) {
        showStatus('❌ Failed to copy to clipboard', 'error');
    }
}

function downloadFile(path) {
    const link = document.createElement('a');
    link.href = CONFIG.API_BASE_URL + path;
    link.download = path.split('/').pop();
    link.click();
}

async function checkHealth() {
    try {
        const response = await fetch(CONFIG.API_BASE_URL + CONFIG.ENDPOINTS.HEALTH);
        const data = await response.json();
        console.log('Health check:', data);
    } catch (error) {
        console.error('Health check failed:', error);
    }
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ===== EXPORT FOR TESTING =====
window.QRAttendanceApp = {
    state,
    CONFIG,
    processExpiredQR,
    processEveningQR
};