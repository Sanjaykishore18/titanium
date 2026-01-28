class GameEngine {
    constructor() {
        this.bugsFixed = new Set();
        this.totalBugs = 3;
        this.session = CONFIG.getSession();
        this.timer = null;
    }

    // Initialize game page
    async init() {
        this.extractURLParams(); // Extract team_id from URL if present
        this.validateToken();
        this.setupBugTracking();
        await this.loadGameState(); // countdown starts here
    }

    // Extract team_id and token from URL parameters
// Extract team_id and token from URL parameters
    extractURLParams() {
        const urlParams = new URLSearchParams(window.location.search);
        const teamFromURL = urlParams.get('team');
        const tokenFromURL = urlParams.get('token');
        const roundFromURL = urlParams.get('round');      // ✅ NEW
        const pageFromURL = urlParams.get('page');        // ✅ NEW
        
        // Store all URL params to localStorage
        if (teamFromURL) {
            localStorage.setItem('team_id', teamFromURL);
            this.session.teamId = teamFromURL;
        }
        
        if (tokenFromURL) {
            localStorage.setItem('game_token', tokenFromURL);
            this.session.token = tokenFromURL;
        }

        // ✅ NEW: Store round and page from URL
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
        // Re-fetch session after extracting URL params
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

            if (teamEl) teamEl.textContent = data.team_name;
            if (scoreEl) scoreEl.textContent = data.current_score;

            // Start countdown timer
            this.startCountdown(data.time_remaining);
        } catch (error) {
            console.error('Error loading game state:', error);
            alert('Failed to load game state.');
        }
    }

    // Setup bug tracking UI
    setupBugTracking() {
        const bugCounter = document.getElementById('bugs-fixed');
        if (bugCounter) {
            bugCounter.textContent = `0/${this.totalBugs}`;
        }
    }

    // Mark bug as fixed
    fixBug(bugId) {
        if (this.bugsFixed.has(bugId)) return;

        this.bugsFixed.add(bugId);

        const bugCounter = document.getElementById('bugs-fixed');
        if (bugCounter) {
            bugCounter.textContent = `${this.bugsFixed.size}/${this.totalBugs}`;
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
                    window.location.href =
                        CONFIG.BACKEND_URL + '/dashboard/';
                }
                return;
            }

            if (data.success) {
                const scoreEl = document.getElementById('current-score');
                if (scoreEl) scoreEl.textContent = data.current_score;

                if (data.round_completed) {
                    alert(
                        `${data.message} Final Score: ${data.final_score}`
                    );
                    window.location.href =
                        CONFIG.BACKEND_URL + '/dashboard/';
                } else {
                    this.showNotification(
                        'Page completed! +10 points',
                        'success'
                    );
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
                window.location.href =
                    CONFIG.BACKEND_URL + '/dashboard/';
                return;
            }

            const minutes = Math.floor(timeLeft / 60);
            const secs = timeLeft % 60;

            timerEl.textContent = `${String(minutes).padStart(
                2,
                '0'
            )}:${String(secs).padStart(2, '0')}`;

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
        if (
            confirm(
                'Exit game and return to dashboard? (Progress will be saved)'
            )
        ) {
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