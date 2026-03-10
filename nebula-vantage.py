#!/usr/bin/env python3
# ====================================================================================================
# Nebula Vantage (Main Application)
# VERSION: v2.2.12
# ====================================================================================================
# PURPOSE: Media player - light mode default, left nav sidebar, full-width content,
#          collapsible right playlist overlay, video-only fullscreen, working dark/light toggle
# ====================================================================================================

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, Adw, Gst, GLib, Gio, GdkPixbuf, Gdk, Pango
import os, json, random, subprocess, shutil
from pathlib import Path

Gst.init(None)

APP_ID      = "org.nebulaprojects.vantage"
VERSION     = "v2.2.12"
CONFIG_DIR  = Path.home() / ".config" / "nebula-vantage"
CONFIG_FILE = CONFIG_DIR / "config.json"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
PLAYLISTS_DIR  = CONFIG_DIR / "playlist_saves"
PLAYLISTS_DIR.mkdir(parents=True, exist_ok=True)
ICONS_FILE     = CONFIG_DIR / "icons.json"
ICONS_IMG_DIR  = CONFIG_DIR / "icons"
ICONS_IMG_DIR.mkdir(parents=True, exist_ok=True)

AUDIO_FORMATS = {'.mp3','.flac','.ogg','.wav','.m4a','.aac','.opus','.wma'}
VIDEO_FORMATS = {'.mp4','.mkv','.avi','.mov','.webm','.flv','.wmv','.m4v','.ts','.mpg','.mpeg'}
ALL_FORMATS   = AUDIO_FORMATS | VIDEO_FORMATS

# =========================================================
#   CSS
# =========================================================
LIGHT_CSS = """
* { font-family: 'Noto Sans', 'Ubuntu', 'Cantarell', sans-serif; }
window { background-color: #f4f4f7; color: #1a1a2e; }
.left-sidebar { background-color: #ffffff; border-right: 1px solid #e0e0ea; min-width: 196px; }
.sidebar-logo-area { padding: 14px 16px 10px 16px; border-bottom: 1px solid #ebebf2; }
.sidebar-app-name { font-size: 13px; font-weight: 800; color: #1a1a2e; letter-spacing: -0.3px; }
.sidebar-app-sub  { font-size: 9.5px; font-weight: 600; color: #9898b0; letter-spacing: 0.5px; }
.sidebar-section-label { font-size: 9.5px; font-weight: 700; color: #b0b0c8; letter-spacing: 0.7px; padding: 10px 16px 3px 16px; }
.sidebar-item { border-radius: 8px; padding: 8px 12px; margin: 1px 8px; border: none; background: transparent; color: #5a5a78; font-size: 12.5px; font-weight: 500; }
.sidebar-item:hover { background-color: #f0f0f8; color: #1a1a2e; }
.sidebar-item.active { background-color: #eff3ff; color: #2563eb; font-weight: 700; }
.top-bar { background-color: #ffffff; border-bottom: 1px solid #e8e8f0; padding: 0 10px 0 14px; min-height: 38px; }
.open-btn { background: #f0f0f8; border: 1px solid #dcdce8; border-radius: 6px; padding: 2px 10px; color: #3a3a5a; font-size: 11px; font-weight: 600; min-height: 0; }
.open-btn:hover { background: #e8e8f4; }
.open-btn-primary { background: #2563eb; border: none; border-radius: 6px; padding: 2px 10px; color: #fff; font-size: 11px; font-weight: 600; min-height: 0; }
.open-btn-primary:hover { background: #1d4ed8; }
.page-title { font-size: 14px; font-weight: 700; color: #1a1a2e; }
.theme-toggle-row { border-top: 1px solid #ebebf2; padding-top: 10px; }
.theme-toggle-icon { color: #6666a0; }
.theme-toggle-label { font-size: 12px; font-weight: 600; color: #5a5a78; }
.placeholder-outer { background-color: #f4f4f7; }
.placeholder-art-box { background: #ebebf5; border-radius: 20px; border: 1.5px solid #dddded; }
.placeholder-icon  { color: #c8c8dc; }
.placeholder-title { font-size: 17px; font-weight: 700; color: #8888a8; }
.placeholder-sub   { font-size: 12px; color: #b0b0c8; }
.video-area { background-color: #000000; }
.media-list-area { background-color: #f4f4f7; padding: 12px 16px; }
.music-np-card { background: linear-gradient(135deg, #eff3ff 0%, #ffffff 100%); border-radius: 12px; border: 1px solid rgba(37,99,235,0.18); padding: 14px 18px; }
.music-np-art { background: #e8eaf8; border-radius: 10px; border: 1px solid #ddddef; }
.music-np-badge { font-size: 9px; font-weight: 800; color: #2563eb; letter-spacing: 1.2px; }
.music-np-title { font-size: 16px; font-weight: 800; color: #1a1a2e; letter-spacing: -0.3px; }
.music-np-artist { font-size: 12px; color: #6666a0; font-weight: 500; }
.media-row { background-color: #ffffff; border-radius: 8px; padding: 9px 14px; margin: 2px 0; border: 1px solid #ebebf2; }
.media-row:hover { background-color: #fafaff; border-color: #d8d8ea; }
.media-row.now-playing { background-color: #eff3ff; border-color: rgba(37,99,235,0.3); }
.row-num   { font-size: 11px; color: #c0c0d8; font-weight: 500; min-width: 20px; font-variant-numeric: tabular-nums; }
.row-icon  { color: #b0b0cc; }
.row-title { font-size: 12.5px; font-weight: 600; color: #1a1a2e; }
.media-row.now-playing .row-title { color: #2563eb; }
.row-meta  { font-size: 10.5px; color: #9898b8; }
.row-dur   { font-size: 10.5px; color: #c0c0d8; font-variant-numeric: tabular-nums; }
.video-badge { background: rgba(124,58,237,0.10); border-radius: 4px; padding: 1px 5px; font-size: 9px; font-weight: 700; color: #7c3aed; }
.playlist-overlay { background-color: rgba(255,255,255,0.97); border-left: 1px solid #e0e0ea; min-width: 264px; }
.playlist-overlay-hdr { background-color: #fafafe; border-bottom: 1px solid #ebebf2; padding: 10px 14px; }
.playlist-overlay-title { font-size: 11px; font-weight: 700; color: #5a5a88; letter-spacing: 0.7px; }
.playlist-overlay-count { font-size: 10.5px; color: #aaaacc; }
.pl-row-title { font-size: 12px; font-weight: 600; color: #2a2a48; }
.pl-row-meta  { font-size: 10.5px; color: #9898b8; }
.pl-row-dur   { font-size: 10px; color: #c0c0d8; font-variant-numeric: tabular-nums; }
.pl-item { border-radius: 6px; padding: 7px 10px; margin: 1px 6px; border: 1px solid transparent; }
.pl-item:hover { background: #f4f4fc; border-color: #e8e8f4; }
.pl-item.now-playing { background: #eff3ff; border-color: rgba(37,99,235,0.25); }
.pl-item.now-playing .pl-row-title { color: #2563eb; }
.pl-toggle-btn { background: #ffffff; border: 1px solid #e0e0ea; border-right: none; border-radius: 8px 0 0 8px; color: #8888aa; min-width: 20px; min-height: 44px; padding: 0; }
.pl-toggle-btn:hover { background: #f4f4fc; color: #2563eb; }
.playback-bar { background-color: #ffffff; border-top: 1px solid #e8e8f0; padding: 0 16px; }
.resize-handle { min-height: 12px; background: transparent; border-top: 1px solid #e4e4ef; }
.resize-handle:hover { background: rgba(37,99,235,0.10); border-top: 1px solid rgba(37,99,235,0.4); }
.resize-handle-active { background: rgba(37,99,235,0.18); border-top: 1px solid rgba(37,99,235,0.6); }
.resize-grip { font-size: 9px; color: #c8c8de; letter-spacing: 3px; }
.resize-handle:hover .resize-grip { color: rgba(37,99,235,0.6); }
.resize-grip { color: #c8c8de; }
.seek-bar trough   { background-color: #e8e8f2; border-radius: 3px; min-height: 3px; border: none; }
.seek-bar highlight { background-color: #2563eb; border-radius: 3px; }
.seek-bar slider   { background-color: #2563eb; border-radius: 50%; min-width: 11px; min-height: 11px; border: none; margin: -4px; }
.time-lbl { font-size: 10.5px; color: #9898b8; font-weight: 500; font-variant-numeric: tabular-nums; min-width: 34px; }
.np-title { font-size: 12.5px; font-weight: 700; color: #1a1a2e; }
.np-sub   { font-size: 10.5px; color: #9898b8; }
.ctrl-btn { background: #f4f4f8; border: 1px solid #e0e0ec; border-radius: 8px; color: #8888aa; }
.ctrl-btn:hover  { background: #ebebf4; color: #2a2a4a; border-color: #d0d0e4; }
.ctrl-btn.active { color: #2563eb; background: #eff3ff; border-color: rgba(37,99,235,0.3); }
.play-btn { background: #2563eb; border: none; border-radius: 50%; color: #ffffff; box-shadow: 0 3px 10px rgba(37,99,235,0.4); }
.play-btn:hover { background: #1d4ed8; }
.vol-bar trough   { background-color: #e8e8f2; border-radius: 3px; min-height: 3px; border: none; }
.vol-bar highlight { background-color: #2563eb; border-radius: 3px; }
.vol-bar slider   { background-color: #2563eb; border-radius: 50%; min-width: 10px; min-height: 10px; border: none; margin: -3px; }
.speed-btn { background: #f4f4f8; border: 1px solid #e0e0ec; border-radius: 6px; padding: 2px 8px; min-width: 40px; min-height: 30px; color: #6666a0; font-size: 11px; font-weight: 700; }
.speed-btn:hover  { background: #ebebf4; }
.speed-btn.active { color: #2563eb; background: #eff3ff; border-color: rgba(37,99,235,0.3); }
.art-box  { background-color: #eff0f8; border-radius: 7px; border: 1px solid #dddded; min-width: 42px; min-height: 42px; }
.art-icon { color: #c0c0da; }
.status-bar  { background-color: #fafafe; border-top: 1px solid #ebebf2; padding: 2px 14px; min-height: 20px; }
.status-lbl  { font-size: 10px; color: #b0b0c8; font-weight: 500; }
.fs-top-bar { background: linear-gradient(rgba(0,0,0,0.72), transparent); padding: 14px 20px 28px 20px; }
.fs-title { font-size: 14px; font-weight: 700; color: #ffffff; letter-spacing: -0.2px; }
.fs-sub   { font-size: 11px; color: rgba(255,255,255,0.6); }
.fs-bottom-bar { background: linear-gradient(transparent, rgba(0,0,0,0.78) 30%, rgba(0,0,0,0.88)); padding: 24px 20px 14px 20px; }
.fs-ctrl-btn { background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.18); border-radius: 8px; color: #ffffff; transition: all 0.1s; }
.fs-ctrl-btn:hover { background: rgba(255,255,255,0.22); }
.fs-ctrl-btn.active { background: rgba(37,99,235,0.5); border-color: rgba(37,99,235,0.6); }
.fs-play-btn { background: rgba(37,99,235,0.9); border: none; border-radius: 50%; color: #ffffff; }
.fs-play-btn:hover { background: #2563eb; }
.fs-seek trough   { background-color: rgba(255,255,255,0.22); border-radius: 3px; min-height: 4px; border: none; }
.fs-seek highlight { background-color: #2563eb; border-radius: 3px; }
.fs-seek slider   { background-color: #ffffff; border-radius: 50%; min-width: 13px; min-height: 13px; border: none; margin: -4px; box-shadow: 0 1px 4px rgba(0,0,0,0.5); }
.fs-vol trough    { background-color: rgba(255,255,255,0.22); border-radius: 3px; min-height: 3px; border: none; }
.fs-vol highlight  { background-color: rgba(255,255,255,0.85); border-radius: 3px; }
.fs-vol slider     { background-color: #ffffff; border-radius: 50%; min-width: 10px; min-height: 10px; border: none; margin: -3px; }
.fs-time  { font-size: 11.5px; color: rgba(255,255,255,0.85); font-variant-numeric: tabular-nums; font-weight: 500; }
.fs-speed { font-size: 10.5px; font-weight: 700; color: rgba(255,255,255,0.8); background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.18); border-radius: 5px; padding: 2px 7px; min-width: 34px; }
.settings-outer { background-color: #f4f4f7; }
.settings-section-label { font-size: 9.5px; font-weight: 700; color: #9898b8; letter-spacing: 0.8px; padding: 0 4px 5px 4px; }
.settings-card { background-color: #ffffff; border-radius: 10px; border: 1px solid #e4e4ef; }
.settings-row { padding: 11px 16px; border-bottom: 1px solid #f0f0f8; }
.settings-row:last-child { border-bottom: none; }
.settings-row-title { font-size: 12.5px; font-weight: 600; color: #1a1a2e; }
.settings-row-sub   { font-size: 10.5px; color: #9898b8; }
.settings-row-value { font-size: 12px; font-weight: 600; color: #2563eb; }
.settings-kbd { background: #f0f0f8; border: 1px solid #ddddef; border-radius: 5px; padding: 2px 8px; font-size: 11px; font-weight: 700; color: #4444aa; font-family: monospace; }
.settings-about-card { background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%); border-radius: 12px; padding: 20px; border: none; }
.settings-about-name { font-size: 18px; font-weight: 800; color: #ffffff; letter-spacing: -0.4px; }
.settings-about-ver  { font-size: 11px; font-weight: 600; color: rgba(255,255,255,0.6); }
.settings-about-sub  { font-size: 11px; color: rgba(255,255,255,0.5); }
.settings-badge { background: rgba(255,255,255,0.15); border-radius: 5px; padding: 2px 8px; font-size: 10px; font-weight: 700; color: rgba(255,255,255,0.8); }
.settings-fmt-chip { background: #eff0f8; border: 1px solid #e0e0f0; border-radius: 5px; padding: 2px 7px; font-size: 10px; font-weight: 600; color: #6666a0; margin: 2px; }
.settings-banner { background: #fffbeb; border-bottom: 1px solid #f59e0b; padding: 8px 16px; }
.banner-icon { color: #d97706; }
.banner-lbl { font-size: 12px; font-weight: 600; color: #92400e; }
.banner-apply-btn { background: #2563eb; border: none; border-radius: 6px; padding: 3px 12px; color: #fff; font-size: 11.5px; font-weight: 700; min-height: 26px; }
.banner-apply-btn:hover { background: #1d4ed8; }
.banner-revert-btn { background: #f0f0f8; border: 1px solid #dcdce8; border-radius: 6px; padding: 3px 10px; color: #5a5a78; font-size: 11.5px; font-weight: 600; min-height: 26px; }
.banner-revert-btn:hover { background: #e8e8f4; }
.settings-banner { background: #fffbeb; border-bottom: 1px solid #fde68a; padding: 8px 16px; min-height: 40px; }
.banner-lbl { font-size: 12px; font-weight: 600; color: #92400e; }
.banner-icon { color: #d97706; }
.banner-apply-btn { background: #2563eb; border: none; border-radius: 6px; padding: 4px 14px; color: #fff; font-size: 11.5px; font-weight: 700; min-height: 28px; }
.banner-apply-btn:hover { background: #1d4ed8; }
.banner-revert-btn { background: transparent; border: 1px solid #fcd34d; border-radius: 6px; padding: 4px 14px; color: #92400e; font-size: 11.5px; font-weight: 600; min-height: 28px; }
.banner-revert-btn:hover { background: #fef3c7; }
.pl-page-outer { background-color: #f4f4f7; }
.pl-page-header { background-color: #ffffff; border-bottom: 1px solid #e8e8f0; padding: 14px 20px; }
.pl-page-title  { font-size: 15px; font-weight: 800; color: #1a1a2e; letter-spacing: -0.3px; }
.pl-page-sub    { font-size: 10.5px; color: #9898b8; }
.pl-create-btn  { background: #2563eb; border: none; border-radius: 8px; padding: 5px 14px; color: #fff; font-size: 11.5px; font-weight: 700; min-height: 30px; }
.pl-create-btn:hover { background: #1d4ed8; }
.pl-card { background: #ffffff; border-radius: 10px; border: 1px solid #e4e4ef; padding: 0; }
.pl-card-header { padding: 14px 18px 12px 12px; border-bottom: 1px solid #f0f0f8; }
.pl-card-name   { font-size: 15px; font-weight: 700; color: #1a1a2e; }
.pl-card-count  { font-size: 11px; color: #9898b8; }
.pl-card-add-btn { background: #eff3ff; border: 1px solid rgba(37,99,235,0.2); border-radius: 6px; padding: 4px 12px; color: #2563eb; font-size: 11.5px; font-weight: 700; min-height: 30px; }
.pl-card-add-btn:hover { background: #dbeafe; }
.pl-card-del-btn { background: #fff0f0; border: 1px solid rgba(220,38,38,0.2); border-radius: 6px; padding: 4px 10px; color: #dc2626; font-size: 11.5px; font-weight: 700; min-height: 30px; }
.pl-card-del-btn:hover { background: #fee2e2; }
.pl-card-play-btn { background: #2563eb; border: none; border-radius: 6px; padding: 4px 14px; color: #fff; font-size: 11.5px; font-weight: 700; min-height: 30px; }
.pl-card-play-btn:hover { background: #1d4ed8; }
.pl-card-row  { padding: 10px 18px; border-bottom: 1px solid #f4f4fb; }
.pl-card-row:last-child { border-bottom: none; }
.pl-card-row:hover { background: #fafaff; }
.pl-card-row-title { font-size: 13px; font-weight: 600; color: #1a1a2e; }
.pl-card-row-meta  { font-size: 11px; color: #9898b8; }
.pl-card-row-dur   { font-size: 11px; color: #c0c0d8; font-variant-numeric: tabular-nums; }
.pl-card-row-remove { background: transparent; border: none; border-radius: 5px; color: #c0c0d8; padding: 3px 6px; min-height: 0; }
.pl-card-row-remove:hover { background: #fee2e2; color: #dc2626; }
.pl-empty-hint { font-size: 11px; color: #c0c0d8; padding: 14px 16px; }
.pl-rename-entry { background: #f4f4f8; border: 1px solid #ddddef; border-radius: 6px; padding: 3px 8px; font-size: 13px; font-weight: 700; color: #1a1a2e; min-height: 0; }
.pl-collapse-btn { background: transparent; border: none; padding: 0 4px; color: #b0b0cc; min-height: 0; min-width: 0; border-radius: 4px; }
.pl-collapse-btn:hover { background: #f0f0f8; color: #2563eb; }
.sidebar-pl-item { border-radius: 6px; padding: 5px 8px 5px 10px; margin: 0px 4px; border: none; background: transparent; color: #6666a0; font-size: 11.5px; font-weight: 600; }
.sidebar-pl-item:hover { background-color: #f0f0f8; color: #1a1a2e; }
.sidebar-pl-item.active { background-color: #eff3ff; color: #2563eb; font-weight: 700; }
.sidebar-pl-track { border-radius: 5px; padding: 4px 8px 4px 28px; margin: 0px 4px; border: none; background: transparent; color: #9898b8; font-size: 10.5px; font-weight: 500; }
.sidebar-pl-track:hover { background-color: #f4f4fc; color: #3a3a5a; }
.sidebar-pl-track.now-playing { color: #2563eb; font-weight: 700; }
.sidebar-pl-arrow { background: transparent; border: none; padding: 0 2px; color: #c0c0d8; min-height: 0; min-width: 14px; border-radius: 3px; }
.sidebar-pl-arrow:hover { color: #2563eb; }
.icon-pick-btn { background: #f4f4f8; border: 1px solid #e4e4ef; border-radius: 8px; font-size: 20px; min-width: 42px; min-height: 42px; padding: 2px; }
.icon-pick-btn:hover { background: #eff3ff; border-color: rgba(37,99,235,0.3); }
.icon-pick-active { background: #eff3ff; border: 2px solid #2563eb; }
.pl-icon-lbl { font-size: 18px; min-width: 38px; min-height: 38px; }
.pl-card-edit-btn { background: #f0f4ff; border: 1px solid #c7d2fe; border-radius: 8px; padding: 5px 9px; color: #3b5bdb; min-width: 30px; min-height: 30px; }
.pl-card-edit-btn:hover { background: #e0e8ff; border-color: #3b5bdb; }
.pl-set-icon-btn { background: #f4f0ff; border: 1.5px solid #c4b5fd; border-radius: 9px; padding: 0; min-width: 58px; min-height: 58px; }
.pl-set-icon-btn:hover { background: #ede9fe; border-color: #7c3aed; }
.pl-set-icon-emoji { font-size: 20px; }
.pl-set-icon-text { font-size: 12px; font-weight: 700; color: #7c3aed; }
.tr-set-icon-btn { background: #f4f0ff; border: 1.5px solid #c4b5fd; border-radius: 8px; font-size: 22px; min-width: 42px; min-height: 42px; padding: 0; }
.tr-set-icon-btn:hover { background: #ede9fe; border-color: #7c3aed; }
"""

