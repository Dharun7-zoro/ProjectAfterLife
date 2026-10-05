// Inbuilt AI Chatbot Client Controller

document.addEventListener('DOMContentLoaded', () => {
    const chatBtn = document.getElementById('aiChatWidgetBtn');
    const chatModal = document.getElementById('aiChatWidgetModal');
    const closeBtn = document.getElementById('aiChatCloseBtn');
    const clearBtn = document.getElementById('aiChatClearBtn');
    const chatForm = document.getElementById('aiChatForm');
    const chatInput = document.getElementById('aiChatInput');
    const messagesBox = document.getElementById('aiChatMessages');
    const chipsContainer = document.getElementById('aiChatChips');
    const roleBadge = document.getElementById('aiChatRoleBadge');

    if (!chatBtn || !chatModal) return;

    // Determine current user role & project context from page DOM
    const userRole = document.body.getAttribute('data-user-role') || 'student';
    const projectElement = document.querySelector('[data-current-project-id]');
    const currentProjectId = projectElement ? projectElement.getAttribute('data-current-project-id') : null;

    if (roleBadge) {
        roleBadge.innerText = userRole.toUpperCase() + (currentProjectId ? ' • PROJECT CONTEXT' : ' MODE');
    }

    // Toggle Modal
    chatBtn.addEventListener('click', () => {
        const isVisible = chatModal.style.display === 'flex';
        chatModal.style.display = isVisible ? 'none' : 'flex';
        if (!isVisible) {
            chatInput.focus();
            scrollToBottom();
        }
    });

    closeBtn.addEventListener('click', () => {
        chatModal.style.display = 'none';
    });

    // Clear Chat
    clearBtn.addEventListener('click', () => {
        messagesBox.innerHTML = '';
        appendBotMessage(
            `Chat history cleared. I'm your AI Project Assistant running in **${userRole.toUpperCase()}** mode.` +
            (currentProjectId ? " I have this project's full submission context loaded." : "")
        );
    });

    // Simple Markdown to HTML formatter
    function formatMarkdown(text) {
        if (!text) return '';
        let escaped = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');

        // Bold
        escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Italic
        escaped = escaped.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // Inline Code
        escaped = escaped.replace(/`([^`]+)`/g, '<code style="background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 0.82rem; color: #38bdf8;">$1</code>');
        
        // Blockquotes
        escaped = escaped.replace(/^> (.*$)/gim, '<blockquote style="border-left: 3px solid #6366f1; padding-left: 10px; margin: 8px 0; color: #94a3b8; font-style: italic;">$1</blockquote>');
        
        // Line breaks & bullet lists
        escaped = escaped.replace(/^\s*•\s*(.*$)/gim, '<li style="margin-left: 18px; margin-bottom: 4px;">$1</li>');
        escaped = escaped.replace(/\n/g, '<br>');
        
        return escaped;
    }

    function appendUserMessage(text) {
        const div = document.createElement('div');
        div.className = 'chat-bubble user';
        div.innerText = text;
        messagesBox.appendChild(div);
        scrollToBottom();
    }

    function appendBotMessage(markdownText) {
        const div = document.createElement('div');
        div.className = 'chat-bubble bot';
        div.innerHTML = formatMarkdown(markdownText);
        messagesBox.appendChild(div);
        scrollToBottom();
    }

    function scrollToBottom() {
        messagesBox.scrollTop = messagesBox.scrollHeight;
    }

    // Handle Form Submit
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const msg = chatInput.value.trim();
        if (!msg) return;

        appendUserMessage(msg);
        chatInput.value = '';

        // Temporary thinking indicator
        const loadingId = 'ai-loading-' + Date.now();
        const loadingDiv = document.createElement('div');
        loadingDiv.id = loadingId;
        loadingDiv.className = 'chat-bubble bot';
        loadingDiv.innerHTML = '<span style="color: var(--secondary); font-style: italic;">Consulting project intelligence...</span>';
        messagesBox.appendChild(loadingDiv);
        scrollToBottom();

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: msg,
                    role: userRole,
                    project_id: currentProjectId
                })
            });

            const data = await res.json();
            const loader = document.getElementById(loadingId);
            if (loader) loader.remove();

            appendBotMessage(data.reply);

            // Update suggested chips if provided
            if (data.suggested_questions && data.suggested_questions.length > 0) {
                renderChips(data.suggested_questions);
            }
        } catch (err) {
            const loader = document.getElementById(loadingId);
            if (loader) loader.remove();
            appendBotMessage("An error occurred while connecting to the AI assistant. Please try again.");
            console.error(err);
        }
    });

    // Render Quick Question Chips
    function renderChips(questions) {
        chipsContainer.innerHTML = '';
        questions.forEach(q => {
            const chip = document.createElement('button');
            chip.type = 'button';
            chip.className = 'chat-chip';
            chip.innerText = q;
            chip.addEventListener('click', () => {
                chatInput.value = q;
                chatForm.dispatchEvent(new Event('submit'));
            });
            chipsContainer.appendChild(chip);
        });
    }

    // Default chips based on context
    if (currentProjectId) {
        renderChips([
            "What problem does this project solve?",
            "What technologies are used?",
            "How can this project be used in our industry?",
            "What questions should I ask the student team?",
            "What is the funding requirement?"
        ]);
    } else if (userRole === 'company') {
        renderChips([
            "How do I find projects by technology?",
            "Explain project evaluation criteria",
            "How does funding proposal work?",
            "How to monitor project development progress?"
        ]);
    } else {
        renderChips([
            "How to submit a project?",
            "How to write an impactful problem statement?",
            "How to explain our proposed solution?",
            "How do I add a valid GitHub repository?",
            "How do I create development milestones?"
        ]);
    }
});
