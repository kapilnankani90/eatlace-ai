"""
Default Streamlit entrypoint for Streamlit Cloud deployment.
Redirects to the main application inside src/ui/app.py.
"""

from src.ui.app import main

if __name__ == "__main__":
    main()
