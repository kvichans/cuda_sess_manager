Plugin for CudaText.
Gives commands in menu "Plugins" to manage sessions. Session is a set of opened named documents,
with properties of each document: caret position, encoding, lexer, bookmarks etc.
Session also contains information how "editor groups" are placed/resized. Sessions are stored
to files in JSON format, with .cuda-session extension, usually in the "settings" folder of CudaText.

Plugin also supports session files from SynWrite editor, which have different format and
.synw-session extension.

Plugin commands:
- Recent sessions: Show last used sessions in menu-dialog, and open chosen session.
- Open/New session: Show "Open" dialog to open session file (create session if filename not exists).
- Open previous session: Open most recently used session.
- Close session: Forget name of current session.
- Forget session and close all files: Forget name of current session, and close all documents.
- Save session: Save current session (CudaText does it only on app closing).
- Save session as: Save current session to a new file.

Plugin option(s) in user.json:
- "session_manager_confirmation": how to handle session files on opening them in CudaText.
	0: open as raw content
	1: open as session
	2 (default): ask user how to open


Author: Andrey Kvichanskiy https://github.com/kvichans/
License: MIT
