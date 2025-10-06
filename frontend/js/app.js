// ===== QR ATTENDANCE AGENT - FRONTEND APPLICATION =====

const CONFIG = {
    API_BASE_URL: window.location.origin,
    ENDPOINTS: {
        CONVERT_EXPIRED: '/api/convert-expired-qr',
        CREATE_EVENING: '/api/create-evening-qr',
        MARK_ATTENDANCE: '/api/mark-attendance',
        HEALTH: '/health'
    }
};

const state = {
    currentMode: 'expired',
    isProcessing: false,
    currentQRData: null,
    credentials: { username: null, password: null }
};

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

document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    attachEventListeners();
    checkHealth();
});

function initializeApp() {
    console.log('🚀 QR Attendance Agent initialized');
    updateModeUI();
}

function attachEventListeners() {
    elements.modeButtons.forEach(btn => {
        btn.addEventListener('click', () => handleModeChange(btn.dataset.mode));
    });
    
    elements.form.addEventListener('submit', handleFormSubmit);
    elements.copyBtn.addEventListener('click', copyToClipboard);
    elements.downloadQR.addEventListener('click', () => downloadFile(elements.downloadQR.dataset.path));
    elements.downloadScreenshot.addEventListener('click', () => downloadFile(elements.downloadScreenshot.dataset.path));
}

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

async function handleFormSubmit(e) {
    e.preventDefault();
    
    if (state.isProcessing) return;
    
    const formData = {
        module_name: elements.moduleName.value.trim(),
        qr_link: elements.qrLink.value.trim(),
        username: elements.username.value.trim(),
        password: elements.password.value.trim(),
        auto_mark_attendance: false
    };
    
    // Validation
    if (!formData.module_name || !formData.qr_link) {
        showStatus('Please fill in all required fields', 'error');
        return;
    }
    
    // NEW: Validate credentials
    if (!formData.username || !formData.password) {
        showStatus('Username and password are required', 'error');
        return;
    }
    
    if (!formData.qr_link.includes('students.nsbm.ac.lk/attendence/')) {
        showStatus('Invalid NSBM QR code link format', 'error');
        return;
    }
    
    // Store credentials for later use
    state.credentials = {
        username: formData.username,
        password: formData.password
    };
    
    
    if (state.currentMode === 'expired') {
        await processExpiredQR(formData);
    } else {
        await processEveningQR(formData);
    }
}

async function processExpiredQR(data) {
    showLoading('Converting expired QR code...');
    clearResults();
    
    try {
        showStatus('Converting QR code...', 'info');
        
        const response = await fetch(CONFIG.API_BASE_URL + CONFIG.ENDPOINTS.CONVERT_EXPIRED, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.detail || 'Conversion failed');
        }
        
        hideLoading();
        showStatus('QR code converted successfully!', 'success');
        
        state.currentQRData = {
            converted_qr: result.converted_qr,
            original_qr: result.original_qr,
            module_name: data.module_name,
            is_evening: false
        };
        
        displayResults(result);
        
    } catch (error) {
        hideLoading();
        showStatus(`Error: ${error.message}`, 'error');
        console.error('Process error:', error);
    }
}

