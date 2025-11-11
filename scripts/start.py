"""
Crypto LLM Trading System - Python Startup Script (Cross-Platform)

This script provides a cross-platform way to start the trading system.
It's an alternative to start.sh for Windows or systems without bash.

Usage:
    python scripts/start.py              # Start with default settings
    python scripts/start.py --verify     # Verify config before starting
    python scripts/start.py --port 8080  # Start on custom port
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path
import importlib.util

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_python_version():
    """Check if Python version is 3.9+"""
    if sys.version_info < (3, 9):
        print("❌ Python 3.9 or higher is required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")


def check_env_file():
    """Check if .env file exists"""
    env_file = Path(".env")

    if not env_file.exists():
        print("❌ .env file not found")
        print("   Please create a .env file with required configuration")
        print("   See .env.example for reference")
        sys.exit(1)

    print("✅ .env file found")


def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        "fastapi",
        "uvicorn",
        "supabase",
        "anthropic",
        "openai"
    ]

    missing_packages = []

    for package in required_packages:
        if importlib.util.find_spec(package) is None:
            missing_packages.append(package)

    if missing_packages:
        print(f"⚠️  Missing packages: {', '.join(missing_packages)}")
        print("   Installing dependencies from requirements.txt...")

        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                check=True
            )
            print("✅ Dependencies installed")
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            sys.exit(1)
    else:
        print("✅ All dependencies installed")


def verify_configuration():
    """Run configuration verification script"""
    print("\n🔍 Verifying configuration...")
    print("="*70)

    try:
        subprocess.run(
            [sys.executable, "scripts/verify_config.py"],
            check=True
        )
    except subprocess.CalledProcessError:
        print("\n❌ Configuration verification failed")
        sys.exit(1)


def print_banner():
    """Print startup banner"""
    print("\n" + "="*70)
    print("  🚀 CRYPTO LLM TRADING SYSTEM")
    print("="*70 + "\n")


def print_startup_info(host: str, port: int, reload: bool):
    """Print startup configuration"""
    print("\n" + "="*70)
    print("📊 STARTUP CONFIGURATION")
    print("="*70)
    print(f"  Host:              {host}")
    print(f"  Port:              {port}")
    print(f"  Auto-reload:       {reload}")
    print(f"  Dashboard URL:     http://localhost:{port}/dashboard/")
    print(f"  API Docs:          http://localhost:{port}/docs")
    print(f"  WebSocket:         ws://localhost:{port}/ws")
    print("="*70 + "\n")

    print("🤖 ACTIVE LLMs:")
    print("  • LLM-A - Claude Sonnet 4")
    print("  • LLM-B - DeepSeek Reasoner")
    print("  • LLM-C - GPT-4o")
    print()

    print("📈 TRADING CONFIGURATION:")
    print("  • 6 symbols - ETH, BNB, XRP, DOGE, ADA, AVAX")
    print("  • 5-minute cycles - Automated trading")
    print("  • $100 per LLM - Virtual balance")
    print()

    print("💻 FEATURES:")
    print("  • Real-time WebSocket dashboard")
    print("  • Automated 5-minute trading cycles")
    print("  • REST API (23 endpoints)")
    print("  • Live market data")
    print("  • LLM leaderboard")
    print("  • Position tracking")
    print()


def start_server(host: str, port: int, reload: bool):
    """Start the FastAPI server"""
    print("="*70)
    print("🚀 STARTING SERVER...")
    print("="*70 + "\n")

    # Build uvicorn command
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "src.api.main:app",
        "--host", host,
        "--port", str(port),
        "--log-level", "info"
    ]

    if reload:
        cmd.append("--reload")

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print("⚠️  Server stopped by user")
        print("="*70)
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Crypto LLM Trading System - Startup Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/start.py
  python scripts/start.py --verify
  python scripts/start.py --port 8080
  python scripts/start.py --no-reload --port 8000
        """
    )

    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify configuration before starting"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run on (default: 8000)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable auto-reload (for production)"
    )

    args = parser.parse_args()

    # Print banner
    print_banner()

    # Check Python version
    check_python_version()

    # Check .env file
    check_env_file()

    # Check dependencies
    check_dependencies()

    # Verify configuration if requested
    if args.verify:
        verify_configuration()

    # Print startup info
    print_startup_info(
        host=args.host,
        port=args.port,
        reload=not args.no_reload
    )

    # Start server
    start_server(
        host=args.host,
        port=args.port,
        reload=not args.no_reload
    )


if __name__ == "__main__":
    main()
