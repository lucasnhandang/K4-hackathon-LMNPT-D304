# custom_styles.py
"""
CSS styles for 100% authentic Discord Dark Theme UI in NiceGUI
Includes AI Tracepath & Tool Execution styling
"""

DISCORD_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=gg+sans:wght@400;500;600;700&family=Sora:wght@600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Lora:ital,wght@1,500&display=swap" rel="stylesheet">

<style>
  :root {
    /* Authentic Discord Dark Colors */
    --bg-servers: #1e1f22;
    --bg-sidebar: #2b2d31;
    --bg-chat: #313338;
    --bg-input: #383a40;
    --bg-modifier-hover: rgba(255, 255, 255, 0.07);
    --bg-modifier-active: rgba(255, 255, 255, 0.12);
    --bg-modifier-selected: rgba(255, 255, 255, 0.1);
    --bg-embed: #2b2d31;

    --text-normal: #dbdee1;
    --text-muted: #949ba4;
    --text-faint: #80848e;
    --text-heading: #f2f3f5;
    --text-link: #00a8fc;

    --brand: #5865f2;
    --brand-hover: #4752c4;
    --brand-mention-bg: rgba(88, 101, 242, 0.15);
    --brand-mention-text: #c9cdfb;

    --green: #23a55a;
    --red: #f23f43;
    --amber: #f0b232;
    --cyan: #22d3ee;
    --purple: #8b6cf7;

    --font-discord: 'Inter', 'gg sans', system-ui, -apple-system, sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
    --font-quote: 'Lora', Georgia, serif;
  }

  * {
    box-sizing: border-box;
  }

  body {
    font-family: var(--font-discord) !important;
    background-color: var(--bg-servers) !important;
    color: var(--text-normal) !important;
    margin: 0;
    padding: 0;
    overflow: hidden;
  }

  /* Custom Discord Scrollbars */
  ::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }
  ::-webkit-scrollbar-track {
    background: #2b2d31;
  }
  ::-webkit-scrollbar-thumb {
    background: #1a1b1e;
    border-radius: 4px;
  }
  ::-webkit-scrollbar-thumb:hover {
    background: #111214;
  }

  /* NiceGUI Layout Overrides */
  .nicegui-content {
    padding: 0 !important;
    max-width: none !important;
    width: 100vw;
    height: 100vh;
  }
  .q-layout, .q-page-container, .q-page {
    background-color: var(--bg-servers) !important;
  }

  /* Server List Column (72px) */
  .servers-column {
    width: 72px;
    background-color: var(--bg-servers);
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 12px 0;
    gap: 8px;
    height: 100vh;
    flex-shrink: 0;
  }

  .server-pill-icon {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background-color: var(--bg-chat);
    color: var(--text-heading);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-weight: 700;
    font-size: 15px;
    transition: all 0.2s ease;
    position: relative;
  }

  .server-pill-icon:hover {
    border-radius: 16px;
    background-color: var(--brand);
    color: white;
  }

  .server-pill-icon.active {
    border-radius: 16px;
    background: linear-gradient(135deg, #8b6cf7, #5865f2);
    color: white;
  }

  .server-separator {
    width: 32px;
    height: 2px;
    background-color: var(--bg-modifier-hover);
    border-radius: 1px;
    margin: 4px 0;
  }

  /* Channel Sidebar (240px) */
  .channels-sidebar {
    width: 240px;
    background-color: var(--bg-sidebar);
    display: flex;
    flex-direction: column;
    height: 100vh;
    border-top-left-radius: 8px;
    flex-shrink: 0;
  }

  .sidebar-header {
    height: 48px;
    padding: 0 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-weight: 700;
    font-size: 14.5px;
    color: var(--text-heading);
    border-bottom: 1px solid rgba(0, 0, 0, 0.2);
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
    cursor: pointer;
  }

  .sidebar-header:hover {
    background-color: var(--bg-modifier-hover);
  }

  .channel-category {
    padding: 16px 8px 4px 14px;
    font-size: 11px;
    font-weight: 700;
    color: var(--text-faint);
    text-transform: uppercase;
    letter-spacing: 0.2px;
    display: flex;
    align-items: center;
    gap: 4px;
    cursor: pointer;
  }

  .channel-category:hover {
    color: var(--text-muted);
  }

  .channel-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 8px 6px 12px;
    margin: 1px 8px;
    border-radius: 4px;
    color: var(--text-muted);
    cursor: pointer;
    font-weight: 500;
    font-size: 14px;
    transition: background 0.15s ease, color 0.15s ease;
  }

  .channel-item.active {
    background-color: var(--bg-modifier-selected);
    color: var(--text-heading);
  }

  .channel-item:hover:not(.active) {
    background-color: var(--bg-modifier-hover);
    color: var(--text-normal);
  }

  .channel-name-box {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .badge-pill {
    background-color: var(--red);
    color: white;
    font-size: 10px;
    font-weight: 700;
    padding: 1px 6px;
    border-radius: 8px;
  }

  /* Discord User Status Footer */
  .sidebar-user-footer {
    height: 52px;
    background-color: #232428;
    padding: 0 8px 0 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .user-info-box {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    padding: 4px;
    border-radius: 4px;
  }

  .user-info-box:hover {
    background-color: var(--bg-modifier-hover);
  }

  .avatar-status-wrapper {
    position: relative;
    width: 32px;
    height: 32px;
  }

  .avatar-img {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: linear-gradient(135deg, #2fbf71, #1c8f52);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 12px;
  }

  .status-dot-green {
    position: absolute;
    bottom: -1px;
    right: -1px;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background-color: var(--green);
    border: 2px solid #232428;
  }

  .user-text-details {
    display: flex;
    flex-direction: column;
    line-height: 1.2;
  }

  .user-display-name {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-heading);
  }

  .user-sub-status {
    font-size: 11px;
    color: var(--text-muted);
  }

  .user-icon-btn {
    color: var(--text-muted);
    padding: 4px;
    border-radius: 4px;
    cursor: pointer;
  }

  .user-icon-btn:hover {
    color: var(--text-heading);
    background-color: var(--bg-modifier-hover);
  }

  /* Main Chat Area */
  .chat-area {
    flex: 1;
    display: flex;
    flex-direction: column;
    background-color: var(--bg-chat);
    height: 100vh;
    min-width: 0;
  }

  .chat-header {
    height: 48px;
    padding: 0 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid rgba(0, 0, 0, 0.2);
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
    flex-shrink: 0;
    background-color: var(--bg-chat);
  }

  .chat-header-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 700;
    font-size: 15px;
    color: var(--text-heading);
  }

  .chat-header-desc {
    font-size: 12.5px;
    color: var(--text-muted);
    font-weight: 400;
    border-left: 1px solid rgba(255, 255, 255, 0.1);
    padding-left: 10px;
    margin-left: 4px;
  }

  .chat-header-tools {
    display: flex;
    align-items: center;
    gap: 12px;
    color: var(--text-muted);
  }

  .chat-header-icon {
    cursor: pointer;
  }
  .chat-header-icon:hover {
    color: var(--text-heading);
  }

  /* Messages View */
  .messages-container {
    flex: 1;
    padding: 16px 20px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .discord-msg-row {
    display: flex;
    gap: 16px;
    padding: 2px 0;
    position: relative;
  }

  .discord-msg-row:hover {
    background-color: rgba(2, 2, 2, 0.06);
  }

  .msg-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 13px;
    color: white;
    flex-shrink: 0;
  }

  .msg-avatar.bot-avatar {
    background: linear-gradient(135deg, #5865f2, #8b6cf7);
  }

  .msg-avatar.user-avatar {
    background: linear-gradient(135deg, #2fbf71, #1c8f52);
  }

  .msg-content-wrapper {
    flex: 1;
    min-width: 0;
  }

  .msg-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 3px;
  }

  .author-name {
    font-weight: 600;
    color: var(--text-heading);
    font-size: 15px;
    cursor: pointer;
  }

  .author-name:hover {
    text-decoration: underline;
  }

  .bot-app-badge {
    background-color: var(--brand);
    color: white;
    font-size: 9.5px;
    font-weight: 700;
    padding: 1px 4px;
    border-radius: 3px;
    text-transform: uppercase;
  }

  .msg-timestamp {
    font-size: 11px;
    color: var(--text-faint);
  }

  .msg-text-body {
    font-size: 14.5px;
    line-height: 1.5;
    color: var(--text-normal);
    word-break: break-word;
  }

  .mention-pill {
    background-color: var(--brand-mention-bg);
    color: var(--brand-mention-text);
    padding: 0 4px;
    border-radius: 3px;
    font-weight: 600;
    cursor: pointer;
  }

  .mention-pill:hover {
    background-color: var(--brand);
    color: white;
  }

  /* Discord Reply Line */
  .reply-context-line {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: var(--text-muted);
    margin-bottom: 2px;
    padding-left: 2px;
  }

  /* Embed Card */
  .discord-embed {
    background-color: var(--bg-embed);
    border-radius: 4px;
    border-left: 4px solid var(--brand);
    padding: 12px 14px;
    margin-top: 8px;
    max-width: 540px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .discord-embed.warning-embed {
    border-left-color: var(--amber);
  }

  .discord-embed.success-embed {
    border-left-color: var(--green);
  }

  .discord-embed.escalate-embed {
    border-left-color: var(--red);
  }

  .embed-source-pill {
    background: rgba(0, 0, 0, 0.2);
    padding: 6px 10px;
    border-radius: 4px;
    font-size: 12px;
    color: var(--text-muted);
  }

  .embed-source-pill.escalate-pill {
    background: rgba(242, 63, 67, 0.15);
    color: #fca5a5;
  }

  /* ==================== AI TRACEPATH BOX STYLING ==================== */
  .discord-tracepath-box {
    background: #1e1f22;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    padding: 10px 12px;
    margin-top: 8px;
    font-family: var(--font-discord);
    font-size: 12px;
  }

  .trace-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    cursor: pointer;
    user-select: none;
    padding-bottom: 6px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  }

  .trace-header-left {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    color: #a78bfa;
    font-size: 12.5px;
  }

  .trace-metrics-group {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
  }

  .trace-metric-badge {
    background: rgba(139, 108, 247, 0.15);
    color: #c4b5fd;
    padding: 2px 7px;
    border-radius: 4px;
    font-family: var(--font-mono);
    font-weight: 500;
  }

  .trace-tools-flow {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px;
    margin-top: 8px;
  }

  .trace-tool-pill {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: var(--text-normal);
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 11.5px;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 5px;
  }

  .trace-tool-pill .tool-icon {
    font-size: 12px;
  }

  .trace-tool-arrow {
    color: var(--text-faint);
    font-size: 10px;
  }

  .trace-steps-list {
    margin-top: 8px;
    padding-top: 6px;
    border-top: 1px dashed rgba(255, 255, 255, 0.08);
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .trace-step-item {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-muted);
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .trace-step-item::before {
    content: '❯';
    color: var(--cyan);
    font-size: 9px;
  }

  /* Action Buttons Grid */
  .options-flex-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 6px;
  }

  .disc-btn {
    background-color: var(--bg-input) !important;
    color: var(--text-heading) !important;
    padding: 5px 12px !important;
    border-radius: 3px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    text-transform: none !important;
    transition: background 0.15s ease !important;
  }

  .disc-btn:hover {
    background-color: #4e5058 !important;
  }

  .disc-btn-success {
    background-color: rgba(35, 165, 90, 0.2) !important;
    color: #4ade80 !important;
  }
  .disc-btn-success:hover {
    background-color: rgba(35, 165, 90, 0.35) !important;
  }

  .disc-btn-danger {
    background-color: rgba(242, 63, 67, 0.2) !important;
    color: #f87171 !important;
  }
  .disc-btn-danger:hover {
    background-color: rgba(242, 63, 67, 0.35) !important;
  }

  /* Discord Reaction Pills */
  .reaction-bar {
    display: flex;
    gap: 6px;
    margin-top: 6px;
  }

  .reaction-pill {
    background-color: var(--bg-sidebar);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    padding: 2px 8px;
    font-size: 12px;
    color: var(--text-muted);
    display: flex;
    align-items: center;
    gap: 4px;
    cursor: pointer;
  }

  .reaction-pill:hover {
    background-color: var(--bg-input);
    color: var(--text-normal);
  }

  /* Discord Input Bar */
  .chat-input-wrapper {
    padding: 0 16px 24px;
    background-color: var(--bg-chat);
    flex-shrink: 0;
  }

  .input-bar-inner {
    background-color: var(--bg-input);
    border-radius: 8px;
    padding: 8px 16px;
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .attachment-btn {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background-color: #4e5058;
    color: var(--bg-chat);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-weight: 700;
    font-size: 16px;
  }

  .attachment-btn:hover {
    background-color: var(--text-heading);
  }

  /* Modal Customization */
  .discord-dialog {
    background: var(--bg-sidebar) !important;
    color: var(--text-normal) !important;
    border-radius: 8px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    width: 90vw;
    max-width: 500px;
  }
</style>
"""
