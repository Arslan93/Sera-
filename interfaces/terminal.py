import os
import logging
from rich.console import Console
from rich.markdown import Markdown
from core.orchestrator import Orchestrator
from core.config import config
from core.clipboard_listener import clipboard_listener
from voice.voice_handler import voice_handler
from voice.wake_word import wake_word_listener
from skills.skill_manager import skill_manager
from skills.daily_brief_skill import GetDailyBriefTool, check_and_trigger_daily_brief
from skills.clipboard_capture_skill import file_captured_content

logger = logging.getLogger(__name__)

class TerminalInterface:
    """
    Handles the terminal-based chat, coding, and voice interface for SERA.
    """
    def __init__(self, orchestrator: Orchestrator):
        """
        Initializes the TerminalInterface.
        Args:
            orchestrator (Orchestrator): The application's central orchestrator.
        """
        self.orchestrator = orchestrator
        self.console = Console()
        self.voice_handler = voice_handler
        self.wake_listener = wake_word_listener
        self.clipboard_listener = clipboard_listener

    def start_chat(self):
        """
        Starts the interactive chat loop in the terminal.
        """
        self.console.print("[bold cyan]SERA[/bold cyan] - [dim]Personal AI Desktop & Coding Assistant[/dim]")
        self.console.print("[bold green]All Phases (1-5) Active: Brain, PC Control, Voice, Coding & Skills[/bold green]")
        self.console.print("Commands: [cyan]/help[/cyan] | [cyan]/brief[/cyan] | [cyan]/capture[/cyan] | [cyan]/voice[/cyan] | [cyan]/mic[/cyan] | [cyan]/wake[/cyan] | [cyan]/skills[/cyan]")
        self.console.print("-" * 65)

        # Optional auto-brief on start (fires once per day)
        if config.auto_brief_on_start:
            try:
                auto_brief = check_and_trigger_daily_brief()
                if auto_brief and auto_brief.get("status") == "success":
                    brief_text = auto_brief.get("brief_text", "")
                    self.console.print("\n[bold cyan]☀️ Daily Orientation Brief[/bold cyan]")
                    self.console.print(f"[bold white]{brief_text}[/bold white]\n")
                    if self.voice_handler.voice_enabled:
                        self.voice_handler.speak_async(brief_text)
            except Exception as e:
                logger.warning(f"Auto daily brief failed on startup: {e}")

        try:
            while True:
                user_input = self.console.input("[bold green]You > [/bold green]")
                if not user_input or not user_input.strip():
                    if self.voice_handler.voice_enabled:
                        self._handle_mic_input()
                    continue
                
                clean_input = user_input.strip()
                if self._handle_command(clean_input):
                    continue

                self._process_message(clean_input)

        except KeyboardInterrupt:
            self.wake_listener.stop()
            self.clipboard_listener.stop()
            self.console.print("\n[bold yellow]Exiting SERA. Goodbye![/bold yellow]")
        except Exception as e:
            self.wake_listener.stop()
            self.clipboard_listener.stop()
            logger.critical(f"A critical error occurred in the chat loop: {e}", exc_info=True)
            self.console.print(f"\n[bold red]A critical error occurred: {e}. Shutting down.[/bold red]")

    def _process_message(self, user_message: str):
        """Sends a message to the orchestrator, displays streaming output, and speaks if voice enabled."""
        full_response = ""
        with self.console.status("[italic cyan]SERA is thinking...[/italic cyan]"):
            try:
                response_iterator = self.orchestrator.handle_user_message(user_message)
                first_chunk = next(response_iterator, None)
            except Exception as e:
                logger.error(f"Error during response generation: {e}", exc_info=True)
                self.console.print(f"\n[bold red]Error: Could not get a response. Please check the logs.[/bold red]")
                return

        if first_chunk is not None:
            self.console.print("[bold blue]SERA > [/bold blue]", end="")
            self.console.out(first_chunk, end="")
            full_response += first_chunk
            for chunk in response_iterator:
                self.console.out(chunk, end="")
                full_response += chunk
            self.console.out("\n")

            # Speak response if voice is toggled on
            if self.voice_handler.voice_enabled and full_response:
                self.voice_handler.speak_async(full_response)

    def _handle_command(self, command: str) -> bool:
        """
        Handles user commands.
        """
        cmd = command.lower()
        if cmd == '/help':
            self._show_help()
            return True
        if cmd in ['/brief', '/dailybrief', '/daily-brief']:
            tool = GetDailyBriefTool()
            brief_res = tool.execute()
            brief_text = brief_res.get("brief_text", "")
            self.console.print("\n[bold cyan]☀️ SERA Daily Brief[/bold cyan]")
            self.console.print(f"[bold white]{brief_text}[/bold white]\n")
            if self.voice_handler.voice_enabled:
                self.voice_handler.speak_async(brief_text)
            return True
        if cmd == '/voice':
            is_on = self.voice_handler.toggle_voice()
            status_text = "[bold green]ON[/bold green]" if is_on else "[bold yellow]OFF[/bold yellow]"
            self.console.print(f"Voice Response Mode is now {status_text}.")
            if is_on:
                self.console.print("[dim cyan]Tip: With voice ON, simply press Enter on a blank line to speak your query![/dim cyan]")
                self.voice_handler.speak_async("Voice mode enabled. You can speak to me now.")
            return True
        if cmd in ['/mic', '/listen']:
            self._handle_mic_input()
            return True
        if cmd == '/wake':
            self._toggle_wake_word()
            return True
        if cmd == '/capture':
            self._toggle_clipboard_capture()
            return True
        if cmd.startswith('/skills'):
            parts = command.strip().split()
            if len(parts) >= 3 and parts[1].lower() == 'enable':
                skill_name = parts[2]
                if skill_manager.enable_skill(skill_name):
                    self.console.print(f"[bold green]Enabled skill plugin '{skill_name}'. Tools registered.[/bold green]")
                else:
                    self.console.print(f"[bold red]Skill '{skill_name}' not found.[/bold red]")
            elif len(parts) >= 3 and parts[1].lower() == 'disable':
                skill_name = parts[2]
                if skill_manager.disable_skill(skill_name):
                    self.console.print(f"[bold yellow]Disabled skill plugin '{skill_name}'. Tools unregistered.[/bold yellow]")
                else:
                    self.console.print(f"[bold red]Skill '{skill_name}' not found.[/bold red]")
            else:
                self._show_skills()
            return True
        if cmd == '/new':
            self.orchestrator.new_session()
            self.console.print("[bold yellow]Started a new conversation session.[/bold yellow]")
            return True
        if cmd == '/history':
            self._show_history()
            return True
        if cmd in ['/ui', '/web', '/gui']:
            import webbrowser
            import threading
            import uvicorn
            from interfaces.web_server import app
            
            def run_server():
                uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

            t = threading.Thread(target=run_server, daemon=True)
            t.start()
            self.console.print("[bold green]✨ Launched SERA Web UI at http://127.0.0.1:8000[/bold green]")
            webbrowser.open("http://127.0.0.1:8000")
            return True
        if cmd == '/clear':
            os.system('cls' if os.name == 'nt' else 'clear')
            return True
        if cmd == '/exit':
            raise KeyboardInterrupt
        return False

    def _toggle_wake_word(self):
        """Toggles background hands-free wake word listener."""
        if self.wake_listener.is_listening:
            self.wake_listener.stop()
            self.console.print("Wake Word detection is now [bold yellow]OFF[/bold yellow].")
        else:
            def on_wake_triggered():
                self.console.print("\n[bold magenta]⚡ Wake Word Detected ('Hey Sera')! Listening...[/bold magenta]")
                self._handle_mic_input()

            self.wake_listener.start(on_wake=on_wake_triggered)
            self.console.print("Wake Word detection is now [bold green]ON[/bold green]. Say [cyan]'Hey Sera'[/cyan] anytime!")
            if self.voice_handler.voice_enabled:
                self.voice_handler.speak_async("Wake word listening is active.")

    def _toggle_clipboard_capture(self):
        """Toggles background clipboard hotkey listener (Ctrl+Shift+S)."""
        if self.clipboard_listener.is_listening:
            self.clipboard_listener.stop()
            self.console.print("Clipboard Capture Hotkey listener is now [bold yellow]OFF[/bold yellow].")
        else:
            def on_capture_detected(text: str):
                result = file_captured_content(text)
                classification = result.get("classification", "content")
                dest = result.get("filed_to", "notes")
                snippet = text.split("\n")[0][:45]
                self.console.print(f"\n[bold magenta]📋 Clipboard Captured ({classification.upper()}):[/bold magenta] [italic]'{snippet}'[/italic] → filed to [cyan]{dest}[/cyan]")
                if self.voice_handler.voice_enabled:
                    self.voice_handler.speak_async(f"Captured {classification} saved.")

            success = self.clipboard_listener.start(on_capture=on_capture_detected)
            if success:
                self.console.print(f"Clipboard Capture is now [bold green]ON[/bold green]. Press [bold cyan]{self.clipboard_listener.hotkey.upper()}[/bold cyan] anytime to capture & auto-file!")
            else:
                self.console.print(f"[bold red]Could not register hotkey '{self.clipboard_listener.hotkey}'. Run as Administrator if required.[/bold red]")

    def _show_skills(self):
        """Displays loaded dynamic skill plugins and status."""
        skills = skill_manager.get_loaded_skills_summary()
        self.console.print("\n[bold]Loaded Skill Plugins & Permissions:[/bold]")
        if not skills:
            self.console.print("  [dim]No additional skill plugins found.[/dim]")
        for s in skills:
            badge = "[bold green][ACTIVE][/bold green]" if s.get("enabled", True) else "[bold yellow][DISABLED][/bold yellow]"
            tools_str = ", ".join(s.get("tools", []))
            self.console.print(f"  • {badge} [bold cyan]{s['name']}[/bold cyan]: {s['description']}")
            if tools_str:
                self.console.print(f"    [dim]Tools: {tools_str}[/dim]")
        self.console.print("[dim cyan]Tip: Toggle with '/skills enable <name>' or '/skills disable <name>'[/dim cyan]\n")

    def _handle_mic_input(self):
        """Records voice from microphone interactively, transcribes it, and processes it."""
        self.console.print("[bold magenta]🎤 Listening... Speak into your microphone and press Enter when done.[/bold magenta]")
        try:
            transcribed_text = self.voice_handler.record_interactive()
            if transcribed_text and transcribed_text.strip():
                self.console.print(f"[bold green]You (Voice) > [/bold green][italic]{transcribed_text}[/italic]")
                self._process_message(transcribed_text)
            else:
                self.console.print("[yellow]No speech detected. Please speak clearly and try again.[/yellow]")
        except Exception as e:
            logger.error(f"Error during mic recording/transcription: {e}", exc_info=True)
            self.console.print(f"[bold red]Could not record or transcribe audio: {e}[/bold red]")

    def _show_help(self):
        """Displays the help message."""
        self.console.print("\n[bold]Available Commands:[/bold]")
        self.console.print("  [cyan]/help[/cyan]    - Show this help menu.")
        self.console.print("  [cyan]/brief[/cyan]   - Generate your daily orientation brief (tasks, sessions, system).")
        self.console.print("  [cyan]/voice[/cyan]   - Toggle spoken voice output (ON/OFF).")
        self.console.print("  [cyan]/mic[/cyan]     - Record your voice and speak your query.")
        self.console.print("  [cyan]/wake[/cyan]    - Toggle hands-free 'Hey Sera' wake word listener.")
        self.console.print("  [cyan]/capture[/cyan] - Toggle global clipboard capture hotkey (Ctrl+Shift+S).")
        self.console.print("  [cyan]/skills[/cyan]  - List all loaded dynamic skill plugins.")
        self.console.print("  [cyan]/ui[/cyan]      - Launch modern Glassmorphic Web Dashboard in your browser.")
        self.console.print("  [cyan]/new[/cyan]     - Reset context and start a new conversation session.")
        self.console.print("  [cyan]/history[/cyan] - Display messages from the current session.")
        self.console.print("  [cyan]/clear[/cyan]   - Clear the terminal screen.")
        self.console.print("  [cyan]/exit[/cyan]    - Exit the application.\n")

    def _show_history(self):
        """Displays the conversation history for the current session."""
        history = self.orchestrator.memory.get_conversation_history(self.orchestrator.session_id)
        if not history:
            self.console.print("[yellow]No history in this session yet.[/yellow]")
            return

        self.console.print(f"\n[bold]History for session {self.orchestrator.session_id}:[/bold]")
        for msg in history:
            color = "green" if msg.role == "user" else "blue"
            self.console.print(f"[bold {color}]{msg.role.capitalize()} >[/bold {color}]")
            self.console.print(Markdown(msg.content))
            self.console.print("-" * 15)
        self.console.print()