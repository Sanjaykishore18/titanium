// ============================================================================
// CORRECTED CONFIG.JS - Fixed CSRF and token issues
// Save as: frontend/assets/js/config.js
// ============================================================================

const CONFIG = {
    // Backend URL (port 8000 for Django)
    BACKEND_URL: `http://${window.location.hostname}:8000`,
    
    API: {
        START_GAME: '/api/start-game/',
        VALIDATE_PAGE: '/api/validate-page/',
        GAME_STATE: '/api/game-state/',
    },
    
    // WebSocket configuration
    WEBSOCKET: {
        getUrl: function(teamId, roundNumber) {
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsHost = window.location.hostname;
            return `${wsProtocol}//${wsHost}:8000/ws/game/team/${teamId}/round/${roundNumber}/`;
        }
    },
    
    // ✅ NEW: Get CSRF token from cookies
    getCsrfToken: function() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    },
    
    getSession: function() {
        const session = {
            teamId: localStorage.getItem('team_id'),
            token: localStorage.getItem('game_token'),
            roundNumber: parseInt(localStorage.getItem('current_round')),
            pageNumber: parseInt(localStorage.getItem('current_page'))
        };
        
        if (isNaN(session.roundNumber)) session.roundNumber = null;
        if (isNaN(session.pageNumber)) session.pageNumber = null;
        
        console.log('Current Session:', session);
        return session;
    },
    
    setSession: function(data) {
        if (data.teamId) localStorage.setItem('team_id', data.teamId);
        if (data.token) localStorage.setItem('game_token', data.token);
        if (data.roundNumber) localStorage.setItem('current_round', data.roundNumber);
        if (data.pageNumber) localStorage.setItem('current_page', data.pageNumber);
    },
    
    clearSession: function() {
        localStorage.removeItem('team_id');
        localStorage.removeItem('game_token');
        localStorage.removeItem('current_round');
        localStorage.removeItem('current_page');
    }
};