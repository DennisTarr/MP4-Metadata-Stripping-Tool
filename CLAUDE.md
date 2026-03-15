# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Repository Overview

This is a simple HTML5 games repository containing two browser-based strategy games with AI opponents:

- `tic-tac-toe.html` - Tic Tac Toe with three difficulty levels (Easy, Medium, Hard/unbeatable)
- `connect-four.html` - Connect Four with three difficulty levels using minimax with alpha-beta pruning

Both games are single-file applications containing HTML, CSS, and JavaScript. There is no build process or external dependencies.

## Development Workflow

### Viewing Games
Open either `.html` file in a web browser to play/test the game. No local server required.

### Testing Changes
- Edit an `.html` file and refresh the browser to test changes
- No test framework or automated tests exist for this repository

## Game Architecture

Both games follow a similar structure:

**Core Components:**
- **Game Board**: Rendered as DOM elements (grid of buttons/cells)
- **State Management**: Global variables track board state, current player, game active status
- **AI Engine**: Minimax algorithm with difficulty tiers:
  - Easy: Random move selection
  - Medium: Blended approach (X% optimal moves, Y% random)
  - Hard: Full minimax search (depth-limited for Connect Four)

**Tic Tac Toe Specifics:**
- Uses pure minimax with depth-based scoring (`10 - depth` for AI win, `depth - 10` for player win)
- Guarantees unbeatable gameplay on "Hard" setting
- Board: 3x3 grid stored as flat array of 9 elements

**Connect Four Specifics:**
- Uses minimax with alpha-beta pruning for performance optimization
- Includes heuristic board evaluation function when depth limit reached
- Board: 6x7 grid stored as 2D array (rows x columns)
- Hard mode searches up to depth 4 with randomized selection among best moves

## Key Patterns

**Move Validation:**
- Tic Tac Toe: Check if cell is empty and game is active before placing mark
- Connect Four: Find lowest empty row in selected column (`getValidRow`)

**Win Detection:**
- Predefined winning combinations checked after each move
- Winning cells highlighted visually upon game end

**Game Flow:**
1. Player clicks cell → validates move → updates board
2. Check win/draw conditions
3. If game continues, computer moves after 500ms delay
4. Update status and scores accordingly

## Code Style Notes

Both games use vanilla JavaScript with:
- No build tools or transpilation
- Inline styles in `<style>` tags
- Event handlers via `onclick` attributes
- CSS transitions/animations for polish

When modifying these files, maintain the single-file structure and avoid introducing external dependencies.
