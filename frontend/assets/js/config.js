const CONFIG = {
    BACKEND_URL: 'http://10.98.207.227:8000',  // ✅ UPDATED IP
    
    API: {
        START_GAME: '/api/start-game/',
        VALIDATE_PAGE: '/api/validate-page/',
        GAME_STATE: '/api/game-state/',
    },
    
    // ✅ NEW: WebSocket configuration
    WEBSOCKET: {
        getUrl: function(teamId, roundNumber) {
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsHost = CONFIG.BACKEND_URL.replace('http://', '').replace('https://', '');
            return `${wsProtocol}//${wsHost}/ws/game/team/${teamId}/round/${roundNumber}/`;
        }
    },
    
    getSession: function() {
        const session = {
            teamId: localStorage.getItem('team_id'),
            token: localStorage.getItem('game_token'),
            roundNumber: parseInt(localStorage.getItem('current_round')),
            pageNumber: parseInt(localStorage.getItem('current_page'))
        };
        
        // Validate numbers aren't NaN
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
    
    // ✅ NEW: Clear session on logout/exit
    clearSession: function() {
        localStorage.removeItem('team_id');
        localStorage.removeItem('game_token');
        localStorage.removeItem('current_round');
        localStorage.removeItem('current_page');
    }
};