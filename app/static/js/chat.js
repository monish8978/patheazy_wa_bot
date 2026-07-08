// State configuration for simulator client
const MOCK_USER_ID = "PATHEAZY-USER-99";
const chatMessages = document.getElementById("chat-messages");
const chatInput = document.getElementById("chat-input");
const quickRepliesContainer = document.getElementById("quick-replies");
const ticketList = document.getElementById("ticket-list");

// Document ready entry
document.addEventListener("DOMContentLoaded", () => {
    // Perform initial loading
    initializeChat();
});

// Initialize chatbot by requesting initial greeting
async function initializeChat() {
    chatMessages.innerHTML = "";
    quickRepliesContainer.innerHTML = "";

    // Check if there are existing logs, or trigger standard welcome message
    try {
        const response = await fetch(`/api/logs/${MOCK_USER_ID}`);
        const logs = await response.json();

        if (logs && logs.length > 0) {
            logs.forEach(log => {
                appendBubble(log.sender.toLowerCase(), log.message_text, false);
            });
            scrollToBottom();
        } else {
            // Trigger main menu initial greetings
            submitMessage("", "MAIN_MENU");
        }
    } catch (e) {
        console.error("Failed to load logs:", e);
        submitMessage("", "MAIN_MENU");
    }
}

// Send user text from input bar
function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    appendBubble("user", text);
    chatInput.value = "";
    quickRepliesContainer.innerHTML = "";

    submitMessage(text, null);
}

// Handle enter key submit
function handleEnterKey(event) {
    if (event.key === "Enter") {
        sendMessage();
    }
}

// Action button / postback button press handler
function handleActionButton(title, payload) {
    if (payload && (payload.startsWith("http://") || payload.startsWith("https://"))) {
        window.open(payload, "_blank");
        return;
    }
    appendBubble("user", title);
    quickRepliesContainer.innerHTML = "";

    submitMessage(title, payload);
}

// Quick reply pill click handler
function handleQuickReply(title, payload) {
    if (payload && (payload.startsWith("http://") || payload.startsWith("https://"))) {
        window.open(payload, "_blank");
        return;
    }
    appendBubble("user", title);
    quickRepliesContainer.innerHTML = "";

    submitMessage(title, payload);
}

// Send payload to backend
async function submitMessage(message, payload) {
    // Add custom typing indicator bubble
    const typingIndicator = appendTypingIndicator();

    try {
        const response = await fetch("/api/simulate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                query: payload || message || "",
                app_id: "1212",
                sessionid: MOCK_USER_ID,
                clientId: 208,
                botId: 1212,
                extraParms: JSON.stringify({ source: "webchat", csid: "731779738973688" })
            })
        });

        const data = await response.json();

        // Remove typing indicator bubble
        typingIndicator.remove();

        // Render bot message
        appendBotResponse(data);

    } catch (e) {
        typingIndicator.remove();
        appendBubble("bot", "⚠️ Network connection lost. Please check if backend services are active.");
        console.error("Simulation error:", e);
    }
}

// Appends standard text bubble
function appendBubble(sender, text, animate = true) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", sender);
    if (!animate) messageDiv.style.animation = "none";

    messageDiv.innerHTML = formatMarkdown(text);
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
    return messageDiv;
}

// Appends typing loader animation
function appendTypingIndicator() {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", "bot");
    messageDiv.innerHTML = `
        <div style="display: flex; gap: 4px; align-items: center; padding: 4px 8px;">
            <i class="fa-solid fa-circle" style="font-size: 6px; animation: bounce 1.2s infinite; color: var(--text-secondary);"></i>
            <i class="fa-solid fa-circle" style="font-size: 6px; animation: bounce 1.2s infinite 0.2s; color: var(--text-secondary);"></i>
            <i class="fa-solid fa-circle" style="font-size: 6px; animation: bounce 1.2s infinite 0.4s; color: var(--text-secondary);"></i>
        </div>
        <style>
            @keyframes bounce {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-4px); }
            }
        </style>
    `;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
    return messageDiv;
}

// Appends multi-featured bot response structure (AdaptiveCard layout)
function appendBotResponse(data) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", "bot");

    let botText = "";
    let choices = [];

    // Parse AdaptiveCard body
    if (data.body && data.body.length > 0) {
        data.body.forEach(block => {
            if (block.type === "TextBlock") {
                botText = block.text;
            } else if (block.type === "Button" && block.choices) {
                choices = block.choices;
            }
        });
    }

    // 1. Set text content with custom formatting
    let contentHtml = formatMarkdown(botText || data.text || "");

    // 2. Render choice buttons inside the message bubble
    if ((choices && choices.length > 0) || (data.actions && data.actions.length > 0)) {
        contentHtml += `<div class="bot-action-buttons">`;
        if (choices && choices.length > 0) {
            choices.forEach(choice => {
                contentHtml += `
                    <div class="action-btn" onclick="handleActionButton('${choice.title}', '${choice.id}')">
                        ${choice.title}
                    </div>
                `;
            });
        }
        if (data.actions && data.actions.length > 0) {
            data.actions.forEach(action => {
                const payloadVal = action.value || action.title || "";
                contentHtml += `
                    <div class="action-btn" onclick="handleActionButton('${action.title}', '${payloadVal}')">
                        ${action.title}
                    </div>
                `;
            });
        }
        contentHtml += `</div>`;
    }

    messageDiv.innerHTML = contentHtml;
    chatMessages.appendChild(messageDiv);

    // Clear quick replies since they are merged into body choices
    quickRepliesContainer.innerHTML = "";

    scrollToBottom();
}

// Utility formatting helper
function formatMarkdown(text) {
    if (!text) return "";

    let html = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

    // Bold formats
    html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/\*(.*?)\*/g, "<strong>$1</strong>");

    // Newlines conversion
    html = html.replace(/\n/g, "<br>");

    // Bullet formats
    html = html.replace(/•\s(.*?)(<br>|$)/g, "<li>$1</li>");
    html = html.replace(/-\s(.*?)(<br>|$)/g, "<li>$1</li>");

    // 1. Parse markdown links [text](url)
    html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" style="color: var(--accent-gold); text-decoration: underline;">$1</a>');

    // 2. Convert raw URLs to links (excluding those already inside href or parenthesis)
    html = html.replace(/(?<!href=\")(?<!href=\')(?<!\()(https?:\/\/[^\s<)]+)/g, '<a href="$1" target="_blank" style="color: var(--accent-gold); text-decoration: underline;">$1</a>');

    return html;
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}



// Reset session variables
async function resetDeveloperSession() {
    try {
        const response = await fetch(`/api/reset/${MOCK_USER_ID}`, { method: "POST" });
        const result = await response.json();

        // Re-initialize chat greeting and refresh logs view
        initializeChat();

        // Show status feedback
        console.info(result.message);
    } catch (e) {
        console.error("Failed to reset session:", e);
    }
}