async function processEveningQR(data) {
    showLoading('Creating evening QR code...');
    clearResults();
    
    try {
        showStatus('Creating evening QR...', 'info');
        
        const requestData = {
            morning_qr_link: data.qr_link,
            module_name: data.module_name,
            username: data.username,
            password: data.password,
            auto_mark_attendance: false
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
        
        hideLoading();
        showStatus('Evening QR code created successfully!', 'success');
        
        state.currentQRData = {
            converted_qr: result.evening_qr,
            original_qr: result.original_qr,
            module_name: data.module_name,
            is_evening: true
        };
        
        displayResults(result);
        
    } catch (error) {
        hideLoading();
        showStatus(`Error: ${error.message}`, 'error');
        console.error('Process error:', error);
    }
}

async function markAttendanceManually() {
    if (!state.currentQRData) {
        showStatus('No QR code data available', 'error');
        return;
    }
    
    showLoading('Marking attendance...');
    
    try {
        showStatus('Marking attendance...', 'info');
        
        const requestData = {
            qr_link: state.currentQRData.converted_qr,
            module_name: state.currentQRData.module_name,
            original_qr: state.currentQRData.original_qr,
            username: state.credentials.username,
            password: state.credentials.password,
            is_evening: state.currentQRData.is_evening
        };
        
        const response = await fetch(CONFIG.API_BASE_URL + CONFIG.ENDPOINTS.MARK_ATTENDANCE, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.detail || 'Attendance marking failed');
        }
        
        hideLoading();
        showStatus('Attendance marked successfully!', 'success');
        
        if (result.screenshot_path && result.screenshot_filename) {
            displayScreenshot(result.screenshot_path, result.screenshot_filename);
        }
        
        document.getElementById('markAttendanceBtn').disabled = true;
        document.getElementById('markAttendanceBtn').textContent = 'Attendance Marked ✓';
        
    } catch (error) {
        hideLoading();
        showStatus(`Error: ${error.message}`, 'error');
        console.error('Attendance marking error:', error);
    }
}

function displayResults(result) {
    elements.resultsContainer.classList.remove('hidden');
    
    const qrLink = result.converted_qr || result.evening_qr || result.original_qr;
    elements.qrLinkOutput.value = qrLink;
    
    if (result.qr_image_path) {
        const qrImageUrl = CONFIG.API_BASE_URL + result.qr_image_path;
        elements.qrDisplay.innerHTML = `<img src="${qrImageUrl}" alt="QR Code">`;
        elements.downloadQR.style.display = 'flex';
        elements.downloadQR.dataset.path = result.qr_image_path;
    }
    
    elements.screenshotDisplay.innerHTML = `
        <div class="screenshot-placeholder">
            <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                <rect x="3" y="3" width="18" height="18" rx="2"/>
                <circle cx="8.5" cy="8.5" r="1.5"/>
                <path d="M21 15l-5-5L5 21"/>
            </svg>
            <p>Click "Mark Attendance" to capture screenshot</p>
        </div>
        <button class="download-btn" id="markAttendanceBtn" style="margin-top: 1rem;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
            Mark Attendance
        </button>
    `;
    
    document.getElementById('markAttendanceBtn').addEventListener('click', markAttendanceManually);
}

function displayScreenshot(screenshotPath, filename) {
    const screenshotUrl = CONFIG.API_BASE_URL + screenshotPath;
    
    elements.screenshotDisplay.innerHTML = `
        <img src="${screenshotUrl}" alt="Confirmation Screenshot" style="max-width: 100%; border-radius: 8px;">
    `;
    
    elements.downloadScreenshot.style.display = 'flex';
    elements.downloadScreenshot.dataset.path = screenshotPath;
    
    showStatus('Screenshot captured successfully!', 'success');
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
    state.currentQRData = null;
}

function showStatus(message, type = 'info') {
    const statusDiv = document.createElement('div');
    statusDiv.className = `status-message ${type}`;
    statusDiv.textContent = message;
    
    elements.statusMessages.appendChild(statusDiv);
    
    setTimeout(() => {
        statusDiv.style.opacity = '0';
        setTimeout(() => statusDiv.remove(), 300);
    }, 5000);
    
    const messages = elements.statusMessages.children;
    while (messages.length > 5) {
        messages[0].remove();
    }
}

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

async function copyToClipboard() {
    const text = elements.qrLinkOutput.value;
    
    try {
        await navigator.clipboard.writeText(text);
        showStatus('Link copied to clipboard!', 'success');
        
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
        showStatus('Failed to copy to clipboard', 'error');
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

window.QRAttendanceApp = {
    state,
    CONFIG,
    processExpiredQR,
    processEveningQR,
    markAttendanceManually
};