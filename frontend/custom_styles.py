# custom_styles.py
"""
CSS styles for a polished Discord-inspired Dark Theme in NiceGUI
Includes AI Tracepath & Tool Execution styling

v2: softer/rounder corners throughout, layered gradients & glow shadows,
subtle glass effect on cards, richer hover/active states.
"""

DISCORD_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=gg+sans:wght@400;500;600;700&family=Sora:wght@600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Lora:ital,wght@1,500&display=swap" rel="stylesheet">

<style>
  :root {
    /* Base Discord Dark Colors */
    --bg-servers: #17181b;
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
    --brand-2: #8b6cf7;
    --brand-hover: #4752c4;
    --brand-mention-bg: rgba(88, 101, 242, 0.18);
    --brand-mention-text: #c9cdfb;

    --green: #23a55a;
    --green-2: #3ddc84;
    --red: #f23f43;
    --red-2: #ff6b6e;
    --amber: #f0b232;
    --amber-2: #ffce54;
    --cyan: #22d3ee;
    --purple: #8b6cf7;

    /* New: layered gradients & elevation tokens */
    --grad-brand: linear-gradient(135deg, var(--brand-2), var(--brand) 60%);
    --grad-green: linear-gradient(135deg, var(--green-2), var(--green) 70%);
    --grad-red: linear-gradient(135deg, var(--red-2), var(--red) 70%);
    --grad-app-bg: radial-gradient(1200px 600px at 15% -10%, rgba(88,101,242,0.16), transparent 60%),
                   radial-gradient(900px 500px at 100% 110%, rgba(139,108,247,0.10), transparent 55%),
                   var(--bg-servers);

    --radius-xs: 6px;
    --radius-sm: 10px;
    --radius-md: 14px;
    --radius-lg: 18px;
    --radius-xl: 24px;
    --radius-pill: 999px;

    --shadow-sm: 0 1px 2px rgba(0,0,0,0.25);
    --shadow-md: 0 4px 16px rgba(0,0,0,0.28), 0 1px 3px rgba(0,0,0,0.3);
    --shadow-lg: 0 12px 36px rgba(0,0,0,0.38), 0 2px 8px rgba(0,0,0,0.25);
    --shadow-glow-brand: 0 4px 20px rgba(88,101,242,0.35);
    --shadow-glow-green: 0 4px 16px rgba(35,165,90,0.3);
    --shadow-glow-red: 0 4px 16px rgba(242,63,67,0.3);

    --font-discord: 'Inter', 'gg sans', system-ui, -apple-system, sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
    --font-quote: 'Lora', Georgia, serif;
  }

  * {
    box-sizing: border-box;
  }

  body {
    font-family: var(--font-discord) !important;
    background: var(--grad-app-bg) !important;
    color: var(--text-normal) !important;
    margin: 0;
    padding: 0;
    overflow: hidden;
  }

  /* Custom rounded gradient scrollbars */
  ::-webkit-scrollbar {
    width: 9px;
    height: 9px;
  }
  ::-webkit-scrollbar-track {
    background: transparent;
  }
  ::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, #4e5058, #1a1b1e);
    border-radius: var(--radius-pill);
    border: 2px solid transparent;
    background-clip: padding-box;
  }
  ::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(180deg, #6b6e76, #111214);
    background-clip: padding-box;
  }

  /* NiceGUI Layout Overrides */
  .nicegui-content {
    padding: 0 !important;
    max-width: none !important;
    width: 100vw;
    height: 100vh;
  }
  .q-layout, .q-page-container, .q-page {
    background: transparent !important;
  }

  /* Server List Column (72px) */
  .servers-column {
    width: 78px;
    background: linear-gradient(180deg, #1c1d20, #101113);
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 16px 0;
    gap: 10px;
    height: 100vh;
    flex-shrink: 0;
    box-shadow: inset -1px 0 0 rgba(255,255,255,0.04);
  }

  .server-pill-icon {
    width: 48px;
    height: 48px;
    border-radius: var(--radius-xl);
    background-color: var(--bg-chat);
    color: var(--text-heading);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-weight: 700;
    font-size: 15px;
    transition: border-radius 0.25s cubic-bezier(.4,0,.2,1), background 0.25s ease, transform 0.15s ease, box-shadow 0.25s ease;
    position: relative;
    box-shadow: var(--shadow-sm);
  }

  .server-pill-icon:hover {
    border-radius: var(--radius-sm);
    background: var(--grad-brand);
    color: white;
    transform: translateY(-2px);
    box-shadow: var(--shadow-glow-brand);
  }

  .server-pill-icon.active {
    border-radius: var(--radius-sm);
    background: var(--grad-brand);
    color: white;
    box-shadow: var(--shadow-glow-brand);
  }

  .server-separator {
    width: 30px;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--bg-modifier-hover), transparent);
    border-radius: var(--radius-pill);
    margin: 6px 0;
  }

  /* Channel Sidebar (240px) */
  .channels-sidebar {
    width: 244px;
    background: linear-gradient(180deg, #2d2f34, #26282c);
    display: flex;
    flex-direction: column;
    height: 100vh;
    border-top-left-radius: var(--radius-lg);
    flex-shrink: 0;
    box-shadow: var(--shadow-md);
  }

  .sidebar-header {
    height: 50px;
    padding: 0 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-weight: 700;
    font-size: 14.5px;
    color: var(--text-heading);
    border-bottom: 1px solid rgba(0, 0, 0, 0.2);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
    cursor: pointer;
    border-top-left-radius: var(--radius-lg);
    transition: background 0.2s ease;
  }

  .sidebar-header:hover {
    background-color: var(--bg-modifier-hover);
  }

  .channel-category {
    padding: 16px 8px 6px 14px;
    font-size: 11px;
    font-weight: 700;
    color: var(--text-faint);
    text-transform: uppercase;
    letter-spacing: 0.4px;
    display: flex;
    align-items: center;
    gap: 4px;
    cursor: pointer;
    transition: color 0.15s ease;
  }

  .channel-category:hover {
    color: var(--text-muted);
  }

  .channel-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 7px 10px 7px 12px;
    margin: 2px 8px;
    border-radius: var(--radius-sm);
    color: var(--text-muted);
    cursor: pointer;
    font-weight: 500;
    font-size: 14px;
    transition: background 0.18s ease, color 0.18s ease, transform 0.15s ease;
  }

  .channel-item.active {
    background: linear-gradient(135deg, rgba(88,101,242,0.22), rgba(139,108,247,0.12));
    color: var(--text-heading);
    box-shadow: inset 0 0 0 1px rgba(88,101,242,0.25);
  }

  .channel-item:hover:not(.active) {
    background-color: var(--bg-modifier-hover);
    color: var(--text-normal);
    transform: translateX(2px);
  }

  .channel-name-box {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .badge-pill {
    background: var(--grad-red);
    color: white;
    font-size: 10px;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: var(--radius-pill);
    box-shadow: var(--shadow-glow-red);
  }

  /* Discord User Status Footer */
  .sidebar-user-footer {
    height: 56px;
    background: linear-gradient(180deg, #26272b, #202124);
    padding: 0 10px 0 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-radius: 0 0 0 var(--radius-lg);
  }

  .user-info-box {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    padding: 5px 6px;
    border-radius: var(--radius-sm);
    transition: background 0.15s ease;
  }

  .user-info-box:hover {
    background-color: var(--bg-modifier-hover);
  }

  .avatar-status-wrapper {
    position: relative;
    width: 34px;
    height: 34px;
  }

  .avatar-img {
    width: 34px;
    height: 34px;
    border-radius: 50%;
    background: var(--grad-green);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 12px;
    box-shadow: var(--shadow-glow-green);
  }

  .status-dot-green {
    position: absolute;
    bottom: -1px;
    right: -1px;
    width: 11px;
    height: 11px;
    border-radius: 50%;
    background-color: var(--green);
    border: 2.5px solid #202124;
  }

  .user-text-details {
    display: flex;
    flex-direction: column;
    line-height: 1.25;
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
    padding: 5px;
    border-radius: var(--radius-xs);
    cursor: pointer;
    transition: all 0.15s ease;
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
    background: linear-gradient(180deg, #34363b, #2f3136);
    height: 100vh;
    min-width: 0;
    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
    box-shadow: var(--shadow-lg);
  }

  .chat-header {
    height: 52px;
    padding: 0 18px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid rgba(0, 0, 0, 0.22);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.22);
    flex-shrink: 0;
    background: transparent;
    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
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
    border-left: 1px solid rgba(255, 255, 255, 0.12);
    padding-left: 12px;
    margin-left: 6px;
  }

  .chat-header-tools {
    display: flex;
    align-items: center;
    gap: 14px;
    color: var(--text-muted);
  }

  .chat-header-icon {
    cursor: pointer;
    padding: 4px;
    border-radius: var(--radius-xs);
    transition: all 0.15s ease;
  }
  .chat-header-icon:hover {
    color: var(--text-heading);
    background-color: var(--bg-modifier-hover);
  }

  /* Messages View */
  .messages-container {
    flex: 1;
    padding: 18px 22px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 18px;
  }

  .discord-msg-row {
    display: flex;
    gap: 16px;
    padding: 8px 10px;
    margin: -8px -10px;
    border-radius: var(--radius-md);
    position: relative;
    transition: background 0.15s ease;
  }

  .discord-msg-row:hover {
    background-color: rgba(2, 2, 2, 0.15);
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
    box-shadow: var(--shadow-sm);
  }

  .msg-avatar.bot-avatar {
    background: var(--grad-brand);
    box-shadow: var(--shadow-glow-brand);
  }

  .msg-avatar.user-avatar {
    background: var(--grad-green);
    box-shadow: var(--shadow-glow-green);
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
    background: var(--grad-brand);
    color: white;
    font-size: 9.5px;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: var(--radius-xs);
    text-transform: uppercase;
    letter-spacing: 0.3px;
  }

  .msg-timestamp {
    font-size: 11px;
    color: var(--text-faint);
  }

  .msg-text-body {
    font-size: 14.5px;
    line-height: 1.55;
    color: var(--text-normal);
    word-break: break-word;
  }

  .mention-pill {
    background-color: var(--brand-mention-bg);
    color: var(--brand-mention-text);
    padding: 1px 6px;
    border-radius: var(--radius-xs);
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .mention-pill:hover {
    background: var(--grad-brand);
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
    background: linear-gradient(160deg, rgba(255,255,255,0.035), rgba(255,255,255,0) 40%), var(--bg-embed);
    border-radius: var(--radius-md);
    border-left: 3px solid var(--brand);
    padding: 14px 16px;
    margin-top: 10px;
    max-width: 560px;
    display: flex;
    flex-direction: column;
    gap: 9px;
    box-shadow: var(--shadow-md);
  }

  .discord-embed.warning-embed {
    border-left-color: var(--amber);
    box-shadow: 0 4px 16px rgba(240,178,50,0.16), var(--shadow-sm);
  }

  .discord-embed.success-embed {
    border-left-color: var(--green);
    box-shadow: var(--shadow-glow-green);
  }

  .discord-embed.escalate-embed {
    border-left-color: var(--red);
    box-shadow: var(--shadow-glow-red);
  }

  .discord-embed.muted-embed {
    border-left-color: var(--text-faint);
    box-shadow: var(--shadow-sm);
    opacity: 0.9;
  }

  .embed-source-pill {
    background: rgba(0, 0, 0, 0.22);
    padding: 8px 12px;
    border-radius: var(--radius-sm);
    font-size: 12px;
    color: var(--text-muted);
  }

  .embed-source-pill.escalate-pill {
    background: rgba(242, 63, 67, 0.14);
    color: #fca5a5;
    box-shadow: inset 0 0 0 1px rgba(242,63,67,0.2);
  }

  /* ==================== AI TRACEPATH BOX STYLING ==================== */
  .discord-tracepath-box {
    background: linear-gradient(160deg, rgba(139,108,247,0.08), rgba(30,31,34,0.4)), #1e1f22;
    border: 1px solid rgba(167, 139, 250, 0.18);
    border-radius: var(--radius-md);
    padding: 12px 14px;
    margin-top: 10px;
    font-family: var(--font-discord);
    font-size: 12px;
    box-shadow: 0 6px 20px rgba(88,101,242,0.12);
  }

  .trace-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    cursor: pointer;
    user-select: none;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.07);
    flex-wrap: wrap;
    gap: 6px;
  }

  .trace-header-left {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    color: #b9a4fb;
    font-size: 12.5px;
  }

  .trace-metrics-group {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    flex-wrap: wrap;
  }

  .trace-metric-badge {
    background: rgba(139, 108, 247, 0.16);
    color: #c4b5fd;
    padding: 3px 8px;
    border-radius: var(--radius-pill);
    font-family: var(--font-mono);
    font-weight: 500;
    box-shadow: inset 0 0 0 1px rgba(139,108,247,0.15);
  }

  .trace-tools-flow {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px;
    margin-top: 10px;
  }

  .trace-tool-pill {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: var(--text-normal);
    padding: 4px 10px;
    border-radius: var(--radius-pill);
    font-size: 11.5px;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 5px;
    transition: all 0.15s ease;
  }

  .trace-tool-pill:hover {
    background: rgba(139, 108, 247, 0.16);
    border-color: rgba(167, 139, 250, 0.3);
  }

  .trace-tool-pill .tool-icon {
    font-size: 12px;
  }

  .trace-tool-arrow {
    color: var(--text-faint);
    font-size: 10px;
  }

  .trace-steps-list {
    margin-top: 10px;
    padding-top: 8px;
    border-top: 1px dashed rgba(255, 255, 255, 0.1);
    display: flex;
    flex-direction: column;
    gap: 5px;
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
    gap: 9px;
    margin-top: 8px;
  }

  .disc-btn {
    background-color: var(--bg-input) !important;
    color: var(--text-heading) !important;
    padding: 7px 16px !important;
    border-radius: var(--radius-pill) !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    text-transform: none !important;
    box-shadow: var(--shadow-sm) !important;
    transition: background 0.18s ease, transform 0.12s ease, box-shadow 0.18s ease !important;
  }

  .disc-btn:hover {
    background-color: #4e5058 !important;
    transform: translateY(-1px);
    box-shadow: var(--shadow-md) !important;
  }

  .disc-btn-success {
    background: linear-gradient(135deg, rgba(61,220,132,0.22), rgba(35,165,90,0.22)) !important;
    color: #4ade80 !important;
  }
  .disc-btn-success:hover {
    background: linear-gradient(135deg, rgba(61,220,132,0.35), rgba(35,165,90,0.35)) !important;
    box-shadow: var(--shadow-glow-green) !important;
  }

  .disc-btn-danger {
    background: linear-gradient(135deg, rgba(255,107,110,0.22), rgba(242,63,67,0.22)) !important;
    color: #f87171 !important;
  }
  .disc-btn-danger:hover {
    background: linear-gradient(135deg, rgba(255,107,110,0.35), rgba(242,63,67,0.35)) !important;
    box-shadow: var(--shadow-glow-red) !important;
  }

  /* Discord Reaction Pills */
  .reaction-bar {
    display: flex;
    gap: 7px;
    margin-top: 8px;
    flex-wrap: wrap;
  }

  .reaction-pill {
    background-color: var(--bg-sidebar);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: var(--radius-pill);
    padding: 3px 10px;
    font-size: 12px;
    color: var(--text-muted);
    display: flex;
    align-items: center;
    gap: 4px;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .reaction-pill:hover {
    background-color: var(--bg-input);
    color: var(--text-normal);
    transform: translateY(-1px);
    box-shadow: var(--shadow-sm);
  }

  /* Discord Input Bar */
  .chat-input-wrapper {
    padding: 0 18px 26px;
    background: transparent;
    flex-shrink: 0;
  }

  .input-bar-inner {
    background: linear-gradient(160deg, rgba(255,255,255,0.04), rgba(255,255,255,0)), var(--bg-input);
    border-radius: var(--radius-xl);
    padding: 10px 18px;
    display: flex;
    align-items: center;
    gap: 12px;
    box-shadow: var(--shadow-md), inset 0 0 0 1px rgba(255,255,255,0.04);
    transition: box-shadow 0.2s ease;
  }

  .input-bar-inner:focus-within {
    box-shadow: var(--shadow-md), 0 0 0 2px rgba(88,101,242,0.45);
  }

  .attachment-btn {
    width: 26px;
    height: 26px;
    border-radius: 50%;
    background-color: #4e5058;
    color: var(--bg-chat);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-weight: 700;
    font-size: 16px;
    transition: all 0.15s ease;
  }

  .attachment-btn:hover {
    background: var(--grad-brand);
    color: white;
    transform: rotate(90deg);
  }

  /* Modal Customization */
  .discord-dialog {
    background: linear-gradient(165deg, #313338, #2b2d31) !important;
    color: var(--text-normal) !important;
    border-radius: var(--radius-lg) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    box-shadow: var(--shadow-lg) !important;
    width: 90vw;
    max-width: 520px;
  }
</style>
"""
