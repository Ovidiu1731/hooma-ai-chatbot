/**
 * Hooma AI Chatbot Widget
 * Embeddable chatbot widget for Hooma business website
 */

(function() {
    'use strict';

    // Prevent multiple initialization
    if (window.HoomaChatbot) {
        return;
    }

    class HoomaChatbot {
        constructor() {
            this.isOpen = false;
            this.sessionId = null;
            this.apiEndpoint = '';
            this.config = {
                primaryColor: '#ff5da2',
                secondaryColor: '#e91e63',
                position: 'bottom-right',
                welcomeMessage: "Hi! I'm Hooma's AI assistant. I can help you learn about our AI business solutions and growth systems. What would you like to know?",
                placeholder: 'Ask about AI solutions...',
                title: 'Hooma AI Assistant',
                subtitle: 'AI Business Solutions',
                poweredBy: true
            };
            this.isTyping = false;
            this.messageQueue = [];
            this.isInitialized = false;
        }

        init(options = {}) {
            console.log('HoomaChatbot.init called with options:', options);
            
            if (this.isInitialized) {
                console.warn('Hooma Chatbot already initialized');
                return;
            }

            // Merge configuration
            this.config = { ...this.config, ...options };
            this.apiEndpoint = options.apiEndpoint || '';

            console.log('Final config:', this.config);
            console.log('API Endpoint:', this.apiEndpoint);

            if (!this.apiEndpoint) {
                console.error('Hooma Chatbot: apiEndpoint is required');
                return;
            }

            // Wait for DOM to be ready
            if (document.readyState === 'loading') {
                console.log('DOM still loading, waiting...');
                document.addEventListener('DOMContentLoaded', () => this.createWidget());
            } else {
                console.log('DOM ready, creating widget...');
                this.createWidget();
            }

            this.isInitialized = true;
        }

        createWidget() {
            console.log('Creating widget...');
            
            // Create chat bubble
            this.createChatBubble();
            console.log('Chat bubble created');
            
            // Create chat window
            this.createChatWindow();
            console.log('Chat window created');
            
            // Add event listeners
            this.addEventListeners();
            console.log('Event listeners added');
            
            // Apply custom styles
            this.applyCustomStyles();
            console.log('Custom styles applied');
            
            console.log('Widget creation complete!');
        }

        createChatBubble() {
            const bubble = document.createElement('button');
            bubble.className = `hooma-chat-bubble ${this.config.position}`;
            bubble.setAttribute('aria-label', 'Open chat with Hooma AI Assistant');
            bubble.innerHTML = `
                <svg class="hooma-bubble-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2C6.48 2 2 6.48 2 12c0 1.54.36 3.04 1.05 4.36L2 22l5.64-1.05C9.96 21.64 11.46 22 13 22c5.52 0 10-4.48 10-10S17.52 2 12 2zm0 18c-1.4 0-2.76-.35-4-.99L7 19l.99-1c-.64-1.24-.99-2.6-.99-4 0-4.41 3.59-8 8-8s8 3.59 8 8-3.59 8-8 8z"/>
                    <circle cx="9" cy="12" r="1"/>
                    <circle cx="15" cy="12" r="1"/>
                    <circle cx="12" cy="12" r="1"/>
                </svg>
            `;
            
            this.bubble = bubble;
            document.body.appendChild(bubble);
        }

        createChatWindow() {
            const window = document.createElement('div');
            window.className = `hooma-chatbot hooma-chat-window ${this.config.position}`;
            window.innerHTML = `
                <div class="hooma-chat-header">
                    <div class="hooma-header-content">
                        <div class="hooma-avatar">H</div>
                        <div class="hooma-header-text">
                            <h3>${this.config.title}</h3>
                            <p>${this.config.subtitle}</p>
                        </div>
                    </div>
                    <button class="hooma-close-btn" aria-label="Close chat">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                            <path d="M12.854 3.146a.5.5 0 0 1 0 .708L8.707 8l4.147 4.146a.5.5 0 0 1-.708.708L8 8.707l-4.146 4.147a.5.5 0 0 1-.708-.708L7.293 8 3.146 3.854a.5.5 0 1 1 .708-.708L8 7.293l4.146-4.147a.5.5 0 0 1 .708 0z"/>
                        </svg>
                    </button>
                </div>
                <div class="hooma-chat-messages" id="hooma-messages">
                    <div class="hooma-message assistant welcome">
                        <div class="hooma-message-avatar">H</div>
                        <div class="hooma-message-content">${this.config.welcomeMessage}</div>
                    </div>
                </div>
                <div class="hooma-chat-input">
                    <div class="hooma-input-container">
                        <div class="hooma-input-wrapper">
                            <textarea 
                                class="hooma-input-field" 
                                placeholder="${this.config.placeholder}"
                                rows="1"
                                maxlength="2000"
                                aria-label="Type your message"
                            ></textarea>
                        </div>
                        <button class="hooma-send-btn" aria-label="Send message">
                            <svg class="hooma-send-icon" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                            </svg>
                        </button>
                    </div>
                </div>
                ${this.config.poweredBy ? `
                <div class="hooma-powered-by">
                    Powered by <a href="https://hooma.io" target="_blank" rel="noopener">Hooma AI</a>
                </div>
                ` : ''}
            `;
            
            this.window = window;
            this.messagesContainer = window.querySelector('#hooma-messages');
            this.inputField = window.querySelector('.hooma-input-field');
            this.sendButton = window.querySelector('.hooma-send-btn');
            this.closeButton = window.querySelector('.hooma-close-btn');
            
            document.body.appendChild(window);
        }

        addEventListeners() {
            // Bubble click
            this.bubble.addEventListener('click', () => this.toggleChat());
            
            // Close button
            this.closeButton.addEventListener('click', () => this.closeChat());
            
            // Send button
            this.sendButton.addEventListener('click', () => this.sendMessage());
            
            // Enter key handling
            this.inputField.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                } else if (e.key === 'Enter' && e.shiftKey) {
                    // Allow line break
                }
            });
            
            // Auto-resize textarea
            this.inputField.addEventListener('input', () => this.autoResizeTextarea());
            
            // Escape key to close
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.isOpen) {
                    this.closeChat();
                }
            });
            
            // Click outside to close (optional)
            document.addEventListener('click', (e) => {
                if (this.isOpen && !this.window.contains(e.target) && !this.bubble.contains(e.target)) {
                    // Optionally close on outside click
                    // this.closeChat();
                }
            });
        }

        applyCustomStyles() {
            const style = document.createElement('style');
            style.textContent = `
                .hooma-chat-bubble {
                    background: linear-gradient(135deg, ${this.config.primaryColor} 0%, ${this.config.secondaryColor} 100%) !important;
                }
                .hooma-chat-header {
                    background: linear-gradient(135deg, ${this.config.primaryColor} 0%, ${this.config.secondaryColor} 100%) !important;
                }
                .hooma-message.user .hooma-message-content {
                    background: ${this.config.primaryColor} !important;
                }
                .hooma-message.assistant .hooma-message-avatar {
                    background: linear-gradient(135deg, ${this.config.primaryColor} 0%, ${this.config.secondaryColor} 100%) !important;
                }
                .hooma-send-btn {
                    background: ${this.config.primaryColor} !important;
                }
                .hooma-send-btn:hover:not(:disabled) {
                    background: ${this.config.secondaryColor} !important;
                }
                .hooma-input-field:focus {
                    border-color: ${this.config.primaryColor} !important;
                    box-shadow: 0 0 0 3px ${this.config.primaryColor}20 !important;
                }
            `;
            document.head.appendChild(style);
        }

        toggleChat() {
            if (this.isOpen) {
                this.closeChat();
            } else {
                this.openChat();
            }
        }

        openChat() {
            this.isOpen = true;
            this.bubble.classList.add('open');
            this.window.classList.add('show');
            
            // Hide the bubble when window is open for cleaner look
            this.bubble.style.display = 'none';
            
            this.inputField.focus();
            
            // Scroll to bottom
            this.scrollToBottom();
            
            // Track opening event
            this.trackEvent('chat_opened');
        }

        closeChat() {
            this.isOpen = false;
            this.bubble.classList.remove('open');
            this.window.classList.remove('show');
            
            // Show the bubble again when window is closed
            this.bubble.style.display = 'flex';
            
            // Track closing event
            this.trackEvent('chat_closed');
        }

        async sendMessage() {
            const message = this.inputField.value.trim();
            if (!message || this.isTyping) return;

            // Add user message to UI
            this.addMessage('user', message);
            
            // Clear input
            this.inputField.value = '';
            this.autoResizeTextarea();
            
            // Disable input while processing
            this.setInputState(false);
            
            // Show typing indicator
            this.showTypingIndicator();
            
            try {
                const response = await this.callAPI(message);
                
                // Remove typing indicator
                this.hideTypingIndicator();
                
                // Add assistant response
                this.addMessage('assistant', response.response);
                
                // Update session ID
                this.sessionId = response.session_id;
                
                // Track message sent
                this.trackEvent('message_sent', { message_length: message.length });
                
            } catch (error) {
                console.error('Hooma Chatbot Error:', error);
                
                // Remove typing indicator
                this.hideTypingIndicator();
                
                // Show error message
                this.addMessage('assistant', 
                    "I apologize, but I'm experiencing technical difficulties. Please try again in a moment, or feel free to contact our team directly for immediate assistance."
                );
                
                // Track error
                this.trackEvent('message_error', { error: error.message });
            }
            
            // Re-enable input
            this.setInputState(true);
        }

        async callAPI(message) {
            const response = await fetch(`${this.apiEndpoint}/api/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId,
                    user_info: this.getUserInfo()
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        }

        addMessage(role, content) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `hooma-message ${role}`;
            
            const avatar = role === 'user' ? 'U' : 'H';
            const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            
            messageDiv.innerHTML = `
                <div class="hooma-message-avatar">${avatar}</div>
                <div class="hooma-message-content">${this.escapeHtml(content)}</div>
            `;
            
            this.messagesContainer.appendChild(messageDiv);
            this.scrollToBottom();
        }

        showTypingIndicator() {
            if (this.isTyping) return;
            
            this.isTyping = true;
            const typingDiv = document.createElement('div');
            typingDiv.className = 'hooma-message assistant';
            typingDiv.id = 'hooma-typing';
            typingDiv.innerHTML = `
                <div class="hooma-message-avatar">H</div>
                <div class="hooma-typing-indicator">
                    <div class="hooma-typing-dots">
                        <div class="hooma-typing-dot"></div>
                        <div class="hooma-typing-dot"></div>
                        <div class="hooma-typing-dot"></div>
                    </div>
                </div>
            `;
            
            this.messagesContainer.appendChild(typingDiv);
            this.scrollToBottom();
        }

        hideTypingIndicator() {
            this.isTyping = false;
            const typingIndicator = document.getElementById('hooma-typing');
            if (typingIndicator) {
                typingIndicator.remove();
            }
        }

        setInputState(enabled) {
            this.inputField.disabled = !enabled;
            this.sendButton.disabled = !enabled;
            
            if (enabled) {
                this.inputField.focus();
            }
        }

        autoResizeTextarea() {
            this.inputField.style.height = 'auto';
            this.inputField.style.height = Math.min(this.inputField.scrollHeight, 120) + 'px';
        }

        scrollToBottom() {
            setTimeout(() => {
                this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
            }, 100);
        }

        escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML.replace(/\n/g, '<br>');
        }

        getUserInfo() {
            return {
                url: window.location.href,
                referrer: document.referrer,
                timestamp: new Date().toISOString(),
                screen_resolution: `${screen.width}x${screen.height}`,
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
            };
        }

        trackEvent(eventName, data = {}) {
            // Basic event tracking - can be extended with analytics services
            if (window.gtag) {
                window.gtag('event', eventName, {
                    event_category: 'hooma_chatbot',
                    ...data
                });
            }
            
            // Custom event for other tracking systems
            window.dispatchEvent(new CustomEvent('hooma_chatbot_event', {
                detail: { eventName, data }
            }));
        }

        // Public API methods
        show() {
            this.openChat();
        }

        hide() {
            this.closeChat();
        }

        sendCustomMessage(message) {
            if (typeof message === 'string' && message.trim()) {
                this.inputField.value = message;
                this.sendMessage();
            }
        }

        updateConfig(newConfig) {
            this.config = { ...this.config, ...newConfig };
            this.applyCustomStyles();
        }
    }

    // Create global instance
    window.HoomaChatbot = new HoomaChatbot();

    // Auto-initialize if data attributes are present
    const script = document.currentScript;
    if (script && script.hasAttribute('data-api-endpoint')) {
        const config = {};
        
        // Read configuration from data attributes
        if (script.hasAttribute('data-api-endpoint')) {
            config.apiEndpoint = script.getAttribute('data-api-endpoint');
        }
        if (script.hasAttribute('data-primary-color')) {
            config.primaryColor = script.getAttribute('data-primary-color');
        }
        if (script.hasAttribute('data-position')) {
            config.position = script.getAttribute('data-position');
        }
        
        // Auto-initialize
        window.HoomaChatbot.init(config);
    }

})();
