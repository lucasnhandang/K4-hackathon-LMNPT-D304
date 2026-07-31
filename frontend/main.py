# main.py
"""
NiceGUI Application: 100% Authentic Discord UI for Student Assistant Bot
"""

from datetime import datetime
import asyncio
import sys
import os
import re
from typing import List, Dict, Any

from nicegui import ui

from custom_styles import DISCORD_CSS
from ai_router import call_backend_api_async, handle_option_selection, KNOWLEDGE_BASE

# Options that are pure UI feedback (not a real question for the backend) stay local.
LOCAL_ONLY_OPTIONS = {"FEEDBACK_RESOLVED", "FEEDBACK_WRONG"}

# Enable static Discord styles & fonts
ui.add_head_html(DISCORD_CSS)
ui.add_body_html('<script>function scrollToBottom(){ setTimeout(() => { const el = document.getElementById("chat-scroll"); if(el) el.scrollTop = el.scrollHeight; }, 50); }</script>')

class DiscordChatApp:
    def __init__(self):
        self.messages: List[Dict[str, Any]] = []
        self.is_typing: bool = False
        self.input_element = None
        self.messages_container = None
        
        # Initial Clean Welcome State (Mock messages removed)
        self.reset_messages()
        
    def reset_messages(self):
        self.messages = [
            {
                "sender": "bot",
                "name": "Trợ lý Kute",
                "time": self.get_time_str(),
                "text": "Chào bạn! Mình là **Trợ lý Kute** (K4 AI Thực Chiến). Nếu bạn có thắc mắc gì về bài tập, deadline hoặc quy chế môn học, hãy nhập câu hỏi bên dưới nhé! 🚀",
                "payload": None
            }
        ]

    @staticmethod
    def get_time_str() -> str:
        return f"Hôm nay lúc {datetime.now().strftime('%H:%M')}"

    @staticmethod
    def _schedule(coro):
        """Run a coroutine on the current NiceGUI client's event loop."""
        asyncio.create_task(coro)

    def _build_history_payload(self) -> List[Dict[str, str]]:
        """Turn the rendered message log into a plain role/content history for the backend."""
        history = []
        for msg in self.messages[-10:]:
            role = "assistant" if msg["sender"] == "bot" else "user"
            text = msg["text"]
            if role == "user":
                text = text.replace("@Trợ lý Kute ", "", 1)
            history.append({"role": role, "content": text})
        return history

    def send_user_text(self, text: str):
        text = text.strip()
        if not text or self.is_typing:
            return
        
        formatted_text = text
        if not text.startswith("@"):
            formatted_text = f"@Trợ lý Kute {text}"
            
        user_name = "Học viên K4"
        history = self._build_history_payload()

        # Append User Message
        self.messages.append({
            "sender": "user",
            "name": user_name,
            "time": self.get_time_str(),
            "text": formatted_text,
            "payload": None
        })

        if self.input_element:
            self.input_element.value = ""

        self.update_chat_ui()

        # Trigger Bot Response
        self.is_typing = True
        self.update_chat_ui()

        ui.timer(0.6, lambda: self._schedule(self.process_bot_reply(text, user_name, history)), once=True)

    async def process_bot_reply(self, raw_user_text: str, reply_to_name: str, history: List[Dict[str, str]] = None):
        route_res = await call_backend_api_async(raw_user_text, history)
        self.is_typing = False

        self.messages.append({
            "sender": "bot",
            "name": "Trợ lý Kute",
            "time": self.get_time_str(),
            "text": route_res.get("message", ""),
            "reply_to": reply_to_name,
            "payload": route_res
        })
        self.update_chat_ui()

    def handle_option_click(self, opt_value: str, opt_label: str):
        if self.is_typing:
            return
            
        if opt_value == "VIEW_SOURCE":
            self.open_source_modal()
            return
            
        if opt_value == "FOCUS_INPUT":
            if self.input_element:
                self.input_element.run_method("focus")
            return

        clean_label = opt_label.replace("📄 ", "").replace("✅ ", "").replace("📅 ", "").replace("❓ ", "").replace("↺ ", "").replace("✍ ", "").replace("⚠️ ", "")
        user_name = "Học viên K4"
        history = self._build_history_payload()

        self.messages.append({
            "sender": "user",
            "name": user_name,
            "time": self.get_time_str(),
            "text": f"@Trợ lý Kute {clean_label}",
            "payload": None
        })
        self.update_chat_ui()

        self.is_typing = True
        self.update_chat_ui()

        val_upper = opt_value.upper()
        if opt_value in LOCAL_ONLY_OPTIONS or "MOD" in val_upper:
            # Pure UI feedback / forced escalation: handled locally, no backend round-trip.
            ui.timer(0.5, lambda: self.process_option_reply(opt_value, user_name), once=True)
        else:
            # A follow-up / clarification choice: continue the real conversation with
            # the backend, sending the button's label just like typed text so the
            # backend's session-based clarification state picks it up.
            ui.timer(0.5, lambda: self._schedule(self.process_bot_reply(clean_label, user_name, history)), once=True)

    def process_option_reply(self, opt_value: str, reply_to_name: str):
        route_res = handle_option_selection(opt_value)
        self.is_typing = False
        
        self.messages.append({
            "sender": "bot",
            "name": "Trợ lý Kute",
            "time": self.get_time_str(),
            "text": route_res.get("message", ""),
            "reply_to": reply_to_name,
            "payload": route_res
        })
        self.update_chat_ui()

    def open_source_modal(self):
        kb = KNOWLEDGE_BASE["weekly_report"]
        with ui.dialog() as dialog, ui.card().classes("discord-dialog q-pa-md"):
            with ui.row().classes("items-center justify-between w-full q-mb-sm"):
                ui.label("📄 Căn cứ & Nguồn chính thức").classes("text-weight-bold text-subtitle1 text-white")
                ui.button(icon="close", on_click=dialog.close).props("flat round dense text-color=grey-5")
            
            with ui.column().classes("w-full gap-2 text-body2"):
                ui.html(f"<div><strong style='color: var(--text-heading);'>Chủ đề:</strong> {kb['title']}</div>")
                ui.html(f"<div><strong style='color: var(--text-heading);'>Nguồn phát hành:</strong> {kb['source']}</div>")
                ui.html(f"""
                <div style="margin-top: 10px;">
                    <strong style="color: var(--text-heading);">Trích dẫn nguyên văn:</strong>
                    <blockquote style="font-family: var(--font-quote); font-style: italic; border-left: 3px solid var(--brand); padding-left: 10px; margin-top: 6px; color: var(--text-heading); font-size: 13.5px;">
                        "{kb['quote']}"
                    </blockquote>
                </div>
                """)
        dialog.open()

    def render_msg_text(self, text: str) -> str:
        formatted = re.sub(r'(@Trợ lý Kute|@Trợ lý Học viên|@Mod|@Mentor)', r'<span class="mention-pill">\1</span>', text)
        formatted = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', formatted)
        return formatted

    def render_tracepath_html(self, trace_data: Dict[str, Any]) -> str:
        if not trace_data:
            return ""
            
        latency = trace_data.get("latency_ms", 120)
        confidence = trace_data.get("confidence", 0.95)
        intent = trace_data.get("intent", "general_query")
        tools = trace_data.get("tools_used", [])
        steps = trace_data.get("steps", [])
        
        tools_html = ""
        for i, t in enumerate(tools):
            name = t.get("name", "Tool")
            icon = t.get("icon", "🔧")
            tools_html += f'<span class="trace-tool-pill"><span class="tool-icon">{icon}</span> {name}</span>'
            if i < len(tools) - 1:
                tools_html += '<span class="trace-tool-arrow">➔</span>'

        steps_html = ""
        for s in steps:
            steps_html += f'<div class="trace-step-item">{s}</div>'

        return f'''
        <div class="discord-tracepath-box">
            <div class="trace-header">
                <div class="trace-header-left">
                    <span>⚡ AI Tracepath & Tool Execution</span>
                </div>
                <div class="trace-metrics-group">
                    <span class="trace-metric-badge">⏱️ {latency}ms</span>
                    <span class="trace-metric-badge">🎯 {int(confidence * 100)}% conf</span>
                    <span class="trace-metric-badge">🔍 intent: {intent}</span>
                </div>
            </div>
            
            <div class="trace-tools-flow">
                {tools_html}
            </div>
            
            <div class="trace-steps-list">
                {steps_html}
            </div>
        </div>
        '''

    def update_chat_ui(self):
        if not self.messages_container:
            return
        
        self.messages_container.clear()
        
        with self.messages_container:
            for msg in self.messages:
                is_bot = (msg["sender"] == "bot")
                
                with ui.element("div").classes("discord-msg-row"):
                    if is_bot and "reply_to" in msg:
                        ui.html(f'''
                        <div class="reply-context-line" style="position: absolute; top: -14px; left: 24px;">
                            <span style="color: var(--text-muted);">┌─</span> 
                            <span>@<strong>{msg["reply_to"]}</strong></span>
                        </div>
                        ''')
                        
                    avatar_class = "bot-avatar" if is_bot else "user-avatar"
                    avatar_text = "BOT" if is_bot else "HV"
                    ui.html(f'<div class="msg-avatar {avatar_class}">{avatar_text}</div>')
                    
                    with ui.element("div").classes("msg-content-wrapper"):
                        with ui.element("div").classes("msg-header"):
                            ui.label(msg["name"]).classes("author-name")
                            if is_bot:
                                ui.html('<span class="bot-app-badge">APP</span>')
                            ui.label(msg["time"]).classes("msg-timestamp")
                        
                        ui.html(f'<div class="msg-text-body">{self.render_msg_text(msg["text"])}</div>')
                        
                        payload = msg.get("payload")
                        if payload:
                            embed_type = payload.get("embed_type", "discord-embed")
                            with ui.element("div").classes(f"discord-embed {embed_type}"):
                                if "title" in payload:
                                    ui.html(f'<div style="font-weight: 600; color: var(--text-heading);">{payload["title"]}</div>')
                                    
                                if "escalate_tag" in payload:
                                    ui.html(f'''
                                    <div class="embed-source-pill escalate-pill">
                                        <strong>{payload["escalate_tag"]}:</strong> {payload.get("escalate_detail", "")}
                                    </div>
                                    ''')
                                    
                                if "source_info" in payload:
                                    ui.html(f'''
                                    <div class="embed-source-pill">
                                        💡 {payload["source_info"]}
                                    </div>
                                    ''')
                                    
                                opts = payload.get("options", [])
                                if opts:
                                    with ui.element("div").classes("options-flex-grid"):
                                        for opt in opts:
                                            btn_cls = f"disc-btn {opt.get('class', '')}"
                                            ui.button(
                                                opt["label"],
                                                on_click=lambda o=opt: self.handle_option_click(o["value"], o["label"])
                                            ).classes(btn_cls).props("no-caps unelevated dense")

                                trace_data = payload.get("tracepath")
                                if trace_data:
                                    ui.html(self.render_tracepath_html(trace_data))

                        # Reactions (Rendered dynamically if present in message data)
                        reactions = msg.get("reactions", [])
                        if reactions:
                            r_html = '<div class="reaction-bar">' + ''.join([f'<span class="reaction-pill">{r}</span>' for r in reactions]) + '</div>'
                            ui.html(r_html)

            if self.is_typing:
                with ui.element("div").classes("discord-msg-row"):
                    ui.html('<div class="msg-avatar bot-avatar">BOT</div>')
                    with ui.element("div").classes("msg-content-wrapper"):
                        with ui.element("div").classes("msg-header"):
                            ui.label("Trợ lý Kute").classes("author-name")
                            ui.html('<span class="bot-app-badge">APP</span>')
                        ui.html('<div style="color: var(--text-muted); font-size: 13.5px; font-style: italic;">Trợ lý Kute đang gõ câu trả lời...</div>')

        try:
            if ui.context.client and ui.context.client.has_socket_connection:
                ui.run_javascript('if(typeof scrollToBottom === "function") scrollToBottom();')
        except Exception:
            pass

    def build_ui(self):
        with ui.row().classes("w-full no-wrap").style("height: 100vh; overflow: hidden; margin: 0; padding: 0;"):
            
            # 1. SERVER COLUMN (72px)
            with ui.element("div").classes("servers-column"):
                ui.html('''
                <div class="server-pill-icon">
                    <svg width="28" height="20" viewBox="0 0 28 20" fill="currentColor">
                        <path d="M23.0212 1.67671C21.2107 0.838576 19.2647 0.224424 17.232 0C16.9556 0.496954 16.6436 1.14486 16.4253 1.66014C14.2613 1.33647 12.1066 1.33647 9.972 1.66014C9.75373 1.14486 9.432 0.496954 9.1556 0C7.11333 0.224424 5.16733 0.847938 3.3568 1.67671C-0.306133 7.15831 -0.697067 12.497 0.2212 17.7475C2.65067 19.5398 4.99653 20.6295 7.3032 21.3411C7.87307 20.5638 8.38453 19.7431 8.83147 18.8783C7.9944 18.5638 7.1896 18.1728 6.4208 17.7007C6.62187 17.5539 6.81813 17.401 7.0096 17.2471C11.5877 19.3491 16.5515 19.3491 21.0715 17.2471C21.263 17.401 21.4592 17.5539 21.6603 17.7007C20.8915 18.1728 20.0867 18.5638 19.2496 18.8783C19.6965 19.7431 20.208 20.5638 20.7779 21.3411C23.0845 20.6295 25.4304 19.5398 27.8599 17.7475C28.9483 10.9416 26.0123 5.64259 23.0212 1.67671Z"/>
                    </svg>
                </div>
                ''')
                ui.html('<div class="server-separator"></div>')
                
                ui.html('''
                <div class="server-pill-icon active" title="AI20K Build Phase — Cohort 3 & 4">
                    <span>AI</span>
                </div>
                ''')
                
                ui.html('<div class="server-pill-icon" title="VinUni Hackathon"><span>VU</span></div>')
                ui.html('<div class="server-pill-icon" title="Thêm máy chủ" style="color: var(--green);"><span>+</span></div>')
                ui.html('<div class="server-pill-icon" title="Khám phá" style="color: var(--green);"><span>🧭</span></div>')

            # 2. CHANNELS SIDEBAR (240px)
            with ui.element("div").classes("channels-sidebar"):
                with ui.element("div").classes("sidebar-header"):
                    ui.label("AI20K Build Phase...").classes("text-weight-bold")
                    ui.html('<span style="font-size: 12px; color: var(--text-muted);">⌵</span>')
                
                with ui.element("div").classes("w-full").style("flex: 1; overflow-y: auto; padding-top: 8px;"):
                    ui.html('<div class="channel-category"><span>˅</span> BUILD</div>')
                    ui.html('<div class="channel-item"><div class="channel-name-box"><span>📣</span> <span>thông-báo</span></div></div>')
                    ui.html('<div class="channel-item"><div class="channel-name-box"><span>📂</span> <span>tài-nguyên</span></div></div>')
                    
                    ui.html('<div class="channel-category"><span>˅</span> CỘNG ĐỒNG</div>')
                    ui.html('<div class="channel-item"><div class="channel-name-box"><span>💬</span> <span>chung</span></div></div>')
                    ui.html('<div class="channel-item"><div class="channel-name-box"><span>🙋</span> <span>hỏi-đáp</span></div><span class="badge-pill">9</span></div>')
                    ui.html('<div class="channel-item"><div class="channel-name-box"><span>💡</span> <span>chia-sẻ</span></div><span class="badge-pill">9</span></div>')
                    ui.html('<div class="channel-item"><div class="channel-name-box"><span>📚</span> <span>bài-học</span></div><span class="badge-pill">9</span></div>')

                    ui.html('<div class="channel-category"><span>˅</span> BOT & TIỆN ÍCH</div>')
                    ui.html('<div class="channel-item"><div class="channel-name-box"><span>🤖</span> <span>activity</span></div></div>')
                    ui.html('<div class="channel-item"><div class="channel-name-box"><span>🤖</span> <span>gõ-commands</span></div></div>')

                    ui.html('<div class="channel-category"><span>˅</span> TICKETS</div>')
                    ui.html('<div class="channel-item"><div class="channel-name-box"><span>🎫</span> <span>các-vấn-đề-khác</span></div></div>')
                    ui.html('<div class="channel-item"><div class="channel-name-box"><span>🎫</span> <span>build-phase-tickets</span></div></div>')

                    ui.html('<div class="channel-category"><span>˅</span> THẢO LUẬN</div>')
                    ui.html('<div class="channel-item active"><div class="channel-name-box"><span>💬</span> <span>gỡ-vướng-học-tập</span></div></div>')
                    ui.html('<div class="channel-item"><div class="channel-name-box"><span>💬</span> <span>thảo-luận</span></div></div>')

                with ui.element("div").classes("sidebar-user-footer"):
                    with ui.element("div").classes("user-info-box"):
                        ui.html('''
                        <div class="avatar-status-wrapper">
                            <div class="avatar-img">HV</div>
                            <div class="status-dot-green"></div>
                        </div>
                        ''')
                        with ui.element("div").classes("user-text-details"):
                            ui.label("Học viên K4").classes("user-display-name")
                            ui.label("Trực tuyến").classes("user-sub-status")
                    
                    with ui.row().classes("items-center gap-1"):
                        ui.html('<span class="user-icon-btn" title="Mic">🎤</span>')
                        ui.html('<span class="user-icon-btn" title="Tai nghe">🎧</span>')
                        ui.html('<span class="user-icon-btn" title="Cài đặt">⚙️</span>')

            # 3. MAIN CHAT AREA
            with ui.element("div").classes("chat-area"):
                with ui.element("div").classes("chat-header"):
                    with ui.element("div").classes("chat-header-title"):
                        ui.html('<span style="color: var(--text-faint); font-weight: 700; font-size: 18px;">#</span>')
                        ui.label("gỡ-vướng-học-tập").classes("text-weight-bold")
                        ui.label("Hỏi đáp thắc mắc bài tập & logistics khóa học").classes("chat-header-desc")
                    
                    with ui.element("div").classes("chat-header-tools"):
                        ui.html('<span class="chat-header-icon" title="Thông báo">🔔</span>')
                        ui.html('<span class="chat-header-icon" title="Ghim">📌</span>')
                        ui.html('<span class="chat-header-icon" title="Danh sách thành viên">👥</span>')
                        ui.html('''
                        <div style="background: #1e1f22; border-radius: 4px; padding: 2px 8px; font-size: 12px; display: flex; align-items: center; gap: 6px;">
                            <span>Tìm kiếm</span> 🔍
                        </div>
                        ''')

                self.messages_container = ui.element("div").classes("messages-container")
                self.messages_container.props('id="chat-scroll"')
                
                # Initial render
                self.update_chat_ui()

                with ui.element("div").classes("chat-input-wrapper"):
                    with ui.element("div").classes("input-bar-inner"):
                        ui.html('<div class="attachment-btn" title="Tải tệp lên">+</div>')
                        
                        self.input_element = ui.input(
                            placeholder='Gửi tin nhắn trên "# gỡ-vướng-học-tập"'
                        ).props("borderless dense dark").classes("w-full text-white").style("font-size: 14.5px;")
                        
                        self.input_element.on("keydown.enter", lambda: self.send_user_text(self.input_element.value))
                        
                        with ui.row().classes("items-center gap-2").style("color: var(--text-muted); font-size: 18px; cursor: pointer;"):
                            ui.html('<span title="Quà">🎁</span>')
                            ui.html('<span title="GIF" style="font-weight: 800; font-size: 12px; background: #4e5058; padding: 1px 4px; border-radius: 3px; color: white;">GIF</span>')
                            ui.html('<span title="Biểu cảm">😃</span>')

# Initialize and run App
def main():
    chat_app = DiscordChatApp()
    chat_app.build_ui()

if __name__ in {"__main__", "__mp_main__"}:
    port = int(os.environ.get("PORT", 8080))
    main()
    ui.run(title="Discord — # gỡ-vướng-học-tập", port=port, reload=False, dark=True)