DARK_CSS = """
* { font-family: 'Noto Sans', 'Ubuntu', 'Cantarell', sans-serif; }
window { background-color: #0e0e14; color: #e2e2ec; }
.left-sidebar { background-color: #0c0c12; border-right: 1px solid rgba(255,255,255,0.07); min-width: 196px; }
.sidebar-logo-area { padding: 14px 16px 10px 16px; border-bottom: 1px solid rgba(255,255,255,0.06); }
.sidebar-app-name { font-size: 13px; font-weight: 800; color: #e2e2ec; letter-spacing: -0.3px; }
.sidebar-app-sub  { font-size: 9.5px; font-weight: 600; color: #44445a; letter-spacing: 0.5px; }
.sidebar-section-label { font-size: 9.5px; font-weight: 700; color: #33334a; letter-spacing: 0.7px; padding: 10px 16px 3px 16px; }
.sidebar-item { border-radius: 8px; padding: 8px 12px; margin: 1px 8px; border: none; background: transparent; color: #66668a; font-size: 12.5px; font-weight: 500; }
.sidebar-item:hover { background-color: #14141e; color: #ccccdd; }
.sidebar-item.active { background-color: #111828; color: #60a5fa; font-weight: 700; }
.top-bar { background-color: #0c0c12; border-bottom: 1px solid rgba(255,255,255,0.07); padding: 0 10px 0 14px; min-height: 38px; }
.open-btn { background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.10); border-radius: 6px; padding: 2px 10px; color: #aaaacc; font-size: 11px; font-weight: 600; min-height: 0; }
.open-btn:hover { background: rgba(255,255,255,0.11); }
.open-btn-primary { background: #2563eb; border: none; border-radius: 6px; padding: 2px 10px; color: #fff; font-size: 11px; font-weight: 600; min-height: 0; }
.open-btn-primary:hover { background: #1d4ed8; }
.page-title { font-size: 14px; font-weight: 700; color: #e2e2ec; }
.theme-toggle-row { border-top: 1px solid rgba(255,255,255,0.07); padding-top: 10px; }
.theme-toggle-icon { color: #7777a0; }
.theme-toggle-label { font-size: 12px; font-weight: 600; color: #7777a0; }
.placeholder-outer { background-color: #0e0e14; }
.placeholder-art-box { background: #111118; border-radius: 20px; border: 1.5px solid rgba(255,255,255,0.07); }
.placeholder-icon  { color: #1e1e2e; }
.placeholder-title { font-size: 17px; font-weight: 700; color: #2a2a40; }
.placeholder-sub   { font-size: 12px; color: #202030; }
.video-area { background-color: #000000; }
.media-list-area { background-color: #0e0e14; padding: 12px 16px; }
.music-np-card { background: linear-gradient(135deg, #0e1628 0%, #111116 100%); border-radius: 12px; border: 1px solid rgba(37,99,235,0.25); padding: 14px 18px; }
.music-np-art { background: #111828; border-radius: 10px; border: 1px solid rgba(37,99,235,0.2); }
.music-np-badge { font-size: 9px; font-weight: 800; color: #60a5fa; letter-spacing: 1.2px; }
.music-np-title { font-size: 16px; font-weight: 800; color: #e2e2ec; letter-spacing: -0.3px; }
.music-np-artist { font-size: 12px; color: #6666a0; font-weight: 500; }
.media-row { background-color: #131318; border-radius: 8px; padding: 9px 14px; margin: 2px 0; border: 1px solid rgba(255,255,255,0.05); }
.media-row:hover { background-color: #16161e; border-color: rgba(255,255,255,0.08); }
.media-row.now-playing { background-color: #111828; border-color: rgba(37,99,235,0.35); }
.row-num   { font-size: 11px; color: #33334a; font-weight: 500; min-width: 20px; font-variant-numeric: tabular-nums; }
.row-icon  { color: #33334a; }
.row-title { font-size: 12.5px; font-weight: 600; color: #ccccdd; }
.media-row.now-playing .row-title { color: #60a5fa; }
.row-meta  { font-size: 10.5px; color: #44445a; }
.row-dur   { font-size: 10.5px; color: #2a2a40; font-variant-numeric: tabular-nums; }
.video-badge { background: rgba(124,58,237,0.12); border-radius: 4px; padding: 1px 5px; font-size: 9px; font-weight: 700; color: #7c3aed; }
.playlist-overlay { background-color: rgba(12,12,18,0.97); border-left: 1px solid rgba(255,255,255,0.07); min-width: 264px; }
.playlist-overlay-hdr { background-color: #0a0a10; border-bottom: 1px solid rgba(255,255,255,0.06); padding: 10px 14px; }
.playlist-overlay-title { font-size: 11px; font-weight: 700; color: #44445a; letter-spacing: 0.7px; }
.playlist-overlay-count { font-size: 10.5px; color: #33334a; }
.pl-row-title { font-size: 12px; font-weight: 600; color: #ccccdd; }
.pl-row-meta  { font-size: 10.5px; color: #44445a; }
.pl-row-dur   { font-size: 10px; color: #2a2a40; font-variant-numeric: tabular-nums; }
.pl-item { border-radius: 6px; padding: 7px 10px; margin: 1px 6px; border: 1px solid transparent; }
.pl-item:hover { background: #16161e; border-color: rgba(255,255,255,0.06); }
.pl-item.now-playing { background: #111828; border-color: rgba(37,99,235,0.3); }
.pl-item.now-playing .pl-row-title { color: #60a5fa; }
.pl-toggle-btn { background: #0c0c12; border: 1px solid rgba(255,255,255,0.09); border-right: none; border-radius: 8px 0 0 8px; color: #44445a; min-width: 20px; min-height: 44px; padding: 0; }
.pl-toggle-btn:hover { background: #14141e; color: #60a5fa; }
.playback-bar { background-color: #0c0c12; border-top: 1px solid rgba(255,255,255,0.07); padding: 0 16px; }
.resize-handle { min-height: 12px; background: transparent; border-top: 1px solid rgba(255,255,255,0.07); }
.resize-handle:hover { background: rgba(37,99,235,0.14); border-top: 1px solid rgba(37,99,235,0.4); }
.resize-handle-active { background: rgba(37,99,235,0.22); border-top: 1px solid rgba(37,99,235,0.6); }
.resize-grip { font-size: 9px; color: rgba(255,255,255,0.15); letter-spacing: 3px; }
.resize-handle:hover .resize-grip { color: rgba(37,99,235,0.6); }
.resize-grip { color: #333350; }
.seek-bar trough   { background-color: rgba(255,255,255,0.08); border-radius: 3px; min-height: 3px; border: none; }
.seek-bar highlight { background-color: #2563eb; border-radius: 3px; }
.seek-bar slider   { background-color: #ffffff; border-radius: 50%; min-width: 11px; min-height: 11px; border: none; margin: -4px; }
.time-lbl { font-size: 10.5px; color: #44445a; font-weight: 500; font-variant-numeric: tabular-nums; min-width: 34px; }
.np-title { font-size: 12.5px; font-weight: 700; color: #e2e2ec; }
.np-sub   { font-size: 10.5px; color: #44445a; }
.ctrl-btn { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.09); border-radius: 8px; color: #66668a; }
.ctrl-btn:hover  { background: rgba(255,255,255,0.10); color: #ccccdd; }
.ctrl-btn.active { color: #3b82f6; background: rgba(37,99,235,0.12); border-color: rgba(37,99,235,0.28); }
.play-btn { background: #2563eb; border: none; border-radius: 50%; color: #ffffff; box-shadow: 0 3px 12px rgba(37,99,235,0.45); }
.play-btn:hover { background: #1d4ed8; }
.vol-bar trough   { background-color: rgba(255,255,255,0.07); border-radius: 3px; min-height: 3px; border: none; }
.vol-bar highlight { background-color: #2563eb; border-radius: 3px; }
.vol-bar slider   { background-color: #fff; border-radius: 50%; min-width: 10px; min-height: 10px; border: none; margin: -3px; }
.speed-btn { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.09); border-radius: 6px; padding: 2px 8px; min-width: 40px; min-height: 30px; color: #66668a; font-size: 11px; font-weight: 700; }
.speed-btn:hover  { background: rgba(255,255,255,0.10); }
.speed-btn.active { color: #3b82f6; background: rgba(37,99,235,0.12); border-color: rgba(37,99,235,0.28); }
.art-box  { background-color: #131320; border-radius: 7px; border: 1px solid rgba(37,99,235,0.18); min-width: 42px; min-height: 42px; }
.art-icon { color: #2a3a6a; }
.status-bar  { background-color: #08080e; border-top: 1px solid rgba(255,255,255,0.04); padding: 2px 14px; min-height: 20px; }
.status-lbl  { font-size: 10px; color: #2a2a40; font-weight: 500; }
.fs-top-bar { background: linear-gradient(rgba(0,0,0,0.72), transparent); padding: 14px 20px 28px 20px; }
.fs-title { font-size: 14px; font-weight: 700; color: #ffffff; letter-spacing: -0.2px; }
.fs-sub   { font-size: 11px; color: rgba(255,255,255,0.6); }
.fs-bottom-bar { background: linear-gradient(transparent, rgba(0,0,0,0.78) 30%, rgba(0,0,0,0.88)); padding: 24px 20px 14px 20px; }
.fs-ctrl-btn { background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.18); border-radius: 8px; color: #ffffff; transition: all 0.1s; }
.fs-ctrl-btn:hover { background: rgba(255,255,255,0.22); }
.fs-ctrl-btn.active { background: rgba(37,99,235,0.5); border-color: rgba(37,99,235,0.6); }
.fs-play-btn { background: rgba(37,99,235,0.9); border: none; border-radius: 50%; color: #ffffff; }
.fs-play-btn:hover { background: #2563eb; }
.fs-seek trough   { background-color: rgba(255,255,255,0.22); border-radius: 3px; min-height: 4px; border: none; }
.fs-seek highlight { background-color: #2563eb; border-radius: 3px; }
.fs-seek slider   { background-color: #ffffff; border-radius: 50%; min-width: 13px; min-height: 13px; border: none; margin: -4px; box-shadow: 0 1px 4px rgba(0,0,0,0.5); }
.fs-vol trough    { background-color: rgba(255,255,255,0.22); border-radius: 3px; min-height: 3px; border: none; }
.fs-vol highlight  { background-color: rgba(255,255,255,0.85); border-radius: 3px; }
.fs-vol slider     { background-color: #ffffff; border-radius: 50%; min-width: 10px; min-height: 10px; border: none; margin: -3px; }
.fs-time  { font-size: 11.5px; color: rgba(255,255,255,0.85); font-variant-numeric: tabular-nums; font-weight: 500; }
.fs-speed { font-size: 10.5px; font-weight: 700; color: rgba(255,255,255,0.8); background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.18); border-radius: 5px; padding: 2px 7px; min-width: 34px; }
scrollbar { background: transparent; border: none; }
scrollbar slider { background: rgba(255,255,255,0.09); border-radius: 4px; min-width: 4px; }
scrollbar slider:hover { background: rgba(255,255,255,0.16); }
.settings-outer { background-color: #0e0e14; }
.settings-section-label { font-size: 9.5px; font-weight: 700; color: #33334a; letter-spacing: 0.8px; padding: 0 4px 5px 4px; }
.settings-card { background-color: #111116; border-radius: 10px; border: 1px solid rgba(255,255,255,0.07); }
.settings-row { padding: 11px 16px; border-bottom: 1px solid rgba(255,255,255,0.04); }
.settings-row:last-child { border-bottom: none; }
.settings-row-title { font-size: 12.5px; font-weight: 600; color: #ccccdd; }
.settings-row-sub   { font-size: 10.5px; color: #44445a; }
.settings-row-value { font-size: 12px; font-weight: 600; color: #60a5fa; }
.settings-kbd { background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.12); border-radius: 5px; padding: 2px 8px; font-size: 11px; font-weight: 700; color: #8888cc; font-family: monospace; }
.settings-about-card { background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%); border-radius: 12px; padding: 20px; border: none; }
.settings-about-name { font-size: 18px; font-weight: 800; color: #ffffff; letter-spacing: -0.4px; }
.settings-about-ver  { font-size: 11px; font-weight: 600; color: rgba(255,255,255,0.6); }
.settings-about-sub  { font-size: 11px; color: rgba(255,255,255,0.5); }
.settings-badge { background: rgba(255,255,255,0.15); border-radius: 5px; padding: 2px 8px; font-size: 10px; font-weight: 700; color: rgba(255,255,255,0.8); }
.settings-fmt-chip { background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.10); border-radius: 5px; padding: 2px 7px; font-size: 10px; font-weight: 600; color: #7777aa; margin: 2px; }
.settings-banner { background: #1c1408; border-bottom: 1px solid #92400e; padding: 8px 16px; }
.banner-icon { color: #f59e0b; }
.banner-lbl { font-size: 12px; font-weight: 600; color: #fbbf24; }
.banner-apply-btn { background: #2563eb; border: none; border-radius: 6px; padding: 3px 12px; color: #fff; font-size: 11.5px; font-weight: 700; min-height: 26px; }
.banner-apply-btn:hover { background: #1d4ed8; }
.banner-revert-btn { background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.12); border-radius: 6px; padding: 3px 10px; color: #aaaacc; font-size: 11.5px; font-weight: 600; min-height: 26px; }
.banner-revert-btn:hover { background: rgba(255,255,255,0.11); }
.settings-banner { background: #1a1400; border-bottom: 1px solid #3d2e00; padding: 8px 16px; min-height: 40px; }
.banner-lbl { font-size: 12px; font-weight: 600; color: #fbbf24; }
.banner-icon { color: #f59e0b; }
.banner-apply-btn { background: #2563eb; border: none; border-radius: 6px; padding: 4px 14px; color: #fff; font-size: 11.5px; font-weight: 700; min-height: 28px; }
.banner-apply-btn:hover { background: #1d4ed8; }
.banner-revert-btn { background: transparent; border: 1px solid rgba(251,191,36,0.3); border-radius: 6px; padding: 4px 14px; color: #fbbf24; font-size: 11.5px; font-weight: 600; min-height: 28px; }
.banner-revert-btn:hover { background: rgba(251,191,36,0.08); }
.pl-page-outer { background-color: #0e0e14; }
.pl-page-header { background-color: #0c0c12; border-bottom: 1px solid rgba(255,255,255,0.07); padding: 14px 20px; }
.pl-page-title  { font-size: 15px; font-weight: 800; color: #e2e2ec; letter-spacing: -0.3px; }
.pl-page-sub    { font-size: 10.5px; color: #44445a; }
.pl-create-btn  { background: #2563eb; border: none; border-radius: 8px; padding: 5px 14px; color: #fff; font-size: 11.5px; font-weight: 700; min-height: 30px; }
.pl-create-btn:hover { background: #1d4ed8; }
.pl-card { background: #111116; border-radius: 10px; border: 1px solid rgba(255,255,255,0.07); }
.pl-card-header { padding: 14px 18px 12px 12px; border-bottom: 1px solid rgba(255,255,255,0.04); }
.pl-card-name   { font-size: 15px; font-weight: 700; color: #e2e2ec; }
.pl-card-count  { font-size: 11px; color: #44445a; }
.pl-card-add-btn { background: rgba(37,99,235,0.15); border: 1px solid rgba(37,99,235,0.3); border-radius: 6px; padding: 4px 12px; color: #60a5fa; font-size: 11.5px; font-weight: 700; min-height: 30px; }
.pl-card-add-btn:hover { background: rgba(37,99,235,0.25); }
.pl-card-del-btn { background: rgba(220,38,38,0.10); border: 1px solid rgba(220,38,38,0.2); border-radius: 6px; padding: 4px 10px; color: #f87171; font-size: 11.5px; font-weight: 700; min-height: 30px; }
.pl-card-del-btn:hover { background: rgba(220,38,38,0.18); }
.pl-card-play-btn { background: #2563eb; border: none; border-radius: 6px; padding: 4px 14px; color: #fff; font-size: 11.5px; font-weight: 700; min-height: 30px; }
.pl-card-play-btn:hover { background: #1d4ed8; }
.pl-card-row  { padding: 10px 18px; border-bottom: 1px solid rgba(255,255,255,0.03); }
.pl-card-row:last-child { border-bottom: none; }
.pl-card-row:hover { background: rgba(255,255,255,0.03); }
.pl-card-row-title { font-size: 13px; font-weight: 600; color: #ccccdd; }
.pl-card-row-meta  { font-size: 11px; color: #44445a; }
.pl-card-row-dur   { font-size: 11px; color: #2a2a40; font-variant-numeric: tabular-nums; }
.pl-card-row-remove { background: transparent; border: none; border-radius: 5px; color: #33334a; padding: 3px 6px; min-height: 0; }
.pl-card-row-remove:hover { background: rgba(220,38,38,0.15); color: #f87171; }
.pl-empty-hint { font-size: 11px; color: #33334a; padding: 14px 16px; }
.pl-rename-entry { background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.12); border-radius: 6px; padding: 3px 8px; font-size: 13px; font-weight: 700; color: #e2e2ec; min-height: 0; }
.pl-collapse-btn { background: transparent; border: none; padding: 0 4px; color: #33334a; min-height: 0; min-width: 0; border-radius: 4px; }
.pl-collapse-btn:hover { background: rgba(255,255,255,0.07); color: #60a5fa; }
.sidebar-pl-item { border-radius: 6px; padding: 5px 8px 5px 10px; margin: 0px 4px; border: none; background: transparent; color: #55558a; font-size: 11.5px; font-weight: 600; }
.sidebar-pl-item:hover { background-color: #14141e; color: #ccccdd; }
.sidebar-pl-item.active { background-color: #111828; color: #60a5fa; font-weight: 700; }
.sidebar-pl-track { border-radius: 5px; padding: 4px 8px 4px 28px; margin: 0px 4px; border: none; background: transparent; color: #44445a; font-size: 10.5px; font-weight: 500; }
.sidebar-pl-track:hover { background-color: rgba(255,255,255,0.04); color: #aaaacc; }
.sidebar-pl-track.now-playing { color: #60a5fa; font-weight: 700; }
.sidebar-pl-arrow { background: transparent; border: none; padding: 0 2px; color: #33334a; min-height: 0; min-width: 14px; border-radius: 3px; }
.sidebar-pl-arrow:hover { color: #60a5fa; }
.icon-pick-btn { background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.12); border-radius: 8px; font-size: 20px; min-width: 42px; min-height: 42px; padding: 2px; }
.icon-pick-btn:hover { background: rgba(37,99,235,0.18); border-color: rgba(37,99,235,0.35); }
.icon-pick-active { background: rgba(37,99,235,0.25); border: 2px solid #60a5fa; }
.pl-icon-lbl { font-size: 18px; min-width: 38px; min-height: 38px; }
.pl-card-edit-btn { background: rgba(59,91,219,0.18); border: 1px solid rgba(99,131,255,0.35); border-radius: 8px; padding: 5px 9px; color: #93a8f4; min-width: 30px; min-height: 30px; }
.pl-card-edit-btn:hover { background: rgba(59,91,219,0.28); border-color: rgba(99,131,255,0.6); }
.pl-set-icon-btn { background: rgba(124,58,237,0.18); border: 1.5px solid rgba(167,139,250,0.4); border-radius: 9px; padding: 0; min-width: 58px; min-height: 58px; }
.pl-set-icon-btn:hover { background: rgba(124,58,237,0.28); border-color: rgba(167,139,250,0.65); }
.pl-set-icon-emoji { font-size: 20px; }
.pl-set-icon-text { font-size: 12px; font-weight: 700; color: #a78bfa; }
.tr-set-icon-btn { background: rgba(124,58,237,0.15); border: 1.5px solid rgba(167,139,250,0.35); border-radius: 8px; font-size: 22px; min-width: 42px; min-height: 42px; padding: 0; }
.tr-set-icon-btn:hover { background: rgba(124,58,237,0.25); border-color: rgba(167,139,250,0.6); }
"""

