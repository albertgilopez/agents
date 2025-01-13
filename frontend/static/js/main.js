// Constants
const MESSAGE_TYPES = {
    success: 'message-success',
    error: 'message-error',
    info: 'message-info',
    system: 'message-system'
};

// Helper functions
function createMessageElement(message, type = 'info') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `${MESSAGE_TYPES[type]} fade-in`;
    
    if (message.includes('[Download')) {
        // Handle download links
        if (message.includes('PDF')) {
            const pdfPath = message.match(/\((.*?)\)/)[1];
            messageDiv.innerHTML = `
                <a href="${pdfPath}" target="_blank" class="download-link">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Download PDF Report
                </a>`;
        } else if (message.includes('Markdown')) {
            const mdPath = message.match(/\((.*?)\)/)[1];
            messageDiv.innerHTML = `
                <a href="${mdPath}" target="_blank" class="download-link">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Download Markdown Report
                </a>`;
        }
    } else {
        // Check if it's a system message (from index.html)
        if (message.includes('Retrieved') || message.includes('Analyzing') || message.includes('Processing')) {
            messageDiv.className = `${MESSAGE_TYPES.system} fade-in`;
            messageDiv.innerHTML = `<span>${message}</span>`;
        } else {
            // Handle status messages with icons
            let icon = '';
            if (message.includes('✅') || message.includes('✓') || message.includes('Completed')) {
                icon = '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>';
                type = 'success';
            } else if (message.includes('⚠️') || message.includes('❌')) {
                icon = '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>';
                type = 'error';
            } else if (message.includes('Connected')) {
                icon = '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>';
            }
            messageDiv.className = `${MESSAGE_TYPES[type]} fade-in`;
            messageDiv.innerHTML = icon ? `${icon}<span>${message}</span>` : `<span>${message}</span>`;
        }
    }
    
    return messageDiv;
}

function updateProgressSpinner(show) {
    const progress = document.getElementById('progress');
    const spinner = progress.querySelector('.spinner-container');
    
    if (show) {
        progress.classList.remove('hidden');
        if (!spinner) {
            const spinnerContainer = document.createElement('div');
            spinnerContainer.className = 'spinner-container flex items-center gap-3 mb-4 fade-in';
            spinnerContainer.innerHTML = `
                <div class="spinner"></div>
                <p class="text-gray-600">Research in progress...</p>
            `;
            progress.insertBefore(spinnerContainer, progress.firstChild);
        }
    } else if (spinner) {
        spinner.remove();
    }
}

// WebSocket connection handler
function connectWebSocket(formData) {
    const ws = new WebSocket(`ws://${window.location.host}/ws`);
    const messages = document.getElementById('messages');
    
    ws.onopen = () => {
        console.log('WebSocket connection opened');
        const message = createMessageElement('✓ Connected to research service', 'success');
        messages.appendChild(message);
        console.log('Sending data:', formData);
        ws.send(JSON.stringify(formData));
    };
    
    ws.onmessage = (event) => {
        console.log('Received message:', event.data);
        const message = event.data;
        
        try {
            if (message.includes('```markdown')) {
                // Handle markdown content
                const parts = message.split('```markdown');
                const header = parts[0].trim();
                const report = parts[1].split('```')[0];
                
                if (!header.includes('Report Generated Successfully')) {
                    const headerDiv = createMessageElement(header, 'info');
                    messages.appendChild(headerDiv);
                }
                
                // Add report content with fade-in animation
                const reportDiv = document.createElement('div');
                reportDiv.className = 'mt-4 p-4 bg-white rounded-lg shadow-sm markdown-content fade-in';
                reportDiv.innerHTML = marked.parse(report);
                messages.appendChild(reportDiv);
                
                // Extract and add download links
                const linkMatch = header.match(/\[(Download .*? Report)\]\((.*?)\)/);
                if (linkMatch) {
                    const [, linkText, path] = linkMatch;
                    const type = linkText.includes('PDF') ? 'PDF' : 'Markdown';
                    const encodedPath = encodeURIComponent(path);
                    const downloadMessage = createMessageElement(`[Download ${type} Report](${encodedPath})`, 'success');
                    messages.appendChild(downloadMessage);
                }
            } else {
                // Handle status messages
                let type = 'info';
                if (message.includes('✅') || message.includes('✓')) type = 'success';
                if (message.includes('⚠️') || message.includes('❌')) type = 'error';
                
                if (!message.includes('Generated research report') && !message.includes('Report Generated Successfully')) {
                    const messageDiv = createMessageElement(message, type);
                    messages.appendChild(messageDiv);
                }
            }
            
            // Scroll to bottom
            messages.scrollTop = messages.scrollHeight;
        } catch (error) {
            console.error('Error processing message:', error);
            const errorDiv = createMessageElement(message, 'error');
            messages.appendChild(errorDiv);
        }
    };
    
    ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        updateProgressSpinner(false);
        
        const message = event.code === 1000 
            ? 'Research completed'
            : 'Connection closed';
        const messageDiv = createMessageElement(message, event.code === 1000 ? 'success' : 'info');
        messages.appendChild(messageDiv);
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateProgressSpinner(false);
        
        const messageDiv = createMessageElement('⚠️ Error: Connection failed', 'error');
        messages.appendChild(messageDiv);
    };
    
    return ws;
}

// Initialize form handling
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('researchForm');
    let ws = null;
    
    // Add input animations
    const inputs = form.querySelectorAll('input');
    inputs.forEach(input => {
        input.classList.add('form-input');
        
        // Add floating label animation
        const label = input.previousElementSibling;
        if (label && label.tagName === 'LABEL') {
            label.classList.add('transform', 'transition-all', 'duration-200');
            
            input.addEventListener('focus', () => {
                label.classList.add('text-primary-color');
            });
            
            input.addEventListener('blur', () => {
                label.classList.remove('text-primary-color');
            });
        }
    });
    
    // Style submit button
    const submitButton = form.querySelector('button[type="submit"]');
    submitButton.classList.add('submit-button');
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Reset previous research
        if (ws) {
            ws.close();
        }
        const messages = document.getElementById('messages');
        messages.innerHTML = '';
        
        // Show progress spinner
        updateProgressSpinner(true);
        
        // Get form data
        const formData = {
            companyName: document.getElementById('companyName').value,
            companyUrl: document.getElementById('companyUrl')?.value || null,
            outputFormat: 'pdf'
        };
        
        // Connect WebSocket
        ws = connectWebSocket(formData);
    });
}); 