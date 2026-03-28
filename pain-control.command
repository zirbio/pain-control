#!/bin/bash
# Pain Control — Double-click launcher with interactive menu
# macOS .command files open in Terminal.app when double-clicked

cd "$(dirname "$0")"
BIN="./bin/pain-control"

clear
while true; do
    echo ""
    echo "  ╔══════════════════════════════════╗"
    echo "  ║       PAIN CONTROL  ◆            ║"
    echo "  ╠══════════════════════════════════╣"
    echo "  ║                                  ║"
    echo "  ║  1. Start all                    ║"
    echo "  ║  2. Stop all                     ║"
    echo "  ║  3. Restart all                  ║"
    echo "  ║  4. Status                       ║"
    echo "  ║  5. Logs (backend)               ║"
    echo "  ║  6. Logs (dashboard)             ║"
    echo "  ║  7. Open dashboard               ║"
    echo "  ║  8. Quit                         ║"
    echo "  ║                                  ║"
    echo "  ╚══════════════════════════════════╝"
    echo ""
    read -rp "  → " choice

    case "$choice" in
        1) "$BIN" start ;;
        2) "$BIN" stop ;;
        3) "$BIN" restart ;;
        4) "$BIN" status ;;
        5) "$BIN" logs api ;;
        6) "$BIN" logs web ;;
        7) "$BIN" open ;;
        8|q|Q) echo ""; echo "  Bye."; exit 0 ;;
        *) echo "  Invalid option." ;;
    esac

    echo ""
    read -rp "  Press Enter to continue..." _
    clear
done