# =========================================================
#   CONFIG
# =========================================================
class ConfigManager:
    def __init__(self):
        self._defaults = {"volume": 0.8, "dark_mode": False, "speed": 1.0, "muted": False}
        self.data = dict(self._defaults)
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE) as f: self.data.update(json.load(f))
            except: pass
        self._saved = dict(self.data)   # snapshot of last saved state

    def save(self):
        open(CONFIG_FILE, 'w').write(json.dumps(self.data, indent=2))
        self._saved = dict(self.data)

    def get(self, k, d=None): return self.data.get(k, d)
    def set(self, k, v): self.data[k] = v   # set in memory only — call save() to persist
    def set_and_save(self, k, v): self.data[k] = v; self.save()  # immediate save

    def load_saved(self):
        """Return the last-saved state from disk (for revert)."""
        return dict(self._saved)

# =========================================================
#   ICON STORE  — emoji icons for playlists & tracks
# =========================================================
# Keys: "pl:MyPlaylist" for playlists, "tr:/path/to/file.mp3" for tracks
ICON_PALETTE = [
    "🎵","🎶","🎸","🎹","🎺","🎻","🥁","🎷",
    "🔥","❤️","⭐","💫","🌙","☀️","🌈","⚡",
    "🎯","🏆","💎","👑","🚀","🌊","🌿","🍀",
    "😎","🤩","🥳","💯","✨","🎉","🎊","🎈",
    "🟣","🔵","🟢","🟡","🔴","⚫","⬛","🟤",
]

class IconStore:
    def __init__(self):
        self._data = {}
        if ICONS_FILE.exists():
            try:
                with open(ICONS_FILE) as f: self._data = json.load(f)
            except: pass

    def save(self):
        with open(ICONS_FILE, 'w') as f: json.dump(self._data, f, indent=2)

    def get_pl(self, name): return self._data.get(f"pl:{name}", "")
    def get_tr(self, path): return self._data.get(f"tr:{path}", "")

    def set_pl(self, name, emoji):
        self._data[f"pl:{name}"] = emoji; self.save()

    def set_tr(self, path, emoji):
        self._data[f"tr:{path}"] = emoji; self.save()

    def copy_image(self, src_path, key_label):
        """Copy an image to the icons dir and return its stored path (img:...)."""
        src = Path(src_path)
        # Use a sanitized filename based on key_label + original suffix
        safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in key_label)
        dest = ICONS_IMG_DIR / (safe + src.suffix.lower())
        shutil.copy2(str(src), str(dest))
        return f"img:{dest}"


