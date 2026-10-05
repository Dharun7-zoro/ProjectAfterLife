// Project After Life - Main Client JavaScript

document.addEventListener('DOMContentLoaded', () => {
    // 1. Tab Switching Functionality
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            const parent = btn.closest('.tabs-container') || document;
            
            // Deactivate all sibling buttons
            parent.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            parent.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            // Activate current
            btn.classList.add('active');
            const targetContent = parent.querySelector(`#${targetTab}`);
            if (targetContent) {
                targetContent.classList.add('active');
            }
        });
    });

    // 2. Real-time GitHub URL Validator
    const githubInput = document.getElementById('github_url');
    const githubFeedback = document.getElementById('github_feedback');
    if (githubInput && githubFeedback) {
        const validateGithub = () => {
            const val = githubInput.value.trim();
            const pattern = /^https?:\/\/(www\.)?github\.com\/[a-zA-Z0-9_\-\.]+\/[a-zA-Z0-9_\-\.]+.*$/;
            if (!val) {
                githubFeedback.innerHTML = '<span style="color: var(--text-muted);">Required format: https://github.com/username/repository</span>';
                githubInput.style.borderColor = 'var(--border-color)';
                return false;
            }
            if (pattern.test(val)) {
                githubFeedback.innerHTML = '<span style="color: #34d399;">✓ Valid GitHub repository URL format</span>';
                githubInput.style.borderColor = '#10b981';
                return true;
            } else {
                githubFeedback.innerHTML = '<span style="color: #f87171;">✗ Invalid format. Must be https://github.com/owner/repo</span>';
                githubInput.style.borderColor = '#ef4444';
                return false;
            }
        };
        githubInput.addEventListener('input', validateGithub);
        githubInput.addEventListener('blur', validateGithub);
    }

    // 3. Task Checkbox AJAX Toggle
    const taskCheckboxes = document.querySelectorAll('.task-checkbox');
    taskCheckboxes.forEach(cb => {
        cb.addEventListener('change', async (e) => {
            const taskId = cb.getAttribute('data-task-id');
            const taskItem = cb.closest('.task-item');
            
            try {
                const res = await fetch(`/task/${taskId}/toggle`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                const data = await res.json();
                if (data.completed) {
                    taskItem.classList.add('completed');
                } else {
                    taskItem.classList.remove('completed');
                }
            } catch (err) {
                console.error("Failed to toggle task", err);
            }
        });
    });

    // 4. Bookmark / Save Project AJAX Toggle
    const saveButtons = document.querySelectorAll('.btn-save-project');
    saveButtons.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const projectId = btn.getAttribute('data-project-id');
            try {
                const res = await fetch(`/project/${projectId}/toggle-save`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                if (res.status === 403) {
                    alert("Only company accounts can save/shortlist projects.");
                    return;
                }
                const data = await res.json();
                if (data.saved) {
                    btn.classList.add('saved');
                    btn.innerHTML = '★ Saved';
                    btn.style.color = '#fbbf24';
                } else {
                    btn.classList.remove('saved');
                    btn.innerHTML = '☆ Save';
                    btn.style.color = 'var(--text-secondary)';
                }
            } catch (err) {
                console.error("Save failed", err);
            }
        });
    });

    // 5. Dismiss Alerts
    document.querySelectorAll('.alert-close').forEach(btn => {
        btn.addEventListener('click', () => {
            const alert = btn.closest('.alert');
            if (alert) alert.style.display = 'none';
        });
    });
});
