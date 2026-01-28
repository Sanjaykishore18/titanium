class GameEngine {
    constructor() {
        this.bugsFixed = new Set();
        this.totalBugs = 3;
        this.session = CONFIG.getSession();
        this.timer = null;
        this.ws = null; // ✅ WebSocket connection
        this.isPageCompleted = false; // ✅ Track if current page is done
    }

    // Initialize game page
    async init() {
        this.extractURLParams();
        this.validateToken();
        this.setupBugTracking();
        await this.loadGameState();
        this.connectWebSocket(); // ✅ NEW: Connect to WebSocket
    }

    // ✅ NEW: Establish WebSocket Connection
    connectWebSocket() {
        const session = this.session;
        
        if (!session?.teamId || !session?.roundNumber) {
            console.error('Cannot connect WebSocket: Missing team or round info');
            return;
        }

        // WebSocket URL pattern: ws://backend/ws/game/team/{team_id}/round/{round_number}/
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsHost = CONFIG.BACKEND_URL.replace('http://', '').replace('https://', '');
        const wsUrl = `${wsProtocol}//${wsHost}/ws/game/team/${session.teamId}/round/${session.roundNumber}/`;

        console.log('Connecting to WebSocket:', wsUrl);

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('✅ WebSocket connected');
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
            // ✅ Auto-reconnect after 3 seconds
            setTimeout(() => {
                if (!this.isPageCompleted) {
                    console.log('Reconnecting WebSocket...');
                    this.connectWebSocket();
                }
            }, 3000);
        };
    }

    // ✅ NEW: Handle incoming WebSocket messages
    handleWebSocketMessage(data) {
        console.log('WebSocket message received:', data);

        switch (data.type) {
            case 'game_state':
                this.updateGameState(data.data);
                break;

            case 'bug_fixed':
                this.handleTeammateBugFix(data);
                break;

            case 'page_completed':
                this.handleTeammatePageCompletion(data);
                break;

            default:
                console.log('Unknown message type:', data.type);
        }
    }

    // ✅ NEW: Update game state from WebSocket
    updateGameState(state) {
        console.log('Updating game state:', state);

        // Update score
        const scoreEl = document.getElementById('current-score');
        if (scoreEl && state.score !== undefined) {
            scoreEl.textContent = state.score;
        }

        // Check if current page is already completed by team
        if (state.pages && Array.isArray(state.pages)) {
            const currentPageState = state.pages.find(p => p.page_number === this.session.pageNumber);
            
            if (currentPageState && currentPageState.completed && !this.isPageCompleted) {
                this.showPageCompletedByTeam();
            }
        }
    }

    // ✅ NEW: Show that page was completed by teammate
    showPageCompletedByTeam() {
        this.isPageCompleted = true;
        
        this.showNotification('✅ Page completed by your team!', 'success');

        // Enable the complete button for all team members
        const completeBtn = document.getElementById('complete-btn');
        if (completeBtn) {
            completeBtn.disabled = false;
            completeBtn.classList.add('btn-pulse');
            completeBtn.innerHTML = '✅ Continue to Next Page (Completed by Team)';
            completeBtn.onclick = () => this.moveToNextPage(); // ✅ Just move, don't resubmit
        }
    }

    // ✅ NEW: Handle teammate's bug fix
    handleTeammateBugFix(data) {
        const { bug_id, user } = data;
        
        this.showNotification(`${user} fixed Bug ${bug_id}`, 'info');
        
        // Optionally mark bug as fixed locally too (visual sync)
        this.bugsFixed.add(bug_id);
        this.updateBugCounter();
    }

    // ✅ NEW: Handle teammate's page completion
    handleTeammatePageCompletion(data) {
        const { page_number, user } = data;
        
        if (page_number === this.session.pageNumber) {
            this.showNotification(`${user} completed this page!`, 'success');
            this.showPageCompletedByTeam();
        }
    }

    // ✅ NEW: Move to next page without resubmitting
    async moveToNextPage() {
        try {
            // Just redirect to next page using stored URL or calculate it
            const nextPage = this.session.pageNumber + 1;
            
            if (nextPage > 10) {
                // Round completed
                alert('Round completed! Returning to dashboard...');
                window.location.href = CONFIG.BACKEND_URL + '/dashboard/';
                return;
            }

            const nextPageUrl = `/round${this.session.roundNumber}/page${nextPage}.html?team=${this.session.teamId}&token=${this.session.token}&round=${this.session.roundNumber}&page=${nextPage}`;
            window.location.href = nextPageUrl;

        } catch (error) {
            console.error('Error moving to next page:', error);
            alert('Error. Please try again.');
        }
    }

    // Extract team_id and token from URL parameters
    extractURLParams() {
        const urlParams = new URLSearchParams(window.location.search);
        const teamFromURL = urlParams.get('team');
        const tokenFromURL = urlParams.get('token');
        const roundFromURL = urlParams.get('round');
        const pageFromURL = urlParams.get('page');
        
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

    // Validate URL token
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

    // Load game state from backend
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
                    }),
                }
            );

            const data = await response.json();

            if (data.error) {
                alert(data.error);
                return;
            }

            // Update UI
            const teamEl = document.getElementById('team-name');
            const scoreEl = document.getElementById('current-score');
            const roundEl = document.getElementById('round-num');
            const pageEl = document.getElementById('page-num');

            if (teamEl) teamEl.textContent = data.team_name;
            if (scoreEl) scoreEl.textContent = data.current_score;
            if (roundEl) roundEl.textContent = this.session.roundNumber;
            if (pageEl) pageEl.textContent = this.session.pageNumber;

            // ✅ Check if this page is already completed
            if (data.current_page > this.session.pageNumber) {
                this.showPageCompletedByTeam();
            }

            // Start countdown timer
            this.startCountdown(data.time_remaining);
        } catch (error) {
            console.error('Error loading game state:', error);
            alert('Failed to load game state.');
        }
    }

    // Setup bug tracking UI
    setupBugTracking() {
        this.updateBugCounter();
    }

    // ✅ NEW: Update bug counter UI
    updateBugCounter() {
        const bugCounter = document.getElementById('bugs-fixed');
        if (bugCounter) {
            bugCounter.textContent = `${this.bugsFixed.size}/${this.totalBugs}`;
        }
    }

    // Mark bug as fixed
    fixBug(bugId) {
        if (this.bugsFixed.has(bugId)) return;

        this.bugsFixed.add(bugId);
        this.updateBugCounter();

        // ✅ Broadcast to team via WebSocket
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'bug_fixed',
                page_number: this.session.pageNumber,
                bug_id: bugId,
                user: this.session.teamId // You can get actual username if stored
            }));
        }

        this.showNotification(`Bug ${bugId} fixed! ✓`, 'success');

        if (this.bugsFixed.size >= this.totalBugs) {
            this.showNotification(
                'All bugs fixed! You can complete this page!',
                'success'
            );

            const completeBtn = document.getElementById('complete-btn');
            if (completeBtn) {
                completeBtn.disabled = false;
                completeBtn.classList.add('btn-pulse');
            }
        }
    }

    // Complete page
    async completePage() {
        // ✅ If already completed by team, just move to next page
        if (this.isPageCompleted) {
            this.moveToNextPage();
            return;
        }

        if (this.bugsFixed.size < this.totalBugs) {
            alert(`You must fix all ${this.totalBugs} bugs first!`);
            return;
        }

        if (!confirm('Complete this page and move to the next?')) return;

        try {
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
                        bugs_fixed: Array.from(this.bugsFixed),
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
                const scoreEl = document.getElementById('current-score');
                if (scoreEl) scoreEl.textContent = data.current_score;

                // ✅ Broadcast page completion to team
                if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send(JSON.stringify({
                        type: 'page_completed',
                        page_number: this.session.pageNumber,
                        user: this.session.teamId
                    }));
                }

                if (data.round_completed) {
                    alert(`${data.message} Final Score: ${data.final_score}`);
                    window.location.href = CONFIG.BACKEND_URL + '/dashboard/';
                } else {
                    this.showNotification('Page completed! +10 points', 'success');
                    setTimeout(() => {
                        window.location.href = data.next_page_url;
                    }, 1500);
                }
            }
        } catch (error) {
            console.error('Error completing page:', error);
            alert('Error completing page. Please try again.');
        }
    }

    // Countdown timer
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

    // Notifications
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

    // Exit game
    exitGame() {
        if (confirm('Exit game and return to dashboard? (Progress will be saved)')) {
            // Close WebSocket
            if (this.ws) {
                this.ws.close();
            }
            window.location.href = CONFIG.BACKEND_URL + '/dashboard/';
        }
    }
}

// Initialize game engine
let gameEngine;
window.addEventListener('DOMContentLoaded', () => {
    gameEngine = new GameEngine();
    gameEngine.init();
});

// Global handlers for HTML
function fixBug(bugId) {
    gameEngine.fixBug(bugId);
}

function completePage() {
    gameEngine.completePage();
}

function exitGame() {
    gameEngine.exitGame();
}