# =========================================================
#   MEDIA ITEM
# =========================================================
class MediaItem:
    def __init__(self, path):
        self.path     = str(path)
        self.suffix   = Path(path).suffix.lower()
        self.is_video = self.suffix in VIDEO_FORMATS
        self.title    = Path(path).stem
        self.artist   = ""
        self.duration = 0
        self.cover    = None
        if not self.is_video: self._load_meta()

    def _load_meta(self):
        try:
            from mutagen import File as MF
            a = MF(self.path, easy=True)
            if a:
                self.title    = str(a.get('title', [self.title])[0])
                self.artist   = str(a.get('artist', [''])[0])
                self.duration = int(a.info.length) if hasattr(a,'info') else 0
        except: pass
        try:
            from mutagen import File as MF
            r = MF(self.path)
            if r and r.tags:
                for k in r.tags.keys():
                    ks = str(k)
                    if 'APIC' in ks or 'covr' in ks or 'PICTURE' in ks.upper():
                        t = r.tags[k]
                        if hasattr(t,'data'): self.cover = t.data
                        elif isinstance(t,list) and t and hasattr(t[0],'data'): self.cover = bytes(t[0].data)
                        break
        except: pass

    def fmt_dur(self):
        if not self.duration: return ""
        m,s = divmod(int(self.duration),60); h,m = divmod(m,60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

# =========================================================
#   PLAYER ENGINE
# =========================================================
class PlayerEngine:
    def __init__(self, on_pos, on_end, on_state, on_sink):
        self.on_pos=on_pos; self.on_end=on_end; self.on_state=on_state; on_sink=on_sink
        self._on_sink_cb = on_sink
        self._pipe=None; self._timer=None; self._paintable=None
        self._playing = False
        self._build()

    def _build(self):
        if self._pipe: self._pipe.set_state(Gst.State.NULL)
        self._paintable = None
        vsink = None

        # 1st choice: gtk4paintablesink (from gst-plugins-rs / gstreamer1-plugins-rs)
        try:
            s = Gst.ElementFactory.make("gtk4paintablesink", "vsink")
            if s:
                self._paintable = s.get_property("paintable")
                vsink = s
                print("[VANTAGE] Using gtk4paintablesink")
        except Exception as e:
            print(f"[VANTAGE] gtk4paintablesink: {e}")

        # 2nd choice: wrap gtk4paintablesink in glsinkbin (needed on some Wayland setups)
        if not vsink:
            try:
                inner = Gst.ElementFactory.make("gtk4paintablesink", "inner")
                glbin = Gst.ElementFactory.make("glsinkbin", "glbin")
                if inner and glbin:
                    glbin.set_property("sink", inner)
                    self._paintable = inner.get_property("paintable")
                    vsink = glbin
                    print("[VANTAGE] Using glsinkbin+gtk4paintablesink")
            except:
                pass

        if not vsink:
            print("[VANTAGE] *** gtk4paintablesink not found ***")
            print("[VANTAGE] Install with:")
            print("[VANTAGE]   Fedora/Bazzite: sudo rpm-ostree install gstreamer1-plugin-gtk4")
            print("[VANTAGE]   or: flatpak install flathub org.freedesktop.Platform.GStreamer.gstreamer-vaapi")
            print("[VANTAGE]   Fallback: video will play but not display in window")
            fk = Gst.ElementFactory.make("fakesink", "fv")
            if fk:
                fk.set_property("sync", True)
                self._pipe_vid_fake = True

        self._pipe = Gst.ElementFactory.make("playbin", "pb")
        if vsink:
            self._pipe.set_property("video-sink", vsink)
        elif fk:
            self._pipe.set_property("video-sink", fk)

        bus = self._pipe.get_bus()
        bus.add_signal_watch()
        bus.connect("message::eos",           self._eos)
        bus.connect("message::error",         self._err)
        bus.connect("message::state-changed", self._sc)
        bus.connect("message::async-done",    self._async_done)

        GLib.idle_add(self._on_sink_cb, self._paintable)

    def load(self, p):
        self._playing = False
        self._pipe.set_state(Gst.State.NULL)
        self._pipe.set_property("uri", Path(p).as_uri())
        # Go to PAUSED - wait for async-done before switching to PLAYING
        self._pipe.set_state(Gst.State.PAUSED)

    def play(self):
        self._playing = True
        self._pipe.set_state(Gst.State.PLAYING)
        self._start_timer()

    def pause(self):
        self._playing = False
        self._pipe.set_state(Gst.State.PAUSED)
        self._stop_timer()

    def stop(self):
        self._playing = False
        self._pipe.set_state(Gst.State.NULL)
        self._stop_timer()

    def _start_timer(self):
        self._stop_timer()
        self._timer = GLib.timeout_add(200, self._tick)

    def _stop_timer(self):
        if self._timer:
            GLib.source_remove(self._timer)
            self._timer = None

    def seek(self, s):
        self._pipe.seek_simple(
            Gst.Format.TIME,
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
            int(max(0, s) * Gst.SECOND))

    def set_volume(self, v): self._pipe.set_property("volume", max(0.0, min(1.0, v)))
    def set_mute(self, m):   self._pipe.set_property("mute", m)

    def set_speed(self, spd):
        pos = self.get_position()
        self._pipe.seek(spd, Gst.Format.TIME,
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE,
            Gst.SeekType.SET, int(pos * Gst.SECOND),
            Gst.SeekType.NONE, 0)

    def get_position(self):
        ok, p = self._pipe.query_position(Gst.Format.TIME)
        return p / Gst.SECOND if ok and p >= 0 else 0

    def get_duration(self):
        ok, d = self._pipe.query_duration(Gst.Format.TIME)
        return d / Gst.SECOND if ok and d > 0 else 0

    def is_playing(self):
        return self._playing

    def n_video(self):
        try: return self._pipe.get_property("n-video")
        except: return 0

    def n_text(self):
        try: return self._pipe.get_property("n-text")
        except: return 0

    def n_audio(self):
        try: return self._pipe.get_property("n-audio")
        except: return 0

    def set_audio_track(self, i): self._pipe.set_property("current-audio", i)
    def set_sub_track(self, i):
        self._pipe.set_property("current-text", i)
        self._pipe.set_property("flags", self._pipe.get_property("flags") | 0x4)
    def disable_subs(self):
        self._pipe.set_property("flags", self._pipe.get_property("flags") & ~0x4)

    def _tick(self):
        GLib.idle_add(self.on_pos, self.get_position(), self.get_duration())
        return True

    def _async_done(self, bus, msg):
        # Pipeline reached PAUSED - if we intended to play, switch to PLAYING now
        if self._playing:
            self._pipe.set_state(Gst.State.PLAYING)
            self._start_timer()

    def _eos(self, *a): GLib.idle_add(self.on_end)
    def _err(self, bus, msg):
        err, dbg = msg.parse_error()
        print(f"[VANTAGE|ERR] {err}\n{dbg}")

    def _sc(self, bus, msg):
        if msg.src == self._pipe:
            _, new, _ = msg.parse_state_changed()
            is_now_playing = (new == Gst.State.PLAYING)
            if is_now_playing != self._playing and new != Gst.State.VOID_PENDING:
                pass  # only update UI, don't change _playing flag
            GLib.idle_add(self.on_state, new == Gst.State.PLAYING)

# =========================================================
#   MAIN WINDOW
# =========================================================
class VantageWindow(Gtk.ApplicationWindow):
    NAV_VIDEOS="videos"; NAV_MUSIC="music"; NAV_PLAYLIST="playlists"; NAV_SETTINGS="settings"

    def __init__(self, app):
        super().__init__(application=app, title="Nebula Vantage")
        self.set_default_size(1160, 700)
        self.cfg        = ConfigManager()
        self.icons      = IconStore()
        self._dark      = self.cfg.get("dark_mode", False)
        self._playlist  = []
        self._pl_idx    = -1
        self._cur       = None
        self._seeking   = False
        self._muted     = self.cfg.get("muted", False)
        self._speed     = self.cfg.get("speed", 1.0)
        self._shuffle   = False
        self._repeat    = "off"
        self._has_video = False
        self._nav       = self.NAV_MUSIC
        self._fs_win    = None
        self._fs_tmr    = None
        self._subs_on   = False
        self._pb_bar_height    = float(max(38, self.cfg.get("pb_height", 85)))
        self._pb_drag_start_h  = 80.0
        self._pb_anim_id       = None
        self._anim_speed       = self.cfg.get("anim_speed", "normal")
        self._last_scale       = self.cfg.get("gui_scale", 1.0)
        self._syncing_theme    = False   # guard against recursive theme sync
        self._syncing_theme    = False   # guard against recursive toggle signals
        self._pending          = {}      # settings page pending (not-yet-applied) values

        self._css = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), self._css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self._load_css()

        self.engine = PlayerEngine(self._on_pos, self._on_end, self._on_state, self._on_sink)
        self.engine.set_volume(self.cfg.get("volume", 0.8))
        if self._muted: self.engine.set_mute(True)

        self._build()
        self._register_mime()

        # Apply saved GUI scale
        saved_scale = self.cfg.get("gui_scale", 1.0)
        if saved_scale != 1.0:
            GLib.idle_add(lambda: self._apply_gui_scale(saved_scale) or False)

        # Apply saved animation speed
        anim_map = {"smooth": 280, "normal": 120, "fast": 40}
        saved_anim = self.cfg.get("anim_speed", "normal")
        GLib.idle_add(lambda: self._stack.set_transition_duration(anim_map.get(saved_anim, 120)) or False)

        k = Gtk.EventControllerKey()
        k.connect("key-pressed", self._on_key)
        self.add_controller(k)

    def _load_css(self):
        # Reload CSS string directly on existing provider - instant, no flicker
        self._css.load_from_string(DARK_CSS if self._dark else LIGHT_CSS)

    def _update_theme_btn(self):
        if self._dark:
            self._dm_ico.set_from_icon_name("weather-clear-night-symbolic")
            self._dm_lbl.set_text("Dark")
        else:
            self._dm_ico.set_from_icon_name("weather-clear-symbolic")
            self._dm_lbl.set_text("Light")

    def _toggle_dark(self, *a):
        self._dark = not self._dark
        self.cfg.set("dark_mode", self._dark)
        self._load_css()
        self._sync_theme_ui()

    def _sync_theme_ui(self):
        if self._syncing_theme: return
        self._syncing_theme = True
        try:
            # Sidebar switch
            if hasattr(self, '_theme_switch'):
                self._theme_switch.set_active(self._dark)
                self._theme_icon.set_from_icon_name(
                    "weather-clear-night-symbolic" if self._dark else "weather-clear-symbolic")
                self._theme_lbl2.set_label("Dark Mode" if self._dark else "Light Mode")
            # Settings switch
            if hasattr(self, '_settings_theme_sw'):
                self._settings_theme_sw.set_active(self._dark)
                self._settings_theme_lbl.set_label("Dark Mode" if self._dark else "Light Mode")
        finally:
            self._syncing_theme = False

    def _register_mime(self):
        d = Path.home()/".local"/"share"/"applications"; d.mkdir(parents=True,exist_ok=True)
        mimes = "audio/mpeg;audio/flac;audio/ogg;audio/wav;audio/mp4;audio/aac;audio/opus;video/mp4;video/x-matroska;video/x-msvideo;video/quicktime;video/webm;video/x-flv;video/mpeg;"
        txt = f"[Desktop Entry]\nName=Nebula Vantage\nComment=Media Player\nExec=python3 {Path(__file__).resolve()} %U\nIcon=audio-x-generic\nTerminal=false\nType=Application\nCategories=AudioVideo;Audio;Video;Player;GTK;\nMimeType={mimes}\n"
        try:
            (d/"nebula-vantage.desktop").write_text(txt)
            subprocess.run(["update-desktop-database",str(d)],capture_output=True)
        except: pass

    # =========================================================
    #   BUILD
    # =========================================================
    def _build(self):
        root = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_child(root)
        root.append(self._mk_sidebar())

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        right.set_hexpand(True)
        root.append(right)

        right.append(self._mk_topbar())

        self._overlay = Gtk.Overlay()
        self._overlay.set_hexpand(True); self._overlay.set_vexpand(True)
        right.append(self._overlay)

        self._stack = Gtk.Stack()
        self._stack.set_hexpand(True); self._stack.set_vexpand(True)
        self._stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self._stack.set_transition_duration(100)
        self._overlay.set_child(self._stack)

        self._pg_placeholder = self._mk_placeholder_pg()
        self._pg_video       = self._mk_video_pg()
        self._pg_music       = self._mk_music_pg()
        self._pg_playlists   = self._mk_playlists_pg()
        self._pg_settings    = self._mk_settings_pg()

        self._stack.add_named(self._pg_placeholder,"placeholder")
        self._stack.add_named(self._pg_video,      "video")
        self._stack.add_named(self._pg_music,      "music")
        self._stack.add_named(self._pg_playlists,  "playlists")
        self._stack.add_named(self._pg_settings,   "settings")
        self._stack.set_visible_child_name("placeholder")


        pb_clip = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        pb_clip.set_vexpand(False); pb_clip.set_hexpand(True)
        pb_clip.set_overflow(Gtk.Overflow.HIDDEN)
        self._pb_clip = pb_clip
        pb_clip.append(self._mk_playback_bar())
        right.append(pb_clip)

        sb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        sb.add_css_class("status-bar")
        self._status_lbl = Gtk.Label(label=f"Nebula Vantage {VERSION}  ·  No media loaded")
        self._status_lbl.add_css_class("status-lbl"); self._status_lbl.set_halign(Gtk.Align.START)
        sb.append(self._status_lbl)
        right.append(sb)

    # =========================================================
    #   SIDEBAR
    # =========================================================
    def _mk_sidebar(self):
        sb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sb.add_css_class("left-sidebar")
        sb.set_size_request(196, -1)
        sb.set_hexpand(False)

        logo = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        logo.add_css_class("sidebar-logo-area")
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        n = Gtk.Label(); n.set_markup('<span size="large" weight="heavy" color="#2563eb">V</span>')
        nm = Gtk.Label(label="Nebula Vantage"); nm.add_css_class("sidebar-app-name")
        row.append(n); row.append(nm)
        sub = Gtk.Label(label="MEDIA PLAYER"); sub.add_css_class("sidebar-app-sub"); sub.set_halign(Gtk.Align.START)
        logo.append(row); logo.append(sub)
        sb.append(logo)

        nav_items = [
            ("MEDIA",   [(self.NAV_VIDEOS,   "video-x-generic-symbolic",    "Videos"),
                         (self.NAV_MUSIC,    "audio-x-generic-symbolic",    "Music")]),
        ]
        self._nav_btns = {}
        for sec_lbl, items in nav_items:
            l = Gtk.Label(label=sec_lbl); l.add_css_class("sidebar-section-label"); l.set_halign(Gtk.Align.START)
            sb.append(l)
            for key, ico, txt in items:
                b = self._mk_nav_btn(key, ico, txt)
                self._nav_btns[key] = b; sb.append(b)

        # ── LIBRARY section with inline playlist tree ────────
        lib_lbl = Gtk.Label(label="LIBRARY"); lib_lbl.add_css_class("sidebar-section-label"); lib_lbl.set_halign(Gtk.Align.START)
        sb.append(lib_lbl)

        # "Playlists" nav button (navigates to playlists page)
        pl_nav_btn = self._mk_nav_btn(self.NAV_PLAYLIST, "view-list-symbolic", "Playlists")
        self._nav_btns[self.NAV_PLAYLIST] = pl_nav_btn
        sb.append(pl_nav_btn)

        # Playlist tree container — rebuilt by _sidebar_refresh_playlists()
        self._sidebar_pl_tree = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        sb.append(self._sidebar_pl_tree)

        # Track sidebar playlist expand states: {pl_name: bool}
        self._sidebar_pl_expanded = {}

        self._sidebar_refresh_playlists()

        sp = Gtk.Box(); sp.set_vexpand(True); sb.append(sp)

        # Settings at bottom
        s_btn = self._mk_nav_btn(self.NAV_SETTINGS,"preferences-system-symbolic","Settings")
        self._nav_btns[self.NAV_SETTINGS] = s_btn
        s_btn.set_margin_bottom(4); sb.append(s_btn)

        # Theme toggle row — icon, "Dark Mode" label, Gtk.Switch
        tog_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        tog_row.add_css_class("theme-toggle-row")
        tog_row.set_margin_start(12); tog_row.set_margin_end(12); tog_row.set_margin_bottom(12)
        tog_row.set_valign(Gtk.Align.CENTER)

        self._theme_icon = Gtk.Image.new_from_icon_name(
            "weather-clear-night-symbolic" if self._dark else "weather-clear-symbolic")
        self._theme_icon.set_pixel_size(15); self._theme_icon.add_css_class("theme-toggle-icon")

        self._theme_lbl2 = Gtk.Label(label="Dark Mode" if self._dark else "Light Mode")
        self._theme_lbl2.add_css_class("theme-toggle-label"); self._theme_lbl2.set_hexpand(True)
        self._theme_lbl2.set_halign(Gtk.Align.START)

        self._theme_switch = Gtk.Switch()
        self._theme_switch.set_active(self._dark)
        self._theme_switch.set_valign(Gtk.Align.CENTER)

        def _on_switch(sw, _param):
            if self._syncing_theme: return
            dark = sw.get_active()
            self._dark = dark; self.cfg.set_and_save("dark_mode", dark)
            self._load_css()
            self._sync_theme_ui()

        self._theme_switch.connect("notify::active", _on_switch)
        tog_row.append(self._theme_icon); tog_row.append(self._theme_lbl2); tog_row.append(self._theme_switch)
        sb.append(tog_row)
        return sb

    def _mk_nav_btn(self, key, ico_name, txt):
        b = Gtk.Button(); b.add_css_class("sidebar-item")
        if key == self._nav: b.add_css_class("active")
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=9); row.set_halign(Gtk.Align.START)
        i = Gtk.Image.new_from_icon_name(ico_name); i.set_pixel_size(15)
        l = Gtk.Label(label=txt)
        row.append(i); row.append(l); b.set_child(row)
        b.connect("clicked", lambda *a, k=key: self._nav_to(k))
        return b

    def _sidebar_refresh_playlists(self):
        """Rebuild sidebar playlist tree from disk."""
        if not hasattr(self, '_sidebar_pl_tree'): return
        while self._sidebar_pl_tree.get_first_child():
            self._sidebar_pl_tree.remove(self._sidebar_pl_tree.get_first_child())

        for pl_name in self._pl_list_names():
            expanded = self._sidebar_pl_expanded.get(pl_name, False)

            # Row: [arrow] [icon] [name]  (clicks navigate to playlists page)
            item_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

            arrow_btn = Gtk.Button()
            arrow_btn.add_css_class("sidebar-pl-arrow")
            arrow_ico = Gtk.Image.new_from_icon_name(
                "pan-down-symbolic" if expanded else "pan-end-symbolic")
            arrow_ico.set_pixel_size(10)
            arrow_btn.set_child(arrow_ico)
            arrow_btn.set_valign(Gtk.Align.CENTER)

            pl_btn = Gtk.Button(); pl_btn.add_css_class("sidebar-pl-item"); pl_btn.set_hexpand(True)
            pl_inner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=7)
            pl_inner.set_halign(Gtk.Align.START)
            pl_emoji = self.icons.get_pl(pl_name)
            pl_ico_widget = self._icon_widget(pl_emoji, 38)
            pl_ico_widget.add_css_class("pl-icon-lbl")
            pl_lbl = Gtk.Label(label=pl_name); pl_lbl.set_ellipsize(Pango.EllipsizeMode.END); pl_lbl.set_max_width_chars(12)
            pl_inner.append(pl_ico_widget); pl_inner.append(pl_lbl)
            pl_btn.set_child(pl_inner)
            pl_btn.connect("clicked", lambda *a, n=pl_name: self._pl_load_and_play(n))

            item_row.append(arrow_btn); item_row.append(pl_btn)
            self._sidebar_pl_tree.append(item_row)

            # Track sub-list (shown when expanded)
            tracks_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            tracks_box.set_visible(expanded)

            tracks = self._pl_tracks(pl_name)
            for tp in tracks:
                try:
                    from mutagen import File as MF
                    a = MF(str(tp), easy=True)
                    title = str(a.get('title', [tp.stem])[0]) if a else tp.stem
                except:
                    title = tp.stem

                is_playing = (self._cur and self._cur.path == str(tp))
                track_btn = Gtk.Button(); track_btn.add_css_class("sidebar-pl-track")
                if is_playing: track_btn.add_css_class("now-playing")
                t_lbl = Gtk.Label(label=title); t_lbl.set_halign(Gtk.Align.START)
                t_lbl.set_ellipsize(Pango.EllipsizeMode.END); t_lbl.set_max_width_chars(16)
                track_btn.set_child(t_lbl)
                track_btn.connect("clicked", lambda *a, n=pl_name, p=str(tp): self._pl_load_and_play(n, start_path=p))
                tracks_box.append(track_btn)

            self._sidebar_pl_tree.append(tracks_box)

            # Wire arrow toggle
            def _toggle(btn, ico=arrow_ico, box=tracks_box, n=pl_name):
                exp = not self._sidebar_pl_expanded.get(n, False)
                self._sidebar_pl_expanded[n] = exp
                ico.set_from_icon_name("pan-down-symbolic" if exp else "pan-end-symbolic")
                box.set_visible(exp)

            arrow_btn.connect("clicked", _toggle)

    def _nav_to(self, key):
        self._nav = key
        for k,b in self._nav_btns.items():
            if k==key: b.add_css_class("active")
            else:      b.remove_css_class("active")
        pages = {self.NAV_SETTINGS:"settings", self.NAV_PLAYLIST:"playlists",
                 self.NAV_MUSIC:"music"}
        if key in pages:
            self._stack.set_visible_child_name(pages[key])
        elif key == self.NAV_VIDEOS:
            self._stack.set_visible_child_name("video" if self._has_video else "placeholder")
        titles = {self.NAV_VIDEOS:"Videos",self.NAV_MUSIC:"Music",
                  self.NAV_PLAYLIST:"Playlists",self.NAV_SETTINGS:"Settings"}
        self._page_title.set_label(titles.get(key,""))
        # Refresh playlists from disk each time we visit the page
        if key == self.NAV_PLAYLIST:
            self._pl_refresh_cards()
            self._sidebar_refresh_playlists()

    # =========================================================
    #   TOP BAR
    # =========================================================
    def _mk_topbar(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        bar.add_css_class("top-bar")
        bar.set_margin_start(4); bar.set_margin_end(8)
        self._page_title = Gtk.Label(label="Music"); self._page_title.add_css_class("page-title")
        bar.append(self._page_title)
        sp = Gtk.Box(); sp.set_hexpand(True); bar.append(sp)
        self._open_file_btn = Gtk.Button(label="Open File")
        self._open_file_btn.add_css_class("open-btn-primary")
        self._open_file_btn.connect("clicked", self._open_file)
        self._open_file_btn.set_size_request(82, 26)
        self._open_file_btn.set_valign(Gtk.Align.CENTER)
        bar.append(self._open_file_btn)
        self._open_folder_btn = Gtk.Button(label="Open Folder")
        self._open_folder_btn.add_css_class("open-btn")
        self._open_folder_btn.connect("clicked", self._open_folder)
        self._open_folder_btn.set_size_request(90, 26)
        self._open_folder_btn.set_valign(Gtk.Align.CENTER)
        bar.append(self._open_folder_btn)
        return bar

    # =========================================================
    #   PAGES
    # =========================================================
    def _mk_placeholder_pg(self):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        outer.add_css_class("placeholder-outer"); outer.set_hexpand(True); outer.set_vexpand(True)

        # Top section: empty state info
        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        inner.set_hexpand(True); inner.set_vexpand(True)
        inner.set_halign(Gtk.Align.CENTER); inner.set_valign(Gtk.Align.CENTER)

        # Big album art placeholder
        art_box = Gtk.Box()
        art_box.add_css_class("placeholder-art-box")
        art_box.set_halign(Gtk.Align.CENTER)
        art_box.set_size_request(120, 120)
        art_ico = Gtk.Image.new_from_icon_name("audio-x-generic-symbolic")
        art_ico.set_pixel_size(56); art_ico.add_css_class("placeholder-icon")
        art_ico.set_halign(Gtk.Align.CENTER); art_ico.set_valign(Gtk.Align.CENTER)
        art_ico.set_hexpand(True); art_ico.set_vexpand(True)
        art_box.append(art_ico)

        t = Gtk.Label(label="No Media Loaded"); t.add_css_class("placeholder-title")
        s = Gtk.Label(label="Open a file or folder to get started")
        s.add_css_class("placeholder-sub")
        inner.append(art_box); inner.append(t); inner.append(s)
        outer.append(inner)
        return outer

    def _mk_video_pg(self):
        ov = Gtk.Overlay(); ov.set_hexpand(True); ov.set_vexpand(True)
        self._vid_pic = Gtk.Picture()
        self._vid_pic.set_hexpand(True); self._vid_pic.set_vexpand(True)
        self._vid_pic.add_css_class("video-area")
        self._vid_pic.set_content_fit(Gtk.ContentFit.CONTAIN)
        ov.set_child(self._vid_pic)

        # Resolution badge — top right, auto-hides after 3s
        self._res_badge = Gtk.Label(label="")
        self._res_badge.add_css_class("resize-size-badge")
        self._res_badge.set_halign(Gtk.Align.END)
        self._res_badge.set_valign(Gtk.Align.START)
        self._res_badge.set_margin_end(10); self._res_badge.set_margin_top(10)
        self._res_badge.set_visible(False)
        ov.add_overlay(self._res_badge)

        gc = Gtk.GestureClick(); gc.connect("released", self._on_video_click); ov.add_controller(gc)
        return ov

    def _mk_music_pg(self):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        outer.add_css_class("media-list-area"); outer.set_hexpand(True); outer.set_vexpand(True)

        # Now-playing card at top — hidden until music loads
        self._music_np_card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        self._music_np_card.add_css_class("music-np-card")
        self._music_np_card.set_visible(False)
        self._music_np_card.set_margin_bottom(12)

        self._music_np_art_box = Gtk.Box()
        self._music_np_art_box.add_css_class("music-np-art")
        self._music_np_art_box.set_size_request(80, 80)
        self._music_np_art_ico = Gtk.Image.new_from_icon_name("audio-x-generic-symbolic")
        self._music_np_art_ico.set_pixel_size(36); self._music_np_art_ico.add_css_class("art-icon")
        self._music_np_art_ico.set_hexpand(True); self._music_np_art_ico.set_vexpand(True)
        self._music_np_art_ico.set_halign(Gtk.Align.CENTER); self._music_np_art_ico.set_valign(Gtk.Align.CENTER)
        self._music_np_art_img = Gtk.Image(); self._music_np_art_img.set_pixel_size(80)
        self._music_np_art_img.set_visible(False)
        self._music_np_art_box.append(self._music_np_art_ico)
        self._music_np_art_box.append(self._music_np_art_img)
        self._music_np_card.append(self._music_np_art_box)

        np_info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        np_info.set_vexpand(True); np_info.set_valign(Gtk.Align.CENTER); np_info.set_hexpand(True)
        now_lbl = Gtk.Label(label="NOW PLAYING"); now_lbl.add_css_class("music-np-badge"); now_lbl.set_halign(Gtk.Align.START)
        self._music_np_title = Gtk.Label(label=""); self._music_np_title.add_css_class("music-np-title")
        self._music_np_title.set_halign(Gtk.Align.START); self._music_np_title.set_ellipsize(Pango.EllipsizeMode.END)
        self._music_np_artist = Gtk.Label(label=""); self._music_np_artist.add_css_class("music-np-artist")
        self._music_np_artist.set_halign(Gtk.Align.START); self._music_np_artist.set_ellipsize(Pango.EllipsizeMode.END)
        np_info.append(now_lbl); np_info.append(self._music_np_title); np_info.append(self._music_np_artist)
        self._music_np_card.append(np_info)
        outer.append(self._music_np_card)

        sc = Gtk.ScrolledWindow(); sc.set_hexpand(True); sc.set_vexpand(True)
        sc.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self._music_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        sc.set_child(self._music_list); outer.append(sc)
        return outer

    def _mk_stub_pg(self, ico_name, title, sub):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        outer.add_css_class("placeholder-outer"); outer.set_hexpand(True); outer.set_vexpand(True)
        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        inner.set_hexpand(True); inner.set_vexpand(True)
        inner.set_halign(Gtk.Align.CENTER); inner.set_valign(Gtk.Align.CENTER)
        ico = Gtk.Image.new_from_icon_name(ico_name); ico.set_pixel_size(40); ico.add_css_class("placeholder-icon")
        t = Gtk.Label(label=title); t.add_css_class("placeholder-title")
        s = Gtk.Label(label=sub); s.add_css_class("placeholder-sub")
        inner.append(ico); inner.append(t); inner.append(s); outer.append(inner)
        return outer

    # =========================================================
    #   PLAYLISTS PAGE
    # =========================================================
    def _pl_saves_dir(self):
        """Always returns the live PLAYLISTS_DIR path."""
        return PLAYLISTS_DIR

    def _pl_folder(self, name):
        return self._pl_saves_dir() / name

    def _pl_list_names(self):
        """Scan playlist_saves for valid playlist folders (sorted)."""
        d = self._pl_saves_dir()
        return sorted([p.name for p in d.iterdir() if p.is_dir()])

    def _pl_tracks(self, name):
        """Return list of audio/video file paths inside a playlist folder."""
        folder = self._pl_folder(name)
        if not folder.exists(): return []
        all_formats = AUDIO_FORMATS | VIDEO_FORMATS
        tracks = [p for p in sorted(folder.iterdir())
                  if p.is_file() and p.suffix.lower() in all_formats]
        return tracks

    def _mk_playlists_pg(self):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        outer.add_css_class("pl-page-outer"); outer.set_hexpand(True); outer.set_vexpand(True)

        # ── Header bar ──────────────────────────────────────
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        hdr.add_css_class("pl-page-header")
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title_box.set_hexpand(True); title_box.set_valign(Gtk.Align.CENTER)
        pt = Gtk.Label(label="Playlists"); pt.add_css_class("pl-page-title"); pt.set_halign(Gtk.Align.START)
        ps = Gtk.Label(label="Saved to  ~/.config/nebula-vantage/playlist_saves/")
        ps.add_css_class("pl-page-sub"); ps.set_halign(Gtk.Align.START)
        title_box.append(pt); title_box.append(ps)
        create_btn = Gtk.Button(label="＋  New Playlist"); create_btn.add_css_class("pl-create-btn")
        create_btn.set_valign(Gtk.Align.CENTER)
        create_btn.connect("clicked", self._pl_create_dialog)
        hdr.append(title_box); hdr.append(create_btn)
        outer.append(hdr)

        # ── Scrollable cards area ────────────────────────────
        scroll = Gtk.ScrolledWindow(); scroll.set_hexpand(True); scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self._pl_cards_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self._pl_cards_box.set_margin_top(16); self._pl_cards_box.set_margin_bottom(20)
        self._pl_cards_box.set_margin_start(20); self._pl_cards_box.set_margin_end(20)
        scroll.set_child(self._pl_cards_box)
        outer.append(scroll)

        self._pl_refresh_cards()
        return outer

    def _pl_refresh_cards(self):
        """Rebuild the playlist cards from disk."""
        if not hasattr(self, '_pl_cards_box'): return
        while self._pl_cards_box.get_first_child():
            self._pl_cards_box.remove(self._pl_cards_box.get_first_child())

        names = self._pl_list_names()
        if not names:
            empty = Gtk.Label(label="No playlists yet — create one with the button above")
            empty.add_css_class("pl-empty-hint"); empty.set_halign(Gtk.Align.CENTER)
            empty.set_margin_top(60)
            self._pl_cards_box.append(empty)
            self._sidebar_refresh_playlists()
            return

        for name in names:
            self._pl_cards_box.append(self._mk_pl_card(name))
        self._sidebar_refresh_playlists()

    def _mk_pl_card(self, name):
        """Build one playlist card widget."""
        tracks = self._pl_tracks(name)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        card.add_css_class("pl-card")

        # Card header row
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        hdr.add_css_class("pl-card-header")

        # Collapse arrow
        collapse_ico = Gtk.Image.new_from_icon_name("pan-down-symbolic")
        collapse_ico.set_pixel_size(11)
        collapse_btn = Gtk.Button(); collapse_btn.add_css_class("pl-collapse-btn")
        collapse_btn.set_child(collapse_ico); collapse_btn.set_valign(Gtk.Align.CENTER)

        name_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        name_box.set_hexpand(True); name_box.set_valign(Gtk.Align.CENTER)
        name_lbl = Gtk.Label(label=name); name_lbl.add_css_class("pl-card-name"); name_lbl.set_halign(Gtk.Align.START)
        count_lbl = Gtk.Label(label=f"{len(tracks)} track{'s' if len(tracks)!=1 else ''}")
        count_lbl.add_css_class("pl-card-count"); count_lbl.set_halign(Gtk.Align.START)
        name_box.append(name_lbl); name_box.append(count_lbl)

        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        btn_row.set_valign(Gtk.Align.CENTER)

        # Folder icon — opens playlist folder in file manager
        folder_btn = Gtk.Button(); folder_btn.add_css_class("pl-card-add-btn")
        folder_ico_img = Gtk.Image.new_from_icon_name("folder-open-symbolic"); folder_ico_img.set_pixel_size(13)
        folder_btn.set_child(folder_ico_img)
        folder_btn.set_tooltip_text("Open playlist folder")
        folder_btn.connect("clicked", lambda *a, n=name: self._pl_open_folder(n))

        play_btn = Gtk.Button(label="▶  Play"); play_btn.add_css_class("pl-card-play-btn")
        play_btn.connect("clicked", lambda *a, n=name: self._pl_load_and_play(n))

        add_btn = Gtk.Button(label="＋  Add Songs"); add_btn.add_css_class("pl-card-add-btn")
        add_btn.connect("clicked", lambda *a, n=name: self._pl_add_songs_dialog(n))

        del_btn = Gtk.Button(label="🗑"); del_btn.add_css_class("pl-card-del-btn")
        del_btn.set_tooltip_text("Delete playlist")
        del_btn.connect("clicked", lambda *a, n=name: self._pl_delete_dialog(n))

        btn_row.append(folder_btn); btn_row.append(play_btn); btn_row.append(add_btn); btn_row.append(del_btn)

        # Pencil edit button — in header next to name
        edit_btn = Gtk.Button(); edit_btn.add_css_class("pl-card-edit-btn")
        edit_ico = Gtk.Image.new_from_icon_name("document-edit-symbolic"); edit_ico.set_pixel_size(13)
        edit_btn.set_child(edit_ico)
        edit_btn.set_tooltip_text("Rename / change icon")
        edit_btn.set_valign(Gtk.Align.CENTER)

        # Playlist icon button — shows + by default, image or emoji when set
        pl_icon_val = self.icons.get_pl(name)
        pl_icon_btn = Gtk.Button()
        pl_icon_btn.add_css_class("pl-set-icon-btn")
        pl_icon_btn.set_valign(Gtk.Align.CENTER)
        pl_icon_display = Gtk.Box()  # holds the icon widget (emoji label or picture)
        pl_icon_display.set_valign(Gtk.Align.CENTER); pl_icon_display.set_halign(Gtk.Align.CENTER)
        pl_icon_display.set_hexpand(False); pl_icon_display.set_vexpand(False)
        self._update_icon_box(pl_icon_display, pl_icon_val, 54)
        pl_icon_btn.set_child(pl_icon_display)
        pl_icon_btn.set_tooltip_text("Set a custom icon for this playlist")
        def _change_pl_icon(btn, n=name, disp=pl_icon_display, key=f"pl_{name}"):
            cur = self.icons.get_pl(n)
            def _on_pick(v, d=disp, nm=n):
                self.icons.set_pl(nm, v)
                self._update_icon_box(d, v, 54)
                self._sidebar_refresh_playlists()
            self._pick_icon(cur, _on_pick)
        pl_icon_btn.connect("clicked", _change_pl_icon)

        # Wire edit button with access to icon display and name label
        edit_btn.connect("clicked", lambda *a, n=name, nl=name_lbl, d=pl_icon_display:
            self._pl_edit_dialog(n, nl, d))

        hdr.append(collapse_btn); hdr.append(pl_icon_btn); hdr.append(name_box); hdr.append(edit_btn); hdr.append(btn_row)
        card.append(hdr)

        # Track list (collapsible, expanded by default)
        tracks_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        tracks_container.set_visible(True)

        if not tracks:
            hint = Gtk.Label(label="No tracks yet — click  ＋ Add Songs  to get started")
            hint.add_css_class("pl-empty-hint"); hint.set_halign(Gtk.Align.START)
            tracks_container.append(hint)
        else:
            for tp in tracks:
                tracks_container.append(self._mk_pl_card_row(name, tp, count_lbl))

        card.append(tracks_container)

        # Wire collapse toggle
        def _collapse(*a, ico=collapse_ico, box=tracks_container):
            vis = not box.get_visible()
            box.set_visible(vis)
            ico.set_from_icon_name("pan-down-symbolic" if vis else "pan-end-symbolic")
        collapse_btn.connect("clicked", _collapse)

        return card

    def _mk_pl_card_row(self, pl_name, track_path, count_lbl_ref):
        """One track row inside a playlist card."""
        item = MediaItem(track_path)
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row.add_css_class("pl-card-row")

        # Track icon — shown left of title, clickable to change; shows + by default
        tr_icon_val = self.icons.get_tr(str(track_path))
        tr_icon_btn = Gtk.Button()
        tr_icon_btn.add_css_class("tr-set-icon-btn")
        tr_icon_btn.set_tooltip_text("Set icon for this track")
        tr_icon_btn.set_valign(Gtk.Align.CENTER)
        tr_icon_display = Gtk.Box()
        tr_icon_display.set_valign(Gtk.Align.CENTER); tr_icon_display.set_halign(Gtk.Align.CENTER)
        self._update_icon_box(tr_icon_display, tr_icon_val, 38)
        tr_icon_btn.set_child(tr_icon_display)
        def _change_tr_icon(btn, p=str(track_path), d=tr_icon_display):
            cur = self.icons.get_tr(p)
            def _on_pick(v, disp=d, path=p):
                self.icons.set_tr(path, v)
                self._update_icon_box(disp, v, 38)
            self._pick_icon(cur, _on_pick)
        tr_icon_btn.connect("clicked", _change_tr_icon)

        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1); info.set_hexpand(True)
        t = Gtk.Label(label=item.title); t.add_css_class("pl-card-row-title")
        t.set_halign(Gtk.Align.START); t.set_ellipsize(Pango.EllipsizeMode.END)
        m = Gtk.Label(label=item.artist or track_path.parent.name)
        m.add_css_class("pl-card-row-meta"); m.set_halign(Gtk.Align.START); m.set_ellipsize(Pango.EllipsizeMode.END)
        info.append(t); info.append(m)

        dur = Gtk.Label(label=item.fmt_dur()); dur.add_css_class("pl-card-row-dur"); dur.set_valign(Gtk.Align.CENTER)

        # Pencil edit button for track
        tr_edit_btn = Gtk.Button(); tr_edit_btn.add_css_class("pl-card-edit-btn")
        tr_edit_ico = Gtk.Image.new_from_icon_name("document-edit-symbolic"); tr_edit_ico.set_pixel_size(12)
        tr_edit_btn.set_child(tr_edit_ico)
        tr_edit_btn.set_tooltip_text("Edit track info / icon")
        tr_edit_btn.set_valign(Gtk.Align.CENTER)
        tr_edit_btn.set_size_request(30, 30)
        tr_edit_btn.connect("clicked", lambda *a, p=str(track_path), d=tr_icon_display, tl=t:
            self._tr_edit_dialog(p, d, tl))

        rm_btn = Gtk.Button(label="✕"); rm_btn.add_css_class("pl-card-row-remove")
        rm_btn.set_tooltip_text("Remove from playlist")
        rm_btn.set_valign(Gtk.Align.CENTER)
        rm_btn.connect("clicked", lambda *a, p=track_path, n=pl_name: self._pl_remove_track(p, n))

        row.append(tr_icon_btn); row.append(info); row.append(dur); row.append(tr_edit_btn); row.append(rm_btn)

        # Click row to play just this playlist
        gc = Gtk.GestureClick()
        gc.connect("released", lambda *a, n=pl_name, p=str(track_path): self._pl_load_and_play(n, start_path=p))
        row.add_controller(gc)
        return row

    def _tr_edit_dialog(self, track_path, icon_display, title_lbl):
        """Edit dialog for a track — change icon and display title."""
        from pathlib import Path as _Path
        p = _Path(track_path)
        current_title = title_lbl.get_label()

        dlg = Gtk.Dialog(title="Edit Track", transient_for=self, modal=True)
        dlg.set_default_size(380, 210)
        content = dlg.get_content_area()
        content.set_spacing(0)

        # Header
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        hdr.set_margin_top(16); hdr.set_margin_bottom(14)
        hdr.set_margin_start(18); hdr.set_margin_end(18)
        hdr_ico = Gtk.Image.new_from_icon_name("document-edit-symbolic"); hdr_ico.set_pixel_size(16)
        hdr_lbl = Gtk.Label(label=f'Edit  \u201c{current_title}\u201d')
        hdr_lbl.add_css_class("settings-row-title"); hdr_lbl.set_hexpand(True); hdr_lbl.set_halign(Gtk.Align.START)
        hdr_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        hdr.append(hdr_ico); hdr.append(hdr_lbl)
        content.append(hdr)

        # Body: [icon preview + change btn] | [title field]
        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        body.set_margin_start(18); body.set_margin_end(18); body.set_margin_bottom(14)

        icon_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        icon_col.set_valign(Gtk.Align.CENTER)

        icon_preview_box = Gtk.Box()
        icon_preview_box.add_css_class("tr-set-icon-btn")
        icon_preview_box.set_size_request(42, 42)
        icon_preview_box.set_halign(Gtk.Align.CENTER)
        cur_val = self.icons.get_tr(track_path)
        self._update_icon_box(icon_preview_box, cur_val, 38)

        change_icon_btn = Gtk.Button(label="🎨  Icon")
        change_icon_btn.add_css_class("pl-card-add-btn")
        change_icon_btn.set_halign(Gtk.Align.CENTER)

        icon_col.append(icon_preview_box); icon_col.append(change_icon_btn)

        name_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        name_col.set_hexpand(True); name_col.set_valign(Gtk.Align.CENTER)
        name_field_lbl = Gtk.Label(label="Display title")
        name_field_lbl.add_css_class("settings-row-sub"); name_field_lbl.set_halign(Gtk.Align.START)
        title_entry = Gtk.Entry(); title_entry.set_text(current_title); title_entry.set_hexpand(True)
        name_col.append(name_field_lbl); name_col.append(title_entry)

        body.append(icon_col); body.append(name_col)
        content.append(body)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        content.append(sep)

        action_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        action_row.set_margin_start(18); action_row.set_margin_end(18)
        action_row.set_margin_top(12); action_row.set_margin_bottom(16)
        action_row.set_halign(Gtk.Align.END)

        save_btn = Gtk.Button(label="✓  Save"); save_btn.add_css_class("pl-card-play-btn")
        cancel_btn = Gtk.Button(label="Cancel"); cancel_btn.add_css_class("banner-revert-btn")

        def _change_icon(*a):
            cur = self.icons.get_tr(track_path)
            def _on_pick(v):
                self.icons.set_tr(track_path, v)
                self._update_icon_box(icon_preview_box, v, 38)
                self._update_icon_box(icon_display, v, 38)
            self._pick_icon(cur, _on_pick)

        def _save(*a):
            new_title = title_entry.get_text().strip()
            if new_title:
                title_lbl.set_label(new_title)
            dlg.destroy()

        cancel_btn.connect("clicked", lambda *a: dlg.destroy())
        change_icon_btn.connect("clicked", _change_icon)
        save_btn.connect("clicked", _save)
        title_entry.connect("activate", _save)

        action_row.append(cancel_btn); action_row.append(save_btn)
        content.append(action_row)
        dlg.present()

    def _pl_create_dialog(self, *a):
        """Show inline create-playlist dialog."""
        dlg = Gtk.Dialog(title="New Playlist", transient_for=self, modal=True)
        dlg.set_default_size(340, -1)
        content = dlg.get_content_area()
        content.set_spacing(10); content.set_margin_top(16); content.set_margin_bottom(10)
        content.set_margin_start(18); content.set_margin_end(18)

        lbl = Gtk.Label(label="Playlist name:"); lbl.set_halign(Gtk.Align.START)
        entry = Gtk.Entry(); entry.set_placeholder_text("e.g. Chill Vibes")
        entry.set_activates_default(True)
        content.append(lbl); content.append(entry)

        dlg.add_button("Cancel", Gtk.ResponseType.CANCEL)
        ok = dlg.add_button("Create", Gtk.ResponseType.OK)
        ok.add_css_class("open-btn-primary"); ok.set_receives_default(True)

        def _on_resp(d, r):
            if r == Gtk.ResponseType.OK:
                raw = entry.get_text().strip()
                if raw:
                    # Sanitize: replace / and null chars
                    safe = raw.replace("/", "-").replace("\x00", "").strip()
                    folder = self._pl_folder(safe)
                    folder.mkdir(parents=True, exist_ok=True)
                    self._pl_refresh_cards()
            d.destroy()

        dlg.connect("response", _on_resp)
        dlg.present()

    def _pl_add_songs_dialog(self, pl_name):
        """Open file chooser; copy selected audio files into playlist folder."""
        fc = Gtk.FileChooserDialog(title=f"Add Songs to '{pl_name}'",
                                   transient_for=self, modal=True,
                                   action=Gtk.FileChooserAction.OPEN)
        fc.set_select_multiple(True)
        ff = Gtk.FileFilter(); ff.set_name("Audio files")
        for fmt in AUDIO_FORMATS: ff.add_pattern(f"*{fmt}")
        fc.add_filter(ff)
        fc.add_button("Cancel", Gtk.ResponseType.CANCEL)
        ok = fc.add_button("Add", Gtk.ResponseType.OK)
        ok.add_css_class("open-btn-primary")

        def _on_resp(d, r):
            if r == Gtk.ResponseType.OK:
                folder = self._pl_folder(pl_name)
                folder.mkdir(parents=True, exist_ok=True)
                files = d.get_files()
                n = files.get_n_items() if files else 0
                import shutil
                for i in range(n):
                    gfile = files.get_item(i)
                    src = Path(gfile.get_path())
                    dst = folder / src.name
                    # Avoid overwrite: append _2, _3, etc.
                    if dst.exists() and dst != src:
                        stem, suffix = src.stem, src.suffix
                        counter = 2
                        while dst.exists():
                            dst = folder / f"{stem}_{counter}{suffix}"
                            counter += 1
                    if not dst.exists():
                        shutil.copy2(src, dst)
                self._pl_refresh_cards()
            d.destroy()

        fc.connect("response", _on_resp)
        fc.present()

    def _icon_widget(self, value, size=20):
        """Return a widget for an icon value: scaled image for img: paths, Gtk.Label for emoji/+."""
        if value and value.startswith("img:"):
            img_path = value[4:]
            try:
                pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(img_path, size, size, False)
                pic = Gtk.Picture.new_for_pixbuf(pb)
                pic.set_size_request(size, size)
                pic.set_hexpand(False); pic.set_vexpand(False)
                pic.set_halign(Gtk.Align.CENTER); pic.set_valign(Gtk.Align.CENTER)
                return pic
            except Exception:
                lbl = Gtk.Label(label="🖼")
                lbl.set_size_request(size, size)
                return lbl
        lbl = Gtk.Label(label=value if value else "+")
        lbl.set_size_request(size, size)
        return lbl

    def _update_icon_box(self, box, value, size=20):
        """Clear box and repopulate with the right icon widget."""
        child = box.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            box.remove(child)
            child = nxt
        box.append(self._icon_widget(value, size))

    def _pick_icon(self, current_value, on_pick):
        """Show icon picker dialog: image upload, custom emoji entry, or palette. on_pick(value) called."""
        dlg = Gtk.Dialog(title="Choose Icon", transient_for=self, modal=True)
        dlg.set_default_size(360, 340)
        content = dlg.get_content_area()
        content.set_spacing(0)

        hdr_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        hdr_box.set_margin_top(14); hdr_box.set_margin_bottom(6)
        hdr_box.set_margin_start(16); hdr_box.set_margin_end(16)
        hdr_lbl = Gtk.Label(label="Choose an icon")
        hdr_lbl.add_css_class("settings-row-title"); hdr_lbl.set_hexpand(True); hdr_lbl.set_halign(Gtk.Align.START)
        clear_btn = Gtk.Button(label="Clear icon"); clear_btn.add_css_class("banner-revert-btn")
        def _clear(*a):
            on_pick(""); dlg.destroy()
        clear_btn.connect("clicked", _clear)
        hdr_box.append(hdr_lbl); hdr_box.append(clear_btn)
        content.append(hdr_box)

        # Image upload row
        img_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        img_row.set_margin_start(16); img_row.set_margin_end(16); img_row.set_margin_bottom(4)
        img_lbl = Gtk.Label(label="Image:")
        img_lbl.add_css_class("settings-row-sub"); img_lbl.set_valign(Gtk.Align.CENTER)
        img_upload_btn = Gtk.Button(label="📁 Upload PNG / JPG")
        img_upload_btn.add_css_class("pl-card-play-btn"); img_upload_btn.set_hexpand(True)
        # Store key_label ref so copy_image can name the file
        _img_key = {"v": current_value or "icon"}
        def _upload_image(*a):
            fc = Gtk.FileDialog()
            fc.set_title("Choose an image")
            img_filter = Gtk.FileFilter()
            img_filter.set_name("Images (PNG, JPG, JPEG, WebP, GIF)")
            for pat in ["*.png","*.jpg","*.jpeg","*.webp","*.gif","*.PNG","*.JPG","*.JPEG"]:
                img_filter.add_pattern(pat)
            filters = Gio.ListStore.new(Gtk.FileFilter)
            filters.append(img_filter)
            fc.set_filters(filters)
            def _done(dialog, result):
                try:
                    f = dialog.open_finish(result)
                    if f:
                        src = f.get_path()
                        val = self.icons.copy_image(src, _img_key["v"])
                        on_pick(val); dlg.destroy()
                except Exception:
                    pass
            fc.open(dlg, None, _done)
        img_upload_btn.connect("clicked", _upload_image)
        img_row.append(img_lbl); img_row.append(img_upload_btn)
        content.append(img_row)

        # Custom emoji entry row
        custom_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        custom_row.set_margin_start(16); custom_row.set_margin_end(16); custom_row.set_margin_bottom(8)
        custom_lbl = Gtk.Label(label="Emoji:")
        custom_lbl.add_css_class("settings-row-sub"); custom_lbl.set_valign(Gtk.Align.CENTER)
        custom_entry = Gtk.Entry()
        custom_entry.set_placeholder_text("Paste any emoji e.g. 🦋")
        custom_entry.set_max_length(4)
        custom_entry.set_hexpand(True)
        cur_emoji = current_value if current_value and not current_value.startswith("img:") else ""
        if cur_emoji: custom_entry.set_text(cur_emoji)
        custom_apply = Gtk.Button(label="Use")
        custom_apply.add_css_class("pl-card-play-btn")
        def _use_custom(*a):
            txt = custom_entry.get_text().strip()
            if txt: on_pick(txt); dlg.destroy()
        custom_apply.connect("clicked", _use_custom)
        custom_entry.connect("activate", _use_custom)
        custom_row.append(custom_lbl); custom_row.append(custom_entry); custom_row.append(custom_apply)
        content.append(custom_row)

        # Divider label
        grid_lbl = Gtk.Label(label="OR PICK FROM PALETTE")
        grid_lbl.add_css_class("settings-section-label"); grid_lbl.set_halign(Gtk.Align.START)
        grid_lbl.set_margin_start(16); grid_lbl.set_margin_bottom(4)
        content.append(grid_lbl)

        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_margin_start(12); scroll.set_margin_end(12); scroll.set_margin_bottom(12)

        flow = Gtk.FlowBox()
        flow.set_max_children_per_line(8)
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_row_spacing(4); flow.set_column_spacing(4)
        flow.set_homogeneous(True)

        for emoji in ICON_PALETTE:
            btn = Gtk.Button(label=emoji); btn.add_css_class("icon-pick-btn")
            if emoji == current_value: btn.add_css_class("icon-pick-active")
            def _pick(b, e=emoji):
                on_pick(e); dlg.destroy()
            btn.connect("clicked", _pick)
            flow.append(btn)

        scroll.set_child(flow)
        content.append(scroll)
        dlg.present()

    def _pl_edit_dialog(self, name, name_lbl, icon_display):
        """Edit dialog — rename playlist and/or change its icon."""
        dlg = Gtk.Dialog(title="Edit Playlist", transient_for=self, modal=True)
        dlg.set_default_size(380, 210)
        content = dlg.get_content_area()
        content.set_spacing(0)

        # Header
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        hdr.set_margin_top(16); hdr.set_margin_bottom(14)
        hdr.set_margin_start(18); hdr.set_margin_end(18)
        hdr_ico = Gtk.Image.new_from_icon_name("document-edit-symbolic"); hdr_ico.set_pixel_size(16)
        hdr_lbl = Gtk.Label(label=f'Edit  \u201c{name}\u201d')
        hdr_lbl.add_css_class("settings-row-title"); hdr_lbl.set_hexpand(True); hdr_lbl.set_halign(Gtk.Align.START)
        hdr.append(hdr_ico); hdr.append(hdr_lbl)
        content.append(hdr)

        # Body row: [icon preview + change btn] | [name field]
        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        body.set_margin_start(18); body.set_margin_end(18); body.set_margin_bottom(14)

        # Left: icon preview box + Change Icon button stacked
        icon_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        icon_col.set_valign(Gtk.Align.CENTER)

        icon_preview_box = Gtk.Box()
        icon_preview_box.add_css_class("pl-set-icon-btn")
        icon_preview_box.set_size_request(58, 58)
        icon_preview_box.set_halign(Gtk.Align.CENTER)
        cur_val = self.icons.get_pl(name)
        self._update_icon_box(icon_preview_box, cur_val, 54)

        change_icon_btn = Gtk.Button(label="🎨  Icon")
        change_icon_btn.add_css_class("pl-card-add-btn")
        change_icon_btn.set_halign(Gtk.Align.CENTER)

        icon_col.append(icon_preview_box); icon_col.append(change_icon_btn)

        # Right: name label + entry
        name_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        name_col.set_hexpand(True); name_col.set_valign(Gtk.Align.CENTER)
        name_field_lbl = Gtk.Label(label="Playlist name")
        name_field_lbl.add_css_class("settings-row-sub"); name_field_lbl.set_halign(Gtk.Align.START)
        rename_entry = Gtk.Entry(); rename_entry.set_text(name); rename_entry.set_hexpand(True)
        name_col.append(name_field_lbl); name_col.append(rename_entry)

        body.append(icon_col); body.append(name_col)
        content.append(body)

        # Separator + action buttons
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        content.append(sep)

        action_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        action_row.set_margin_start(18); action_row.set_margin_end(18)
        action_row.set_margin_top(12); action_row.set_margin_bottom(16)
        action_row.set_halign(Gtk.Align.END)

        save_btn = Gtk.Button(label="✓  Save"); save_btn.add_css_class("pl-card-play-btn")
        cancel_btn = Gtk.Button(label="Cancel"); cancel_btn.add_css_class("banner-revert-btn")

        def _change_icon(*a):
            cur = self.icons.get_pl(name)
            def _on_pick(v):
                self.icons.set_pl(name, v)
                self._update_icon_box(icon_preview_box, v, 54)
                if icon_display:
                    self._update_icon_box(icon_display, v, 54)
                self._sidebar_refresh_playlists()
            self._pick_icon(cur, _on_pick)

        def _save(*a):
            new_name = rename_entry.get_text().strip()
            if new_name and new_name != name:
                old_folder = self._pl_folder(name)
                new_folder = PLAYLISTS_DIR / new_name
                if not new_folder.exists():
                    old_folder.rename(new_folder)
                    old_val = self.icons.get_pl(name)
                    self.icons.set_pl(new_name, old_val)
                    self.icons.set_pl(name, "")
                    name_lbl.set_label(new_name)
            dlg.destroy()
            self._pl_refresh_cards()
            self._sidebar_refresh_playlists()

        cancel_btn.connect("clicked", lambda *a: dlg.destroy())
        change_icon_btn.connect("clicked", _change_icon)
        save_btn.connect("clicked", _save)
        rename_entry.connect("activate", _save)

        action_row.append(cancel_btn); action_row.append(save_btn)
        content.append(action_row)
        dlg.present()

    def _pl_open_folder(self, pl_name):
        """Open the playlist folder in the system file manager."""
        folder = self._pl_folder(pl_name)
        folder.mkdir(parents=True, exist_ok=True)
        try:
            Gio.AppInfo.launch_default_for_uri(folder.as_uri(), None)
        except Exception:
            try: subprocess.Popen(["xdg-open", str(folder)])
            except Exception: pass

    def _pl_remove_track(self, track_path, pl_name):
        """Remove (delete) a track file from the playlist folder."""
        try:
            Path(track_path).unlink(missing_ok=True)
        except Exception:
            pass
        self._pl_refresh_cards()

    def _pl_delete_dialog(self, pl_name):
        """Confirm then delete a playlist folder and all its contents."""
        dlg = Gtk.Dialog(title="Delete Playlist", transient_for=self, modal=True)
        dlg.set_default_size(320, -1)
        content = dlg.get_content_area()

        msg_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        msg_box.set_margin_top(20); msg_box.set_margin_bottom(10)
        msg_box.set_margin_start(20); msg_box.set_margin_end(20)

        title_lbl = Gtk.Label(label=f"Delete \"{pl_name}\"?")
        title_lbl.add_css_class("settings-row-title"); title_lbl.set_halign(Gtk.Align.START)
        sub_lbl = Gtk.Label(label="This will permanently delete the folder and all copies of songs inside it.")
        sub_lbl.add_css_class("settings-row-sub"); sub_lbl.set_halign(Gtk.Align.START)
        sub_lbl.set_wrap(True)

        msg_box.append(title_lbl); msg_box.append(sub_lbl)
        content.append(msg_box)

        action_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        action_row.set_margin_start(20); action_row.set_margin_end(20); action_row.set_margin_bottom(16)
        action_row.set_halign(Gtk.Align.END)

        cancel_btn = Gtk.Button(label="Cancel"); cancel_btn.add_css_class("banner-revert-btn")
        del_btn = Gtk.Button(label="🗑  Delete"); del_btn.add_css_class("pl-card-del-btn")

        def _delete(*a):
            folder = self._pl_folder(pl_name)
            try:
                if folder.exists():
                    import shutil as _sh
                    _sh.rmtree(str(folder))
            except Exception as e:
                err_dlg = Gtk.MessageDialog(transient_for=self, modal=True,
                    message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.OK,
                    text=f"Could not delete: {e}")
                err_dlg.connect("response", lambda d, *a: d.destroy())
                err_dlg.present()
                return
            dlg.destroy()
            self._pl_refresh_cards()

        cancel_btn.connect("clicked", lambda *a: dlg.destroy())
        del_btn.connect("clicked", _delete)

        action_row.append(cancel_btn); action_row.append(del_btn)
        content.append(action_row)
        dlg.present()

    def _pl_load_and_play(self, pl_name, start_path=None):
        """Load all tracks from a playlist into the queue and start playing."""
        tracks = self._pl_tracks(pl_name)
        if not tracks: return
        items = [MediaItem(t) for t in tracks]
        self._playlist = items
        self._pl_idx = 0
        if start_path:
            for i, it in enumerate(items):
                if it.path == str(start_path):
                    self._pl_idx = i; break
        self._play_idx(self._pl_idx)
        # Switch to music page so user can see whats playing
        self._nav_to(self.NAV_MUSIC)
        self._sidebar_refresh_playlists()

    # =========================================================
    #   SETTINGS — PREVIEW / PENDING CHANGES SYSTEM
    # =========================================================
    def _settings_mark_dirty(self):
        if hasattr(self, '_settings_banner'):
            self._settings_banner.set_visible(True)

    def _settings_apply(self, *a):
        """Commit all pending values to live app + disk."""
        p = self._pending

        if "dark_mode" in p and p["dark_mode"] != self._dark:
            self._dark = p["dark_mode"]
            self.cfg.set("dark_mode", self._dark)
            self._load_css()
            self._sync_theme_ui()

        if "gui_scale" in p:
            self.cfg.set("gui_scale", p["gui_scale"])
            self._apply_gui_scale(p["gui_scale"])

        if "anim_speed" in p:
            self.cfg.set("anim_speed", p["anim_speed"])
            self._anim_speed = p["anim_speed"]
            anim_map = {"smooth": 280, "normal": 120, "fast": 40}
            self._stack.set_transition_duration(anim_map.get(p["anim_speed"], 120))

        if "volume" in p:
            self.cfg.set("volume", p["volume"])
            self.engine.set_volume(min(p["volume"], 1.0))
            try: self.engine._pipe.set_property("volume", p["volume"])
            except: pass
            self._vol.set_value(p["volume"])

        if "speed" in p:
            self.cfg.set("speed", p["speed"])
            self._speed = p["speed"]
            self._speed_lbl_w.set_label(self._fmt_spd(p["speed"]))
            if self._cur:
                try: self.engine.set_speed(p["speed"])
                except: pass

        if "repeat" in p:
            self.cfg.set("repeat", p["repeat"])
            self._repeat = p["repeat"]

        if "video_fit" in p:
            self.cfg.set("video_fit", p["video_fit"])
            fit_map = {"contain": Gtk.ContentFit.CONTAIN, "fill": Gtk.ContentFit.FILL,
                       "cover": Gtk.ContentFit.COVER, "native": Gtk.ContentFit.CONTAIN}
            self._vid_pic.set_content_fit(fit_map.get(p["video_fit"], Gtk.ContentFit.CONTAIN))

        self.cfg.save()
        self._pending = {}
        if hasattr(self, '_settings_banner'):
            self._settings_banner.set_visible(False)

    def _settings_revert(self, *a):
        """Discard all pending values — restore settings widgets to current live state."""
        self._pending = {}

        # Restore theme widget
        if hasattr(self, '_settings_theme_sw'):
            self._syncing_theme = True
            self._settings_theme_sw.set_active(self._dark)
            self._settings_theme_lbl.set_label("Dark Mode" if self._dark else "Light Mode")
            self._syncing_theme = False

        # Restore scale widget
        live_scale = self.cfg.get("gui_scale", 1.0)
        if hasattr(self, '_scale_val_lbl'):
            self._scale_val_lbl.set_label(f"{int(live_scale*100)}%")
        if hasattr(self, '_scale_slider_ref'):
            self._scale_slider_ref.set_value(live_scale)

        # Restore volume widget
        live_vol = self.cfg.get("volume", 0.8)
        if hasattr(self, '_settings_vol_lbl'):
            self._settings_vol_lbl.set_label(f"{int(live_vol*100)}%")
        if hasattr(self, '_settings_vol_slider'):
            self._settings_vol_slider.set_value(live_vol)

        # Restore speed widget (toggle buttons refresh on revert via _pending clear)
        # Restore anim widget — force toggle buttons back
        if hasattr(self, '_settings_banner'):
            self._settings_banner.set_visible(False)

    # =========================================================
    #   SETTINGS PAGE
    # =========================================================
    def _mk_settings_pg(self):
        outer_wrap = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        outer_wrap.set_hexpand(True); outer_wrap.set_vexpand(True)

        # ── Confirm Banner ─────────────────────────────────────
        self._settings_banner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self._settings_banner.add_css_class("settings-banner")
        self._settings_banner.set_visible(False)
        banner_ico = Gtk.Image.new_from_icon_name("dialog-information-symbolic")
        banner_ico.set_pixel_size(14); banner_ico.add_css_class("banner-icon")
        banner_lbl = Gtk.Label(label="You have unsaved changes")
        banner_lbl.add_css_class("banner-lbl"); banner_lbl.set_hexpand(True); banner_lbl.set_halign(Gtk.Align.START)
        apply_btn = Gtk.Button(label="Apply"); apply_btn.add_css_class("banner-apply-btn")
        apply_btn.connect("clicked", self._settings_apply)
        revert_btn = Gtk.Button(label="Revert"); revert_btn.add_css_class("banner-revert-btn")
        revert_btn.connect("clicked", self._settings_revert)
        self._settings_banner.append(banner_ico); self._settings_banner.append(banner_lbl)
        self._settings_banner.append(revert_btn); self._settings_banner.append(apply_btn)
        outer_wrap.append(self._settings_banner)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_hexpand(True); scroll.set_vexpand(True)
        outer_wrap.append(scroll)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        outer.add_css_class("settings-outer"); outer.set_hexpand(True); outer.set_vexpand(True)

        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        inner.set_margin_top(16); inner.set_margin_bottom(24)
        inner.set_margin_start(20); inner.set_margin_end(20)
        inner.set_hexpand(True)

        def section(title):
            lbl = Gtk.Label(label=title); lbl.add_css_class("settings-section-label")
            lbl.set_halign(Gtk.Align.START); lbl.set_margin_top(18); lbl.set_margin_bottom(2)
            inner.append(lbl)

        def card():
            c = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            c.add_css_class("settings-card"); c.set_hexpand(True)
            inner.append(c); return c

        def row(c, title, subtitle=None, right=None):
            r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            r.add_css_class("settings-row"); r.set_hexpand(True)
            lbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            lbox.set_hexpand(True); lbox.set_valign(Gtk.Align.CENTER)
            t = Gtk.Label(label=title); t.add_css_class("settings-row-title"); t.set_halign(Gtk.Align.START)
            lbox.append(t)
            if subtitle:
                s = Gtk.Label(label=subtitle); s.add_css_class("settings-row-sub"); s.set_halign(Gtk.Align.START)
                lbox.append(s)
            r.append(lbox)
            if right: r.append(right)
            c.append(r); return r

        # ── ABOUT ─────────────────────────────────────────────
        about_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        about_card.add_css_class("settings-about-card"); about_card.set_hexpand(True)
        about_card.set_margin_top(4)

        ah = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        ico = Gtk.Image.new_from_icon_name("multimedia-player"); ico.set_pixel_size(40)
        ico.set_valign(Gtk.Align.CENTER)
        ah.append(ico)
        ainfo = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        ainfo.set_valign(Gtk.Align.CENTER)
        n = Gtk.Label(label="Nebula Vantage"); n.add_css_class("settings-about-name"); n.set_halign(Gtk.Align.START)
        badges = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        for b in [VERSION, "GTK4", "GStreamer"]:
            bl = Gtk.Label(label=b); bl.add_css_class("settings-badge"); badges.append(bl)
        sub = Gtk.Label(label="by Nebula Projects  ·  org.nebulaprojects.vantage")
        sub.add_css_class("settings-about-sub"); sub.set_halign(Gtk.Align.START)
        ainfo.append(n); ainfo.append(badges); ainfo.append(sub)
        ah.append(ainfo); about_card.append(ah)
        inner.append(about_card)

        # ── APPEARANCE ────────────────────────────────────────
        section("APPEARANCE")
        c = card()

        theme_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        theme_row.add_css_class("settings-row"); theme_row.set_hexpand(True)
        tlb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1); tlb.set_hexpand(True); tlb.set_valign(Gtk.Align.CENTER)
        tlb.append(self._slbl("Theme")); tlb.append(self._ssub("Choose light or dark interface"))
        theme_row.append(tlb)

        sw_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        sw_box.set_valign(Gtk.Align.CENTER)
        sw_lbl = Gtk.Label(label="Dark Mode" if self._dark else "Light Mode")
        sw_lbl.add_css_class("settings-row-value")
        self._settings_theme_lbl = sw_lbl
        self._settings_theme_sw = Gtk.Switch()
        self._settings_theme_sw.set_active(self._dark)
        self._settings_theme_sw.set_valign(Gtk.Align.CENTER)
        def _on_settings_theme(sw, _param):
            if self._syncing_theme: return
            dark = sw.get_active()
            self._settings_theme_lbl.set_label("Dark Mode" if dark else "Light Mode")
            self._pending["dark_mode"] = dark
            self._settings_mark_dirty()
        self._settings_theme_sw.connect("notify::active", _on_settings_theme)
        sw_box.append(sw_lbl); sw_box.append(self._settings_theme_sw)
        theme_row.append(sw_box); c.append(theme_row)

        # GUI Scale
        scale_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        scale_row.add_css_class("settings-row"); scale_row.set_hexpand(True)
        slb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1); slb.set_hexpand(True); slb.set_valign(Gtk.Align.CENTER)
        slb.append(self._slbl("Interface Scale")); slb.append(self._ssub("Scales entire UI — text, icons, layout (50–300%)"))
        scale_row.append(slb)
        scale_right = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        scale_right.set_valign(Gtk.Align.CENTER)
        self._scale_val_lbl = Gtk.Label(); self._scale_val_lbl.add_css_class("settings-row-value")
        self._scale_val_lbl.set_size_request(48, -1)
        cur_scale = self.cfg.get("gui_scale", 1.0)
        self._scale_val_lbl.set_label(f"{int(cur_scale*100)}%")
        gui_scale_slider = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
        gui_scale_slider.set_range(0.5, 3.0); gui_scale_slider.set_draw_value(False)
        gui_scale_slider.set_value(cur_scale); gui_scale_slider.set_size_request(200, -1)
        gui_scale_slider.add_css_class("vol-bar")
        self._scale_slider_ref = gui_scale_slider   # needed for revert
        for v in [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0]:
            gui_scale_slider.add_mark(v, Gtk.PositionType.BOTTOM, None)
        def _on_gui_scale(s):
            v = s.get_value()
            snapped = round(v * 4) / 4
            self._scale_val_lbl.set_label(f"{int(snapped*100)}%")
            self._pending["gui_scale"] = snapped   # preview only — no live apply
            self._settings_mark_dirty()
        gui_scale_slider.connect("value-changed", _on_gui_scale)
        scale_right.append(self._scale_val_lbl); scale_right.append(gui_scale_slider)
        scale_row.append(scale_right); c.append(scale_row)

        # Animation Speed
        anim_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        anim_row.add_css_class("settings-row"); anim_row.set_hexpand(True)
        alb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1); alb.set_hexpand(True); alb.set_valign(Gtk.Align.CENTER)
        alb.append(self._slbl("Animation Speed")); alb.append(self._ssub("Page transitions and UI animations"))
        anim_row.append(alb)
        anim_right = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        anim_right.set_valign(Gtk.Align.CENTER)
        cur_anim = self.cfg.get("anim_speed", "normal")
        anim_vals = [("Smooth", "smooth", 280), ("Normal", "normal", 120), ("Fast", "fast", 40)]
        for label, key, ms in anim_vals:
            b = Gtk.ToggleButton(label=label); b.add_css_class("settings-kbd")
            b.set_active(cur_anim == key)
            def _on_anim(btn, k=key, m=ms):
                if btn.get_active():
                    self._pending["anim_speed"] = k
                    self._settings_mark_dirty()
            b.connect("toggled", _on_anim)
            anim_right.append(b)
        anim_row.append(anim_right); c.append(anim_row)
        section("PLAYBACK")
        c = card()

        # Default volume
        vol_right = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        vol_right.set_valign(Gtk.Align.CENTER)
        self._settings_vol_lbl = Gtk.Label()
        self._settings_vol_lbl.add_css_class("settings-row-value")
        vol_slider = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
        vol_slider.set_range(0, 2.0); vol_slider.set_draw_value(False)
        vol_slider.set_value(self.cfg.get("volume", 0.8)); vol_slider.set_size_request(120, -1)
        vol_slider.add_css_class("vol-bar")
        self._settings_vol_slider = vol_slider   # needed for revert
        def _upd_vol_lbl(v): self._settings_vol_lbl.set_label(f"{int(v*100)}%")
        _upd_vol_lbl(self.cfg.get("volume", 0.8))
        def _on_setvol(s):
            v = s.get_value(); _upd_vol_lbl(v)
            self._pending["volume"] = v   # preview only — no live engine change
            self._settings_mark_dirty()
        vol_slider.connect("value-changed", _on_setvol)
        vol_right.append(self._settings_vol_lbl); vol_right.append(vol_slider)
        row(c, "Default Volume", "Volume level when app starts (0–200%)", vol_right)

        # Default speed
        spd_right = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        spd_right.set_valign(Gtk.Align.CENTER)
        for spd in [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]:
            b = Gtk.ToggleButton(label=self._fmt_spd(spd))
            b.add_css_class("settings-kbd")
            b.set_active(self._speed == spd)
            def _on_spd_set(btn, s=spd):
                if btn.get_active():
                    self._pending["speed"] = s
                    self._settings_mark_dirty()
            b.connect("toggled", _on_spd_set)
            spd_right.append(b)
        row(c, "Default Speed", "Playback speed on startup", spd_right)

        # Repeat mode
        rep_right = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        rep_right.set_valign(Gtk.Align.CENTER)
        for mode, label in [("off","Off"), ("one","One"), ("all","All")]:
            b = Gtk.ToggleButton(label=label); b.add_css_class("settings-kbd")
            b.set_active(self._repeat == mode)
            def _on_rep(btn, m=mode):
                if btn.get_active():
                    self._pending["repeat"] = m
                    self._settings_mark_dirty()
            b.connect("toggled", _on_rep)
            rep_right.append(b)
        row(c, "Repeat Mode", "Default repeat behaviour", rep_right)

        # Video Scaling
        vscale_right = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        vscale_right.set_valign(Gtk.Align.CENTER)
        vid_fit_modes = [
            ("contain", "Fit",    Gtk.ContentFit.CONTAIN, "Show full frame, letterbox if needed"),
            ("fill",    "Fill",   Gtk.ContentFit.FILL,    "Stretch to fill (may distort)"),
            ("cover",   "Crop",   Gtk.ContentFit.COVER,   "Fill and crop edges"),
            ("native",  "Native", Gtk.ContentFit.CONTAIN, "Native resolution, no upscale"),
        ]
        saved_fit = self.cfg.get("video_fit", "contain")
        for key, label, fit_val, tip in vid_fit_modes:
            b = Gtk.ToggleButton(label=label); b.add_css_class("settings-kbd")
            b.set_tooltip_text(tip); b.set_active(saved_fit == key)
            def _on_fit(btn, k=key, fv=fit_val):
                if btn.get_active():
                    self._pending["video_fit"] = k
                    self._settings_mark_dirty()
            b.connect("toggled", _on_fit)
            vscale_right.append(b)
        row(c, "Video Scaling", "How video fills the player area", vscale_right)

        # ── KEYBOARD SHORTCUTS ────────────────────────────────
        section("KEYBOARD SHORTCUTS")
        c = card()

        shortcuts = [
            ("Space", "Play / Pause", None),
            ("→ / ←", "Seek forward / backward 5 s", None),
            ("↑ / ↓", "Volume up / down", None),
            ("F", "Toggle fullscreen", None),
            ("M", "Mute / unmute", None),
            ("N", "Next track", None),
            ("P", "Previous track", None),
            ("[ / ]", "Speed down / up", None),
            ("Escape", "Exit fullscreen", None),
        ]
        for keys, desc, _ in shortcuts:
            kbx = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            kbx.set_valign(Gtk.Align.CENTER)
            for k in keys.split(" / "):
                kl = Gtk.Label(label=k.strip()); kl.add_css_class("settings-kbd"); kbx.append(kl)
                if keys.count("/") > 0 and k != keys.split(" / ")[-1]:
                    sep = Gtk.Label(label="/"); sep.add_css_class("settings-row-sub"); kbx.append(sep)
            row(c, desc, None, kbx)

        # ── FILE ASSOCIATIONS ─────────────────────────────────
        section("FILE ASSOCIATIONS")
        c = card()
        mime_right = Gtk.Button(label="Register")
        mime_right.add_css_class("open-btn-primary")
        mime_right.set_valign(Gtk.Align.CENTER)
        mime_right.connect("clicked", self._register_mime_from_settings)
        row(c, "Register MIME types", "Set Nebula Vantage as default for media files", mime_right)

        self._mime_status = Gtk.Label(label="")
        self._mime_status.add_css_class("settings-row-sub")
        self._mime_status.set_halign(Gtk.Align.START)
        self._mime_status.set_margin_start(16); self._mime_status.set_margin_top(4); self._mime_status.set_margin_bottom(4)
        c.append(self._mime_status)

        # ── SUPPORTED FORMATS ─────────────────────────────────
        section("SUPPORTED FORMATS")
        c = card()

        for label, fmts in [("Audio", sorted(AUDIO_FORMATS)), ("Video", sorted(VIDEO_FORMATS))]:
            r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            r.add_css_class("settings-row"); r.set_hexpand(True)
            tlb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4); tlb.set_hexpand(True)
            tlb.append(self._slbl(label))
            chips = Gtk.FlowBox(); chips.set_selection_mode(Gtk.SelectionMode.NONE)
            chips.set_hexpand(True); chips.set_row_spacing(2); chips.set_column_spacing(2)
            for f in fmts:
                ch = Gtk.Label(label=f); ch.add_css_class("settings-fmt-chip")
                chips.append(ch)
            tlb.append(chips); r.append(tlb); c.append(r)

        scroll.set_child(outer)
        outer.append(inner)
        return outer_wrap

    def _slbl(self, t):
        l = Gtk.Label(label=t); l.add_css_class("settings-row-title"); l.set_halign(Gtk.Align.START); return l
    def _ssub(self, t):
        l = Gtk.Label(label=t); l.add_css_class("settings-row-sub"); l.set_halign(Gtk.Align.START); return l

    def _set_theme(self, dark):
        if dark == self._dark: return
        self._dark = dark
        self.cfg.set("dark_mode", dark)
        self._load_css()
        self._sync_theme_ui()

    def _apply_gui_scale(self, scale):
        """
        True GUI scaling in GTK4 Wayland.
        GTK4 respects GDK_SCALE env var but only at startup, so we use
        gtk-xft-dpi + CSS em-based sizes on all key widgets.
        The CSS approach: set a base font-size on window that everything
        inherits, then use em units for all dimensions in a scale CSS layer.
        """
        if not hasattr(self, '_scale_css_provider'):
            self._scale_css_provider = Gtk.CssProvider()
            Gtk.StyleContext.add_provider_for_display(
                self.get_display(), self._scale_css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_USER)   # highest priority
        # Set root font-size so everything that uses rem/em scales
        # Also scale explicit px values on key structural elements
        base = int(scale * 100)
        btn_h  = max(20, int(28 * scale))
        bar_h  = max(32, int(40 * scale))
        sb_w   = max(120, int(196 * scale))
        ctrl_s = max(20, int(34 * scale))
        play_s = max(28, int(42 * scale))
        seek_h = max(2, int(3 * scale))
        font_s = max(8, int(13 * scale))
        scale_css = f"""
window {{ font-size: {base}%; }}
.left-sidebar {{ min-width: {sb_w}px; }}
.top-bar {{ min-height: {bar_h}px; }}
.open-btn {{ min-height: {btn_h}px; font-size: {max(9, int(11 * scale))}px; }}
.open-btn-primary {{ min-height: {btn_h}px; font-size: {max(9, int(11 * scale))}px; }}
.ctrl-btn {{ min-width: {ctrl_s}px; min-height: {ctrl_s}px; }}
.play-btn {{ min-width: {play_s}px; min-height: {play_s}px; }}
.seek-bar trough {{ min-height: {seek_h}px; }}
.vol-bar trough {{ min-height: {seek_h}px; }}
.sidebar-app-name {{ font-size: {max(9, int(13 * scale))}px; }}
.np-title {{ font-size: {max(9, int(12 * scale))}px; }}
.np-sub {{ font-size: {max(7, int(10 * scale))}px; }}
.settings-row-title {{ font-size: {max(9, int(12 * scale))}px; }}
.settings-row-sub {{ font-size: {max(7, int(10 * scale))}px; }}
.settings-about-name {{ font-size: {min(22, max(12, int(18 * scale)))}px; }}
"""
        self._scale_css_provider.load_from_string(scale_css)
        # Also update xft-dpi for font hinting
        settings = Gtk.Settings.get_default()
        if settings:
            settings.set_property("gtk-xft-dpi", int(96 * scale * 1024))
        # Programmatically resize stored widget refs — bypasses CSS specificity
        if hasattr(self, '_open_file_btn'):
            self._open_file_btn.set_size_request(int(90*scale), btn_h)
            self._open_folder_btn.set_size_request(int(96*scale), btn_h)
        if hasattr(self, '_play_btn'):
            self._play_btn.set_size_request(play_s, play_s)
        if hasattr(self, '_pb_wrapper'):
            new_h = max(38, int(85 * scale))
            self._pb_bar_height = float(new_h)
            self._pb_wrapper.set_size_request(-1, new_h)
            if hasattr(self, '_pb_clip'): self._pb_clip.set_size_request(-1, new_h)
        self._last_scale = scale

    def _register_mime_from_settings(self, *a):
        try:
            self._register_mime()
            self._mime_status.set_label("✓ Registered successfully")
        except Exception as e:
            self._mime_status.set_label(f"Error: {e}")


    def _refresh_music(self):
        while self._music_list.get_first_child(): self._music_list.remove(self._music_list.get_first_child())
        n = 0
        for idx, item in enumerate(self._playlist):
            if not item.is_video:
                n += 1
                self._music_list.append(self._mk_music_row(item, idx, n))

    def _mk_music_row(self, item, idx, num):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row.add_css_class("media-row")
        if self._cur and self._cur.path==item.path: row.add_css_class("now-playing")

        n = Gtk.Label(label=str(num)); n.add_css_class("row-num"); n.set_halign(Gtk.Align.END); n.set_valign(Gtk.Align.CENTER)
        ico = Gtk.Image.new_from_icon_name("audio-x-generic-symbolic"); ico.set_pixel_size(14); ico.add_css_class("row-icon"); ico.set_valign(Gtk.Align.CENTER)

        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1); info.set_hexpand(True)
        t = Gtk.Label(label=item.title); t.add_css_class("row-title"); t.set_halign(Gtk.Align.START); t.set_ellipsize(Pango.EllipsizeMode.END); t.set_max_width_chars(36)
        s = Gtk.Label(label=item.artist or Path(item.path).parent.name); s.add_css_class("row-meta"); s.set_halign(Gtk.Align.START); s.set_ellipsize(Pango.EllipsizeMode.END)
        info.append(t); info.append(s)

        dur = Gtk.Label(label=item.fmt_dur()); dur.add_css_class("row-dur"); dur.set_valign(Gtk.Align.CENTER)

        row.append(n); row.append(ico); row.append(info); row.append(dur)
        gc = Gtk.GestureClick(); gc.connect("released", lambda *a,i=idx: self._play_idx(i)); row.add_controller(gc)
        return row

    # =========================================================
    #   PLAYBACK BAR
    # =========================================================
    def _mk_playback_bar(self):
        self._pb_wrapper = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._pb_wrapper.set_size_request(-1, int(self._pb_bar_height))
        self._pb_wrapper.set_overflow(Gtk.Overflow.HIDDEN)   # clip content when bar is dragged small

        # ── Drag handle ──────────────────────────────────────────
        handle_ov = Gtk.Overlay()
        handle_ov.set_hexpand(True)

        self._pb_handle = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self._pb_handle.add_css_class("resize-handle")
        self._pb_handle.set_size_request(-1, 12)
        self._pb_handle.set_hexpand(True)
        self._pb_handle.set_cursor(Gdk.Cursor.new_from_name("ns-resize"))

        # Grip dots visual
        grip = Gtk.Label(label="· · · · ·")
        grip.add_css_class("resize-grip")
        grip.set_halign(Gtk.Align.CENTER)
        grip.set_hexpand(True)
        grip.set_valign(Gtk.Align.CENTER)
        self._pb_handle.append(grip)

        handle_ov.set_child(self._pb_handle)

        # Size badge overlay during drag
        self._pb_size_badge = Gtk.Label(label="")
        self._pb_size_badge.add_css_class("resize-size-badge")
        self._pb_size_badge.set_halign(Gtk.Align.CENTER)
        self._pb_size_badge.set_valign(Gtk.Align.CENTER)
        self._pb_size_badge.set_visible(False)
        handle_ov.add_overlay(self._pb_size_badge)

        # Drag gesture — attach to the handle widget with CAPTURE phase so it wins
        drag = Gtk.GestureDrag()
        drag.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        drag.connect("drag-begin",  self._on_pb_drag_begin)
        drag.connect("drag-update", self._on_pb_drag_update)
        drag.connect("drag-end",    self._on_pb_drag_end)
        self._pb_handle.add_controller(drag)
        self._pb_wrapper.append(handle_ov)

        bar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        bar.add_css_class("playback-bar")
        bar.set_vexpand(False)
        bar.set_valign(Gtk.Align.FILL)

        sr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        sr.set_margin_top(10); sr.set_margin_bottom(4)
        self._time_cur = Gtk.Label(label="0:00"); self._time_cur.add_css_class("time-lbl")
        self._seek = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
        self._seek.add_css_class("seek-bar"); self._seek.set_hexpand(True)
        self._seek.set_range(0, 100); self._seek.set_draw_value(False)
        self._seek.connect("change-value", self._on_seek_change)
        self._time_tot = Gtk.Label(label="0:00"); self._time_tot.add_css_class("time-lbl")
        sr.append(self._time_cur); sr.append(self._seek); sr.append(self._time_tot)
        bar.append(sr)

        cr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        cr.set_valign(Gtk.Align.CENTER); cr.set_margin_bottom(8)

        # LEFT
        left = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        left.set_size_request(220,-1); left.set_valign(Gtk.Align.CENTER)
        self._art_box = Gtk.Box(); self._art_box.set_size_request(42,42)
        self._art_box.set_valign(Gtk.Align.CENTER); self._art_box.set_halign(Gtk.Align.CENTER)
        self._art_box.add_css_class("art-box")
        self._art_ico = Gtk.Image.new_from_icon_name("audio-x-generic-symbolic")
        self._art_ico.set_pixel_size(18); self._art_ico.set_halign(Gtk.Align.CENTER); self._art_ico.set_valign(Gtk.Align.CENTER)
        self._art_ico.set_hexpand(True); self._art_ico.set_vexpand(True); self._art_ico.add_css_class("art-icon")
        self._art_img = Gtk.Image(); self._art_img.set_pixel_size(42); self._art_img.set_visible(False)
        self._art_box.append(self._art_ico); self._art_box.append(self._art_img)
        left.append(self._art_box)
        ti = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2); ti.set_valign(Gtk.Align.CENTER)
        self._np_title = Gtk.Label(label="Not Playing"); self._np_title.add_css_class("np-title")
        self._np_title.set_halign(Gtk.Align.START); self._np_title.set_ellipsize(Pango.EllipsizeMode.END); self._np_title.set_max_width_chars(17)
        self._np_sub = Gtk.Label(label=""); self._np_sub.add_css_class("np-sub")
        self._np_sub.set_halign(Gtk.Align.START); self._np_sub.set_ellipsize(Pango.EllipsizeMode.END)
        ti.append(self._np_title); ti.append(self._np_sub); left.append(ti)
        cr.append(left)

        # CENTER
        center = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        center.set_hexpand(True); center.set_halign(Gtk.Align.CENTER); center.set_valign(Gtk.Align.CENTER)

        def mk(icon, sz=34):
            b=Gtk.Button(); b.add_css_class("ctrl-btn")
            img=Gtk.Image.new_from_icon_name(icon); img.set_pixel_size(15); b.set_child(img); b.set_size_request(sz,sz); return b

        self._shuf_btn = mk("media-playlist-shuffle-symbolic"); self._shuf_btn.connect("clicked",self._tog_shuffle)
        prev_b = mk("media-skip-backward-symbolic"); prev_b.connect("clicked",lambda *a:self._prev())
        self._play_btn = Gtk.Button(); self._play_btn.add_css_class("play-btn")
        self._play_img = Gtk.Image.new_from_icon_name("media-playback-start-symbolic"); self._play_img.set_pixel_size(18)
        self._play_btn.set_child(self._play_img); self._play_btn.set_size_request(42,42); self._play_btn.connect("clicked",self._tog_play)
        next_b = mk("media-skip-forward-symbolic"); next_b.connect("clicked",lambda *a:self._next())
        self._rep_btn = mk("media-playlist-repeat-symbolic"); self._rep_btn.connect("clicked",self._tog_repeat)
        for w in [self._shuf_btn, prev_b, self._play_btn, next_b, self._rep_btn]: center.append(w)
        cr.append(center)

        # RIGHT
        right = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        right.set_size_request(290,-1); right.set_halign(Gtk.Align.END); right.set_valign(Gtk.Align.CENTER)
        self._mute_btn = mk("audio-volume-high-symbolic"); self._mute_btn.connect("clicked",self._tog_mute)
        right.append(self._mute_btn)
        self._vol = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL); self._vol.add_css_class("vol-bar")
        self._vol.set_size_request(90,-1); self._vol.set_range(0, 2.0); self._vol.set_value(self.cfg.get("volume", 0.8))
        self._vol.set_draw_value(False); self._vol.connect("value-changed",self._on_vol); right.append(self._vol)
        self._speed_btn = Gtk.Button(); self._speed_btn.add_css_class("speed-btn")
        self._speed_lbl_w = Gtk.Label(label=self._fmt_spd(self._speed)); self._speed_btn.set_child(self._speed_lbl_w)
        self._speed_btn.connect("clicked",self._cycle_speed); right.append(self._speed_btn)
        self._sub_btn = mk("media-view-subtitles-symbolic"); self._sub_btn.connect("clicked",self._tog_subs); right.append(self._sub_btn)
        self._aud_btn = mk("audio-x-generic-symbolic"); self._aud_btn.connect("clicked",self._cycle_audio); right.append(self._aud_btn)
        self._fs_btn = mk("view-fullscreen-symbolic"); self._fs_btn.connect("clicked",self._tog_fs); right.append(self._fs_btn)
        cr.append(right)
        bar.append(cr)
        self._pb_wrapper.append(bar)
        return self._pb_wrapper

    # =========================================================
    #   PLAYBACK BAR DRAG / RESIZE
    # =========================================================
    def _on_pb_drag_begin(self, gesture, x, y):
        self._pb_drag_start_h = self._pb_bar_height
        self._pb_handle.add_css_class("resize-handle-active")
        self._pb_size_badge.set_label(f"{int(self._pb_bar_height)}px")
        self._pb_size_badge.set_visible(True)
        if self._pb_anim_id:
            GLib.source_remove(self._pb_anim_id)
            self._pb_anim_id = None

    def _on_pb_drag_update(self, gesture, dx, dy):
        raw = self._pb_drag_start_h - dy
        clamped = max(38.0, min(320.0, raw))
        self._pb_bar_height = clamped
        h = int(clamped)
        self._pb_wrapper.set_size_request(-1, h)
        if hasattr(self, '_pb_clip'): self._pb_clip.set_size_request(-1, h)
        self._pb_size_badge.set_label(f"{int(clamped)}px")

    def _on_pb_drag_end(self, gesture, dx, dy):
        self._pb_handle.remove_css_class("resize-handle-active")
        # Snap to nearest preset — includes small sizes
        presets = [38, 52, 68, 85, 110, 140, 180, 230, 300]
        target = float(min(presets, key=lambda p: abs(p - self._pb_bar_height)))
        self.cfg.set_and_save("pb_height", int(target))
        self._pb_spring_to(target)

    def _pb_spring_to(self, target):
        """Spring-animate the playback bar to target height."""
        if self._pb_anim_id:
            GLib.source_remove(self._pb_anim_id)
            self._pb_anim_id = None
        factors = {"smooth": 0.10, "normal": 0.20, "fast": 0.45}
        factor = factors.get(self._anim_speed, 0.20)
        intervals = {"smooth": 10, "normal": 12, "fast": 8}
        interval = intervals.get(self._anim_speed, 12)

        def _set_h(h):
            self._pb_wrapper.set_size_request(-1, int(h))
            if hasattr(self, '_pb_clip'): self._pb_clip.set_size_request(-1, int(h))

        def _step():
            diff = target - self._pb_bar_height
            if abs(diff) < 0.6:
                self._pb_bar_height = target
                _set_h(target)
                self._pb_size_badge.set_visible(False)
                self._pb_anim_id = None
                return False
            self._pb_bar_height += diff * factor
            _set_h(self._pb_bar_height)
            self._pb_size_badge.set_label(f"{int(self._pb_bar_height)}px")
            return True

        self._pb_anim_id = GLib.timeout_add(interval, _step)

    # =========================================================
    #   SINK CALLBACK
    # =========================================================
    def _on_sink(self, paintable):
        if paintable:
            self._vid_pic.set_paintable(paintable)
            print("[VANTAGE] Video paintable attached to Picture widget")
        else:
            # No video sink - update placeholder with install instructions
            GLib.idle_add(self._show_no_sink_warning)

    def _show_no_sink_warning(self):
        # Replace placeholder text with install instructions
        try:
            child = self._pg_placeholder.get_first_child()
            if child:
                inner = child.get_first_child()
                if inner:
                    # Find and update the subtitle label
                    w = inner.get_first_child()
                    while w:
                        if isinstance(w, Gtk.Label) and "started" in (w.get_label() or ""):
                            w.set_label("Install GStreamer GTK4 plugin for video support:\nsudo rpm-ostree install gstreamer1-plugin-gtk4")
                            w.set_justify(Gtk.Justification.CENTER)
                            break
                        w = w.get_next_sibling()
        except: pass

    # =========================================================
    #   OPEN
    # =========================================================
    def _open_file(self, *a):
        d = Gtk.FileDialog(); d.set_title("Open Media")
        fl = Gio.ListStore.new(Gtk.FileFilter)
        flt = Gtk.FileFilter(); flt.set_name("Media Files")
        for ext in ALL_FORMATS: flt.add_pattern(f"*{ext}"); flt.add_pattern(f"*{ext.upper()}")
        fl.append(flt); d.set_filters(fl)
        d.open_multiple(self, None, self._file_done)

    def _file_done(self, dialog, result):
        try:
            files = dialog.open_multiple_finish(result)
            items = []
            for i in range(files.get_n_items()):
                gf = files.get_item(i); p = gf.get_path()
                if p and Path(p).suffix.lower() in ALL_FORMATS: items.append(MediaItem(p))
            if items: self._playlist=items; self._refresh_all(); self._play_idx(0)
        except: pass

    def _open_folder(self, *a):
        d = Gtk.FileDialog(); d.set_title("Open Folder")
        d.select_folder(self, None, self._folder_done)

    def _folder_done(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
            path = Path(folder.get_path())
            items = [MediaItem(f) for f in sorted(path.iterdir()) if f.suffix.lower() in ALL_FORMATS]
            if items: self._playlist=items; self._refresh_all(); self._play_idx(0)
        except: pass

    def open_path(self, p):
        if Path(p).suffix.lower() in ALL_FORMATS:
            self._playlist=[MediaItem(p)]; self._refresh_all(); self._play_idx(0)

    def _refresh_all(self): self._refresh_music()

    # =========================================================
    #   PLAYBACK
    # =========================================================
    def _play_idx(self, idx):
        if not self._playlist or not (0<=idx<len(self._playlist)): return
        self._pl_idx=idx; self._cur=self._playlist[idx]
        # Set _playing=True BEFORE load so async-done triggers PLAYING
        self.engine._playing = True
        self.engine.load(self._cur.path)
        if self._speed != 1.0:
            try: self.engine.set_speed(self._speed)
            except: pass
        self._update_np(); self._refresh_all()
        # Nav to right section immediately based on file extension
        if self._cur.is_video:
            self._has_video = True
            self._nav_to(self.NAV_VIDEOS)
            self._page_title.set_label("Videos")
            self._stack.set_visible_child_name("video")
        else:
            self._has_video = False
            self._nav_to(self.NAV_MUSIC)
            self._page_title.set_label("Music")
        # Re-check after stream starts in case extension was wrong
        GLib.timeout_add(1200, self._detect_video)

    def _detect_video(self):
        if not self._cur: return False
        has_v = (self.engine.n_video() > 0) or self._cur.is_video
        self._has_video = has_v
        if has_v:
            self._stack.set_visible_child_name("video")
            if self._nav != self.NAV_VIDEOS:
                self._nav_to(self.NAV_VIDEOS)
                self._page_title.set_label("Videos")
            # Show resolution
            GLib.timeout_add(400, self._show_resolution)
        return False

    def _show_resolution(self):
        try:
            pipe = self.engine._pipe
            pad = pipe.emit("get-video-pad", 0)
            if pad:
                caps = pad.get_current_caps()
                if caps:
                    s = caps.get_structure(0)
                    w = s.get_int("width")[1]
                    h = s.get_int("height")[1]
                    if w and h:
                        lbl = f"{w}×{h}"
                        if h >= 2160: lbl += " 4K"
                        elif h >= 1440: lbl += " 1440p"
                        elif h >= 1080: lbl += " 1080p"
                        elif h >= 720:  lbl += " 720p"
                        self._res_badge.set_label(lbl)
                        self._res_badge.set_visible(True)
                        GLib.timeout_add(3000, lambda: self._res_badge.set_visible(False) or False)
        except: pass
        return False

    def _update_np(self):
        if not self._cur: return
        self._np_title.set_label(self._cur.title)
        self._np_sub.set_label(self._cur.artist or Path(self._cur.path).parent.name)
        self._play_img.set_from_icon_name("media-playback-pause-symbolic")
        self._status_lbl.set_label(f"{'▶ Video' if self._cur.is_video else '♪'}  ·  {self._cur.title}")
        if hasattr(self,'_fs_title_lbl') and self._fs_win:
            self._fs_title_lbl.set_label(self._cur.title)
            self._fs_sub_lbl.set_label(self._cur.artist or "")

        # Update music page now-playing card
        if hasattr(self, '_music_np_card') and not self._cur.is_video:
            self._music_np_title.set_label(self._cur.title)
            self._music_np_artist.set_label(self._cur.artist or Path(self._cur.path).parent.name)
            self._music_np_card.set_visible(True)
            if self._cur.cover:
                try:
                    loader = GdkPixbuf.PixbufLoader(); loader.write(self._cur.cover); loader.close()
                    pb = loader.get_pixbuf().scale_simple(80, 80, GdkPixbuf.InterpType.BILINEAR)
                    self._music_np_art_img.set_from_pixbuf(pb)
                    self._music_np_art_img.set_visible(True)
                    self._music_np_art_ico.set_visible(False)
                except:
                    self._music_np_art_ico.set_visible(True); self._music_np_art_img.set_visible(False)
            else:
                self._music_np_art_ico.set_visible(True); self._music_np_art_img.set_visible(False)
        elif hasattr(self, '_music_np_card'):
            self._music_np_card.set_visible(False)

        if not self._cur.is_video and self._cur.cover:
            try:
                loader = GdkPixbuf.PixbufLoader(); loader.write(self._cur.cover); loader.close()
                pb = loader.get_pixbuf().scale_simple(42, 42, GdkPixbuf.InterpType.BILINEAR)
                self._art_img.set_from_pixbuf(pb); self._art_img.set_visible(True); self._art_ico.set_visible(False); return
            except: pass
        self._art_ico.set_from_icon_name("video-x-generic-symbolic" if self._cur.is_video else "audio-x-generic-symbolic")
        self._art_ico.set_visible(True); self._art_img.set_visible(False)

    def _tog_play(self, *a):
        if not self._cur:
            if self._playlist: self._play_idx(0)
            return
        if self.engine.is_playing(): self.engine.pause()
        else: self.engine.play()

    def _next(self):
        if not self._playlist: return
        if self._shuffle:
            self._play_idx(random.randint(0, len(self._playlist)-1))
        elif self._pl_idx < len(self._playlist) - 1:
            self._play_idx(self._pl_idx + 1)
        elif self._repeat == "all":
            self._play_idx(0)
        # else: at end, do nothing — stop

    def _prev(self):
        if not self._playlist: return
        if self.engine.get_position()>3: self.engine.seek(0); return
        self._play_idx((self._pl_idx-1)%len(self._playlist))

    def _on_end(self):
        if self._repeat == "one":
            self.engine.seek(0); self.engine.play()
        else:
            self._next()

    def _on_pos(self, pos, dur):
        if self._seeking: return
        if dur>0: self._seek.set_value((pos/dur)*100)
        t=self._fmt_time(pos); d=self._fmt_time(dur)
        self._time_cur.set_label(t); self._time_tot.set_label(d)
        if hasattr(self,'_fs_seek') and self._fs_win:
            if dur>0: self._fs_seek.set_value((pos/dur)*100)
            self._fs_cur.set_label(t); self._fs_tot.set_label(d)

    def _on_state(self, playing):
        icon = "media-playback-pause-symbolic" if playing else "media-playback-start-symbolic"
        self._play_img.set_from_icon_name(icon)
        if hasattr(self,'_fs_play_img') and self._fs_win:
            self._fs_play_img.set_from_icon_name(icon)

    def _on_seek_change(self, scale, scroll_type, value):
        dur = self.engine.get_duration()
        if dur > 0:
            self._seeking = True
            self.engine.seek((value / 100.0) * dur)
            GLib.timeout_add(100, lambda: setattr(self, '_seeking', False) or False)
        return False  # allow scale to update visually

    def _on_vol(self, scale):
        v = scale.get_value()
        self.engine.set_volume(min(v, 1.0))   # GStreamer caps at 1.0 — use volume above that via pipeline
        # For >1.0 we amplify via playbin volume property which accepts >1.0 on some builds
        try: self.engine._pipe.set_property("volume", v)
        except: pass
        self.cfg.set_and_save("volume", v)
        pct = int(v * 100)
        self._vol.set_tooltip_text(f"{pct}%")
        if self._muted: return
        if v == 0:   ico = "audio-volume-muted-symbolic"
        elif v < 0.4: ico = "audio-volume-low-symbolic"
        elif v < 1.0: ico = "audio-volume-medium-symbolic"
        else:         ico = "audio-volume-high-symbolic"
        self._mute_btn.get_child().set_from_icon_name(ico)

    def _tog_mute(self, *a):
        self._muted = not self._muted; self.engine.set_mute(self._muted); self.cfg.set_and_save("muted",self._muted)
        if self._muted:
            self._mute_btn.get_child().set_from_icon_name("audio-volume-muted-symbolic"); self._mute_btn.add_css_class("active")
            if hasattr(self,'_fs_mute') and self._fs_win:
                self._fs_mute.get_child().set_from_icon_name("audio-volume-muted-symbolic"); self._fs_mute.add_css_class("active")
        else:
            self._mute_btn.remove_css_class("active"); self._on_vol(self._vol)
            if hasattr(self,'_fs_mute') and self._fs_win:
                self._fs_mute.remove_css_class("active"); self._fs_mute.get_child().set_from_icon_name("audio-volume-high-symbolic")

    def _cycle_speed(self, *a):
        speeds=[0.5,0.75,1.0,1.25,1.5,2.0]
        cur = speeds.index(self._speed) if self._speed in speeds else 2
        self._speed = speeds[(cur+1)%len(speeds)]; self.cfg.set_and_save("speed",self._speed)
        self._speed_lbl_w.set_label(self._fmt_spd(self._speed))
        if hasattr(self,'_fs_spd_lbl') and self._fs_win: self._fs_spd_lbl.set_label(self._fmt_spd(self._speed))
        if self._speed!=1.0: self._speed_btn.add_css_class("active")
        else: self._speed_btn.remove_css_class("active")
        try: self.engine.set_speed(self._speed)
        except: pass

    def _tog_subs(self, *a):
        if self._subs_on: self.engine.disable_subs(); self._sub_btn.remove_css_class("active"); self._subs_on=False
        elif self.engine.n_text()>0: self.engine.set_sub_track(0); self._sub_btn.add_css_class("active"); self._subs_on=True

    def _cycle_audio(self, *a):
        n=self.engine.n_audio()
        if n<=1: return
        try:
            cur=self.engine._pipe.get_property("current-audio"); self.engine.set_audio_track((cur+1)%n)
            self._status_lbl.set_label(f"Audio track: {(cur+1)%n+1}/{n}")
        except: pass

    def _tog_shuffle(self, *a):
        self._shuffle = not self._shuffle
        if self._shuffle:
            self._shuf_btn.add_css_class("active")
            if hasattr(self,'_fs_shuf') and self._fs_win: self._fs_shuf.add_css_class("active")
        else:
            self._shuf_btn.remove_css_class("active")
            if hasattr(self,'_fs_shuf') and self._fs_win: self._fs_shuf.remove_css_class("active")

    def _tog_repeat(self, *a):
        modes=["off","all","one"]; self._repeat=modes[(modes.index(self._repeat)+1)%3]
        icons={"off":"media-playlist-repeat-symbolic","all":"media-playlist-repeat-symbolic","one":"media-playlist-repeat-song-symbolic"}
        self._rep_btn.get_child().set_from_icon_name(icons[self._repeat])
        if self._repeat!="off": self._rep_btn.add_css_class("active")
        else: self._rep_btn.remove_css_class("active")

    # =========================================================
    #   FULLSCREEN (video only, separate window)
    # =========================================================
    def _tog_fs(self, *a):
        if self._fs_win: self._close_fs()
        else: self._open_fs()

    def _open_fs(self):
        if not self._has_video: return
        self._fs_win = Gtk.Window(application=self.get_application())
        self._fs_win.set_decorated(False); self._fs_win.fullscreen()

        css2 = Gtk.CssProvider()
        css2.load_from_string(DARK_CSS if self._dark else LIGHT_CSS)
        Gtk.StyleContext.add_provider_for_display(
            self._fs_win.get_display(), css2, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        ov = Gtk.Overlay(); ov.set_hexpand(True); ov.set_vexpand(True)

        # Video picture
        fs_pic = Gtk.Picture(); fs_pic.set_hexpand(True); fs_pic.set_vexpand(True)
        fs_pic.add_css_class("video-area"); fs_pic.set_content_fit(Gtk.ContentFit.CONTAIN)
        if self._vid_pic.get_paintable(): fs_pic.set_paintable(self._vid_pic.get_paintable())
        ov.set_child(fs_pic)

        # TOP bar: title
        self._fs_top = self._mk_fs_top()
        self._fs_top.set_valign(Gtk.Align.START)
        self._fs_top.set_hexpand(True)
        ov.add_overlay(self._fs_top)

        # BOTTOM bar: all controls
        self._fs_ctrl = self._mk_fs_ctrl()
        self._fs_ctrl.set_valign(Gtk.Align.END)
        self._fs_ctrl.set_hexpand(True)
        ov.add_overlay(self._fs_ctrl)

        mo = Gtk.EventControllerMotion(); mo.connect("motion", self._on_fs_motion); ov.add_controller(mo)
        # Single click = play/pause, double click = exit fs
        gc = Gtk.GestureClick(); gc.connect("released", self._on_fs_click); ov.add_controller(gc)
        k = Gtk.EventControllerKey(); k.connect("key-pressed", self._on_key); self._fs_win.add_controller(k)

        self._fs_win.set_child(ov)
        self._fs_win.connect("close-request", lambda *a: self._close_fs() or False)
        self._fs_win.present()
        self._fs_btn.get_child().set_from_icon_name("view-restore-symbolic")
        # Show controls briefly then hide
        self._show_fs_ui(True)
        GLib.timeout_add(2500, lambda: self._show_fs_ui(False) or False)

    def _mk_fs_top(self):
        top = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        top.add_css_class("fs-top-bar")

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        info.set_hexpand(True)
        self._fs_title_lbl = Gtk.Label(label=self._cur.title if self._cur else "")
        self._fs_title_lbl.add_css_class("fs-title")
        self._fs_title_lbl.set_halign(Gtk.Align.START)
        self._fs_title_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        self._fs_sub_lbl = Gtk.Label(label=self._cur.artist if (self._cur and self._cur.artist) else "")
        self._fs_sub_lbl.add_css_class("fs-sub"); self._fs_sub_lbl.set_halign(Gtk.Align.START)
        info.append(self._fs_title_lbl); info.append(self._fs_sub_lbl)
        row.append(info)
        top.append(row)
        return top

    def _close_fs(self):
        if self._fs_win: self._fs_win.destroy(); self._fs_win=None
        if self._fs_tmr: GLib.source_remove(self._fs_tmr); self._fs_tmr=None
        self._fs_btn.get_child().set_from_icon_name("view-fullscreen-symbolic")

    def _mk_fs_ctrl(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.add_css_class("fs-bottom-bar")

        # Seek row
        sr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        sr.set_margin_bottom(10)
        self._fs_cur = Gtk.Label(label="0:00"); self._fs_cur.add_css_class("fs-time")
        self._fs_seek = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
        self._fs_seek.add_css_class("fs-seek"); self._fs_seek.set_hexpand(True)
        self._fs_seek.set_range(0, 100); self._fs_seek.set_draw_value(False)
        self._fs_seek.connect("change-value", self._on_fs_seek_change)
        self._fs_tot = Gtk.Label(label="0:00"); self._fs_tot.add_css_class("fs-time")
        sr.append(self._fs_cur); sr.append(self._fs_seek); sr.append(self._fs_tot)
        box.append(sr)

        # Controls row
        cr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        cr.set_valign(Gtk.Align.CENTER)

        def mk(ico, sz=38):
            b = Gtk.Button(); b.add_css_class("fs-ctrl-btn")
            img = Gtk.Image.new_from_icon_name(ico); img.set_pixel_size(16)
            b.set_child(img); b.set_size_request(sz, sz); return b

        # LEFT: shuffle, prev, play, next, repeat
        left = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self._fs_shuf = mk("media-playlist-shuffle-symbolic")
        self._fs_shuf.connect("clicked", self._tog_shuffle)
        if self._shuffle: self._fs_shuf.add_css_class("active")

        fp = mk("media-skip-backward-symbolic"); fp.connect("clicked", lambda *a: self._prev())

        self._fs_play_btn = Gtk.Button(); self._fs_play_btn.add_css_class("fs-play-btn")
        self._fs_play_img = Gtk.Image.new_from_icon_name(
            "media-playback-pause-symbolic" if self.engine.is_playing() else "media-playback-start-symbolic")
        self._fs_play_img.set_pixel_size(20)
        self._fs_play_btn.set_child(self._fs_play_img); self._fs_play_btn.set_size_request(46, 46)
        self._fs_play_btn.connect("clicked", self._tog_play)

        fn = mk("media-skip-forward-symbolic"); fn.connect("clicked", lambda *a: self._next())

        self._fs_rep = mk("media-playlist-repeat-symbolic")
        self._fs_rep.connect("clicked", self._tog_repeat)
        if self._repeat != "off": self._fs_rep.add_css_class("active")

        for w in [self._fs_shuf, fp, self._fs_play_btn, fn, self._fs_rep]: left.append(w)
        cr.append(left)

        sp = Gtk.Box(); sp.set_hexpand(True); cr.append(sp)

        # RIGHT: mute, volume slider, speed, subs, audio track, exit
        right = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        right.set_valign(Gtk.Align.CENTER)

        self._fs_mute = mk("audio-volume-muted-symbolic" if self._muted else "audio-volume-high-symbolic")
        self._fs_mute.connect("clicked", self._tog_mute)
        if self._muted: self._fs_mute.add_css_class("active")
        right.append(self._fs_mute)

        self._fs_vol = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
        self._fs_vol.add_css_class("fs-vol"); self._fs_vol.set_size_request(100, -1)
        self._fs_vol.set_range(0, 2.0); self._fs_vol.set_value(self.cfg.get("volume", 0.8))
        self._fs_vol.set_draw_value(False)
        self._fs_vol.connect("value-changed", self._on_fs_vol)
        right.append(self._fs_vol)

        self._fs_spd_btn = Gtk.Button(); self._fs_spd_btn.add_css_class("fs-ctrl-btn")
        self._fs_spd_lbl = Gtk.Label(label=self._fmt_spd(self._speed)); self._fs_spd_lbl.add_css_class("fs-speed")
        self._fs_spd_btn.set_child(self._fs_spd_lbl); self._fs_spd_btn.set_size_request(46, 34)
        self._fs_spd_btn.connect("clicked", self._cycle_speed)
        right.append(self._fs_spd_btn)

        self._fs_sub_btn = mk("media-view-subtitles-symbolic")
        self._fs_sub_btn.connect("clicked", self._tog_subs)
        if self._subs_on: self._fs_sub_btn.add_css_class("active")
        right.append(self._fs_sub_btn)

        self._fs_aud_btn = mk("audio-x-generic-symbolic")
        self._fs_aud_btn.connect("clicked", self._cycle_audio)
        right.append(self._fs_aud_btn)

        fs_exit = mk("view-restore-symbolic"); fs_exit.connect("clicked", self._tog_fs)
        right.append(fs_exit)

        cr.append(right)
        box.append(cr)
        return box

    def _on_fs_vol(self, scale):
        v = scale.get_value()
        self._vol.set_value(v)  # sync main vol slider → triggers _on_vol

    def _show_fs_ui(self, visible):
        if hasattr(self, '_fs_top'):  self._fs_top.set_visible(visible)
        if hasattr(self, '_fs_ctrl'): self._fs_ctrl.set_visible(visible)

    def _on_fs_click(self, gesture, n, x, y):
        if n == 2:
            self._tog_fs()
        else:
            # Single click: if UI visible, hide it; else show it and toggle play
            ui_visible = hasattr(self,'_fs_ctrl') and self._fs_ctrl.get_visible()
            if ui_visible:
                self._tog_play()
            else:
                self._show_fs_ui(True)
                if self._fs_tmr: GLib.source_remove(self._fs_tmr)
                self._fs_tmr = GLib.timeout_add(3000, lambda: self._show_fs_ui(False) or False)

    def _on_fs_seek_change(self, scale, scroll_type, value):
        dur = self.engine.get_duration()
        if dur > 0:
            self._seeking = True
            self.engine.seek((value / 100.0) * dur)
            GLib.timeout_add(100, lambda: setattr(self, '_seeking', False) or False)
        return False

    def _on_fs_motion(self, *a):
        self._show_fs_ui(True)
        if self._fs_tmr: GLib.source_remove(self._fs_tmr)
        self._fs_tmr = GLib.timeout_add(3000, lambda: self._show_fs_ui(False) or False)

    def _on_video_click(self, gesture, n, x, y):
        if n==2: self._tog_fs()
        else:    self._tog_play()

    # =========================================================
    #   KEYBOARD
    # =========================================================
    def _on_key(self, ctrl, kv, kc, state):
        if kv == Gdk.KEY_space:
            self._tog_play(); return True
        elif kv == Gdk.KEY_Right:
            self.engine.seek(self.engine.get_position() + 5); return True
        elif kv == Gdk.KEY_Left:
            self.engine.seek(max(0, self.engine.get_position() - 5)); return True
        elif kv == Gdk.KEY_Up:
            self._vol.set_value(min(2.0, self._vol.get_value() + 0.05)); return True
        elif kv == Gdk.KEY_Down:
            self._vol.set_value(max(0.0, self._vol.get_value() - 0.05)); return True
        elif kv in (Gdk.KEY_F11, Gdk.KEY_f, Gdk.KEY_F):
            self._tog_fs(); return True
        elif kv in (Gdk.KEY_m, Gdk.KEY_M):
            self._tog_mute(); return True
        elif kv in (Gdk.KEY_n, Gdk.KEY_N):
            self._next(); return True
        elif kv in (Gdk.KEY_p, Gdk.KEY_P):
            self._prev(); return True
        elif kv == Gdk.KEY_bracketright:   # ] = speed up
            self._cycle_speed(); return True
        elif kv == Gdk.KEY_bracketleft:    # [ = speed down
            speeds = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]
            try: i = speeds.index(self._speed)
            except ValueError: i = speeds.index(min(speeds, key=lambda x: abs(x-self._speed)))
            if i > 0:
                self._speed = speeds[i-1]
                self.engine.set_speed(self._speed)
                self.cfg.set("speed", self._speed)
                self._speed_lbl_w.set_label(self._fmt_spd(self._speed))
                if hasattr(self,'_fs_spd_lbl') and self._fs_win: self._fs_spd_lbl.set_label(self._fmt_spd(self._speed))
            return True
        elif kv == Gdk.KEY_Escape:
            self._close_fs(); return True
        return False

    # =========================================================
    #   HELPERS
    # =========================================================
    def _fmt_time(self, s):
        s=int(s); m,s=divmod(s,60); h,m=divmod(m,60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

    def _fmt_spd(self, spd):
        if spd==int(spd): return f"{int(spd)}x"
        return f"{spd:.2f}".rstrip('0')+'x'

# =========================================================
#   APP
# =========================================================
class VantageApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.HANDLES_OPEN)
        self.connect("activate", self._activate)
        self.connect("open",     self._open)
        self._win = None

    def _activate(self, app):
        if not self._win: self._win = VantageWindow(app)
        self._win.present()

    def _open(self, app, files, hint):
        self._activate(app)
        for f in files:
            p = f.get_path()
            if p: self._win.open_path(p); break

if __name__ == "__main__":
    import sys
    VantageApp().run(sys.argv)
