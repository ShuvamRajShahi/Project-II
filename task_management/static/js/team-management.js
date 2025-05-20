// Team Management API Handlers
const TeamAPI = {
    // Fetch team members
    getMembers: async () => {
        const response = await fetch('/team/api/members/');
        return await response.json();
    },

    // Fetch user's projects
    getUserProjects: async (userId) => {
        const response = await fetch(`/team/api/projects/${userId}/`);
        return await response.json();
    },

    // Fetch team statistics
    getStats: async () => {
        const response = await fetch('/team/api/stats/');
        return await response.json();
    },

    // Fetch project members
    getProjectMembers: async (projectId) => {
        const response = await fetch(`/team/api/project/${projectId}/members/`);
        return await response.json();
    },

    // Update member role
    updateRole: async (userId, role) => {
        const response = await fetch('/team/update-role/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({ user_id: userId, role: role })
        });
        return await response.json();
    }
};

// Initialize team management features
document.addEventListener('DOMContentLoaded', () => {
    // Role change handler
    document.querySelectorAll('.role-select').forEach(select => {
        select.addEventListener('change', async (e) => {
            const userId = e.target.dataset.userId;
            const newRole = e.target.value;
            
            try {
                const result = await TeamAPI.updateRole(userId, newRole);
                if (result.success) {
                    location.reload();
                }
            } catch (error) {
                console.error('Error updating role:', error);
            }
        });
    });

    // Load team statistics
    const loadStats = async () => {
        try {
            const stats = await TeamAPI.getStats();
            // Update statistics in the UI
            document.getElementById('total-members').textContent = stats.total_members;
            document.getElementById('active-projects').textContent = stats.active_projects;
            document.getElementById('completion-rate').textContent = `${stats.completion_rate}%`;
            
            // Update workload chart if exists
            if (window.workloadChart) {
                updateWorkloadChart(stats.workload);
            }
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    };

    // Initial load
    loadStats();
    
    // Refresh stats every 5 minutes
    setInterval(loadStats, 300000);
}); 