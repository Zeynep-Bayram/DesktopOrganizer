# DesktopOrganizer

An **AI-based smart desktop file organizer** that automatically classifies and manages files using Python.  
Keep your desktop clean and structured with real-time file monitoring and intelligent categorization.

---

## Features

- AI-based classification – intelligently detects file types and categories
- Automatic organization – moves files into relevant folders instantly
- Real-time monitoring – watches your desktop and organizes as you work
- Customizable rules – easily adjust categories in `config.py`
- Detailed logging – tracks every action for transparency
- Cross-platform support – works on Windows, macOS, and Linux

---

## Technologies Used

- Python 3.x
- os / pathlib → file system operations
- logging → activity logging
- threading → background monitoring
- colorama → styled console output

---

Run the application with:

python main.py

The program will begin monitoring your desktop.

Files are automatically classified into folders (e.g., Documents/, Images/, Music/, Code/).

You can edit config.py to add or remove categories.
