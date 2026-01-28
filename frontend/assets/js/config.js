const CONFIG = {
    BACKEND_URL: 'https://pipe-investigators-lion-suburban.trycloudflare.com',
    
    API: {
        START_GAME: '/api/start-game/',
        VALIDATE_PAGE: '/api/validate-page/',
        GAME_STATE: '/api/game-state/',
    },
    
    getSession: function() {
        // ✅ IMPROVED: Better error checking
        const session = {
            teamId: localStorage.getItem('team_id'),
            token: localStorage.getItem('game_token'),
            roundNumber: parseInt(localStorage.getItem('current_round')),
            pageNumber: parseInt(localStorage.getItem('current_page'))
        };
        
        // Validate numbers aren't NaN
        if (isNaN(session.roundNumber)) session.roundNumber = null;
        if (isNaN(session.pageNumber)) session.pageNumber = null;
        
        console.log('Current Session:', session); // ✅ Debug logging
        return session;
    },
    
    setSession: function(data) {
        if (data.teamId) localStorage.setItem('team_id', data.teamId);
        if (data.token) localStorage.setItem('game_token', data.token);
        if (data.roundNumber) localStorage.setItem('current_round', data.roundNumber);
        if (data.pageNumber) localStorage.setItem('current_page', data.pageNumber);
    }
};
