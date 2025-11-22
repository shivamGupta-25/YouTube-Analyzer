#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YouTube Channel Analyzer - Main Entry Point

This application analyzes YouTube channel videos and provides metrics
such as views, likes, comments, and engagement ratios.
"""

from gui.app import YouTubeAnalyzerApp


def main():
    """Launch the YouTube Channel Analyzer application."""
    app = YouTubeAnalyzerApp()
    app.mainloop()


if __name__ == "__main__":
    main()