import logging
import os
import sys
from core.orchestrator import get_orchestrator
from interfaces.terminal import TerminalInterface
from core.config import config  # This will raise ValueError if config is invalid
from skills.skill_manager import skill_manager

def setup_logging():
    """
    Configures logging for the application.
    Logs are written to 'logs/sera.log'.
    """
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, "sera.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
        ]
    )
    # Suppress noisy library logs
    logging.getLogger("httpx").setLevel(logging.WARNING)

def main():
    """
    Main entrypoint for the SERA application.
    """
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

    try:
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("SERA application starting...")

        # Load dynamic modular skills
        loaded_skills = skill_manager.discover_and_load_skills()
        logger.info(f"Loaded {len(loaded_skills)} skill plugin(s).")

        # Check for web UI flag
        if any(arg in sys.argv for arg in ['--ui', '--web', '-w']):
            import webbrowser
            import uvicorn
            from interfaces.web_server import app
            
            port = 8000
            url = f"http://127.0.0.1:{port}"
            print(f"\n=======================================================")
            print(f"✨ SERA Web Dashboard launching at: {url}")
            print(f"=======================================================\n")
            webbrowser.open(url)
            uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
            return

        orchestrator = get_orchestrator()
        terminal_interface = TerminalInterface(orchestrator)
        terminal_interface.start_chat()

    except ValueError as e:
        # This catches the config validation error
        logging.critical(f"Configuration error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logging.critical(f"An unexpected error occurred at startup: {e}", exc_info=True)
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

    logger.info("SERA application shutting down.")

if __name__ == "__main__":
    main()
