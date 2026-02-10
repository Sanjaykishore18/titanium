// ============================================================================
// game-engine.js - FIXED VERSION WITH FINAL PAGE DASHBOARD REDIRECT
// Save as: frontend/assets/js/game-engine.js
// ============================================================================

console.log('🔧 game-engine.js loading...');

class GameEngine {
    constructor() {
        console.log('🔧 GameEngine constructor called');
        this.session = CONFIG.getSession();
        this.timer = null;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }

    async init() {
        console.log('🔧 GameEngine init called');
        this.extractURLParams();
        this.validateToken();
        await this.loadGameState();
        this.connectWebSocket();
    }

    connectWebSocket() {
        const session = this.session;
        
        if (!session?.teamId || !session?.roundNumber) {
            console.error('Cannot connect WebSocket: Missing team or round info');
            return;
        }

        const wsUrl = CONFIG.WEBSOCKET.getUrl(session.teamId, session.roundNumber);
        console.log('Connecting to WebSocket:', wsUrl);

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('✅ WebSocket connected');
            this.reconnectAttempts = 0;
            this.showNotification('Connected to team sync', 'success');
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                console.log(`Reconnecting WebSocket... (Attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                
                setTimeout(() => {
                    this.connectWebSocket();
                }, 3000);
            } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                console.log('Max reconnection attempts reached');
                this.showNotification('Team sync offline. Your progress is still saved.', 'info');
            }
        };
    }

    handleWebSocketMessage(data) {
        console.log('📨 WebSocket message received:', data);

        switch (data.type) {
            case 'game_state':
                this.updateGameState(data.data);
                break;
            
            case 'page_changed':
                // ✅ Handle explicit page navigation from teammates
                this.handlePageChange(data);
                break;
            
            case 'token_update':
                this.handleTokenUpdate(data);
                break;
            
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    // ✅ FIXED: Force navigation for teammates
    handlePageChange(data) {
        const { next_page, new_token } = data;

        console.log('📨 Received page_changed:', { 
            next_page, 
            new_token, 
            myCurrentPage: this.session.pageNumber,
            myCurrentToken: this.session.token
        });

        // Safety: If I'm already on that page or ahead, ignore
        if (this.session.pageNumber >= next_page) {
            console.log('✋ Already on page', this.session.pageNumber, '- ignoring navigation to', next_page);
            return;
        }

        console.log('➡️ Team page sync → moving to page', next_page);

        // Update session BEFORE navigation
        this.session.pageNumber = next_page;
        this.session.token = new_token;

        CONFIG.setSession({
            pageNumber: next_page,
            token: new_token
        });

        // Build the URL with proper path
        const currentPath = window.location.pathname;
        const isInRoundFolder = currentPath.includes('/round');
        
        let url;
        if (isInRoundFolder) {
            // Already in /round1/ directory, use relative path
            url = `page${next_page}.html`
                + `?team=${this.session.teamId}`
                + `&round=${this.session.roundNumber}`
                + `&page=${next_page}`
                + `&token=${new_token}`;
        } else {
            // Need full path from root
            url = `/round${this.session.roundNumber}/page${next_page}.html`
                + `?team=${this.session.teamId}`
                + `&round=${this.session.roundNumber}`
                + `&page=${next_page}`
                + `&token=${new_token}`;
        }

        console.log('🔄 Navigating teammate to:', url);
        
        // Show notification before navigation
        this.showNotification(`Teammate completed page! Moving to page ${next_page}...`, 'success');
        
        // Force immediate navigation after brief delay for notification
        setTimeout(() => {
            window.location.href = url;
        }, 500);
    }

    handleTokenUpdate(data) {
        const { new_token } = data;
        
        console.log('🔑 Token update received:', new_token);
        
        // Update token in session and localStorage
        this.session.token = new_token;
        localStorage.setItem('game_token', new_token);
        CONFIG.setSession({ token: new_token });
        
        this.showNotification('Token synced with team', 'info');
    }

    updateGameState(state) {
        console.log('Updating game state:', state);

        // ✅ CHECK IF USER IS BEHIND THE TEAM'S CURRENT PAGE
        if (state.current_page && state.current_page > this.session.pageNumber) {
            console.log('⚠️ Team is ahead! Current team page:', state.current_page, '| My page:', this.session.pageNumber);
            
            // Update session with new page and token
            this.session.pageNumber = state.current_page;
            
            if (state.current_token) {
                this.session.token = state.current_token;
            }
            
            CONFIG.setSession({
                pageNumber: state.current_page,
                token: state.current_token || this.session.token
            });
            
            // Build URL to catch up
            const currentPath = window.location.pathname;
            const isInRoundFolder = currentPath.includes('/round');
            
            let url;
            if (isInRoundFolder) {
                url = `page${state.current_page}.html`
                    + `?team=${this.session.teamId}`
                    + `&round=${this.session.roundNumber}`
                    + `&page=${state.current_page}`
                    + `&token=${state.current_token || this.session.token}`;
            } else {
                url = `/round${this.session.roundNumber}/page${state.current_page}.html`
                    + `?team=${this.session.teamId}`
                    + `&round=${this.session.roundNumber}`
                    + `&page=${state.current_page}`
                    + `&token=${state.current_token || this.session.token}`;
            }
            
            console.log('🚀 Catching up to team! Redirecting to:', url);
            
            // Show notification and redirect
            this.showNotification(`Catching up to team (Page ${state.current_page})...`, 'info');
            
            setTimeout(() => {
                window.location.href = url;
            }, 1000);
            
            return; // Don't update UI since we're redirecting
        }

        // Update score display
        const scoreEl = document.getElementById('current-score');
        if (scoreEl && state.score !== undefined) {
            scoreEl.textContent = state.score;
        }
    }

    async moveToNextPage(bugsFixed = []) {
        console.log('🔧 moveToNextPage called with bugs:', bugsFixed);
        try {
            // ✅ CHECK IF CURRENT PAGE IS A FINAL PAGE (10, 20, or 30)
            const currentPage = this.session.pageNumber;
            const isFinalPage = currentPage === 10 || currentPage === 20 || currentPage === 30;
            
            if (isFinalPage) {
                console.log(`🏁 Final page ${currentPage} detected! Will redirect to dashboard after validation.`);
            }
            
            const nextPage = this.session.pageNumber + 1;
            
            // Safety check for maximum pages
            if (nextPage > 30) {
                alert('All rounds completed! Returning to dashboard...');
                window.location.href = CONFIG.BACKEND_URL + '/dashboard/';
                return;
            }

            // Get new token from backend and validate page
            const response = await fetch(
                CONFIG.BACKEND_URL + CONFIG.API.VALIDATE_PAGE,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    credentials: 'include',
                    body: JSON.stringify({
                        team_id: this.session.teamId,
                        token: this.session.token,
                        round_number: this.session.roundNumber,
                        page_number: this.session.pageNumber,
                        bugs_fixed: bugsFixed,
                    }),
                }
            );

            const data = await response.json();

            if (data.error) {
                alert(data.error);
                if (data.redirect_dashboard) {
                    window.location.href = CONFIG.BACKEND_URL + '/dashboard/';
                }
                return;
            }

            if (data.success) {
                // ✅ Update score
                const scoreEl = document.getElementById('current-score');
                if (scoreEl) scoreEl.textContent = data.current_score;

                // ✅ Update token from backend response
                if (data.new_token) {
                    this.session.token = data.new_token;
                    localStorage.setItem('game_token', data.new_token);
                    CONFIG.setSession({ token: data.new_token });
                    console.log('🔑 New token received:', data.new_token);
                }

                // ✅ CRITICAL: Broadcast PAGE NAVIGATION to teammates
                if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send(JSON.stringify({
                        type: 'page_changed',
                        next_page: nextPage,
                        new_token: this.session.token
                    }));
                    console.log('📢 Broadcasted page_changed to teammates:', {
                        next_page: nextPage,
                        new_token: this.session.token
                    });
                }

                // ✅ CHECK FOR ROUND COMPLETION OR FINAL PAGE
                if (data.round_completed || isFinalPage) {
                    // Determine which round just completed
                    let roundName = 'Round';
                    if (currentPage === 10) roundName = 'Round 1';
                    else if (currentPage === 20) roundName = 'Round 2';
                    else if (currentPage === 30) roundName = 'Round 3';
                    
                    alert(`🎉 ${roundName} Completed!\n\nFinal Score: ${data.final_score || data.current_score}\n\nReturning to dashboard...`);
                    
                    console.log(`✅ ${roundName} completed at page ${currentPage}. Redirecting to dashboard.`);
                    
                    // Close WebSocket before leaving
                    if (this.ws) {
                        this.ws.close();
                    }
                    
                    window.location.href = CONFIG.BACKEND_URL + '/dashboard/';
                } else {
                    // ✅ Navigate to next page (only if NOT a final page)
                    const nextPageUrl = `/round${this.session.roundNumber}/page${nextPage}.html?team=${this.session.teamId}&token=${this.session.token}&round=${this.session.roundNumber}&page=${nextPage}`;
                    console.log('🔄 Moving to next page:', nextPageUrl);
                    window.location.href = nextPageUrl;
                }
            }
        } catch (error) {
            console.error('Error moving to next page:', error);
            alert('Error. Please try again.');
        }
    }

    extractURLParams() {
        const urlParams = new URLSearchParams(window.location.search);
        const teamFromURL = urlParams.get('team');
        const tokenFromURL = urlParams.get('token');
        const roundFromURL = urlParams.get('round');
        const pageFromURL = urlParams.get('page');
        
        console.log('🔍 URL Params:', { teamFromURL, tokenFromURL, roundFromURL, pageFromURL });
        
        if (teamFromURL) {
            localStorage.setItem('team_id', teamFromURL);
            this.session.teamId = teamFromURL;
        }
        
        if (tokenFromURL) {
            localStorage.setItem('game_token', tokenFromURL);
            this.session.token = tokenFromURL;
        }

        if (roundFromURL) {
            localStorage.setItem('current_round', roundFromURL);
            this.session.roundNumber = parseInt(roundFromURL);
        }

        if (pageFromURL) {
            localStorage.setItem('current_page', pageFromURL);
            this.session.pageNumber = parseInt(pageFromURL);
        }
    }

    validateToken() {
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');

        if (!token && !this.session?.token) {
            alert('Invalid access! Redirecting to dashboard...');
            window.location.href = CONFIG.BACKEND_URL + '/dashboard/';
            return;
        }

        if (token) {
            this.session.token = token;
            CONFIG.setSession({ token });
        }
    }

    async loadGameState() {
        this.session = CONFIG.getSession();
        
        if (!this.session?.teamId || !this.session?.roundNumber) {
            alert('Session expired. Redirecting to dashboard...');
            window.location.href = CONFIG.BACKEND_URL + '/dashboard/';
            return;
        }

        try {
            const response = await fetch(
                CONFIG.BACKEND_URL + CONFIG.API.GAME_STATE,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    credentials: 'include',
                    body: JSON.stringify({
                        team_id: this.session.teamId,
                        round_number: this.session.roundNumber,
                        token: this.session.token,
                    }),
                }
            );

            const data = await response.json();

            if (data.error) {
                alert(data.error);
                return;
            }

            // ✅ Update token if backend sends a new one
            if (data.current_token) {
                this.session.token = data.current_token;
                localStorage.setItem('game_token', data.current_token);
                CONFIG.setSession({ token: data.current_token });
                console.log('🔑 Token updated from game state');
            }

            const teamEl = document.getElementById('team-name');
            const scoreEl = document.getElementById('current-score');
            const roundEl = document.getElementById('round-num');
            const pageEl = document.getElementById('page-num');

            if (teamEl) teamEl.textContent = data.team_name;
            if (scoreEl) scoreEl.textContent = data.current_score;
            if (roundEl) roundEl.textContent = this.session.roundNumber;
            if (pageEl) pageEl.textContent = this.session.pageNumber;

            this.startCountdown(data.time_remaining);
        } catch (error) {
            console.error('Error loading game state:', error);
            alert('Failed to load game state.');
        }
    }

    startCountdown(seconds) {
        let timeLeft = seconds;
        const timerEl = document.getElementById('timer');

        if (!timerEl) return;

        clearInterval(this.timer);

        this.timer = setInterval(() => {
            if (timeLeft <= 0) {
                clearInterval(this.timer);
                alert('Time is up! Returning to dashboard...');
                window.location.href = CONFIG.BACKEND_URL + '/dashboard/';
                return;
            }

            const minutes = Math.floor(timeLeft / 60);
            const secs = timeLeft % 60;

            timerEl.textContent = `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

            if (timeLeft <= 300) {
                timerEl.classList.add('timer-warning');
            }

            timeLeft--;
        }, 1000);
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => notification.classList.add('show'), 50);

        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    exitGame() {
        if (confirm('Exit game and return to dashboard? (Progress will be saved)')) {
            if (this.ws) {
                this.ws.close();
            }
            window.location.href = CONFIG.BACKEND_URL + '/dashboard/';
        }
    }
}

// ✅ CRITICAL: Initialize immediately and expose globally
console.log('🔧 Creating gameEngine instance...');
let gameEngine;

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('🔧 DOM ready, initializing gameEngine...');
        gameEngine = new GameEngine();
        window.gameEngine = gameEngine;
        gameEngine.init();
    });
} else {
    // DOM already loaded
    console.log('🔧 DOM already ready, initializing gameEngine immediately...');
    gameEngine = new GameEngine();
    window.gameEngine = gameEngine;
    gameEngine.init();
}

function exitGame() {
    if (window.gameEngine) {
        gameEngine.exitGame();
    }
}

console.log('🔧 game-engine.js loaded successfully');