import logging
import random
import time
import os
import sys
import socket
import json
import threading
import math
import faulthandler
import signal
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Enable faulthandler to debug hangs/deadlocks
faulthandler.enable()
if hasattr(signal, 'SIGUSR1'):
    faulthandler.register(signal.SIGUSR1)

# Global configurations
HOSTNAME = socket.gethostname()
PORT = int(os.getenv('PORT', os.getenv('HTTP_PORT', '8080')))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')

# Messages dictionary
MESSAGES = [
    "Processing user request",
    "Database connection established",
    "Cache hit for key",
    "API response received",
    "Configuration loaded",
    "Health check passed",
    "Memory usage normal",
    "Task completed successfully",
    "Retrying failed operation",
    "Connection timeout occurred",
    "Invalid input detected",
    "Service unavailable",
    "Authentication successful",
    "Rate limit approaching",
    "Backup completed"
]

class LogConfig:
    def __init__(self):
        self.format_type = os.getenv('LOG_FORMAT', 'JSON').upper()
        self.pattern = os.getenv('LOG_PATTERN', 'random').lower()
        self.interval_min = float(os.getenv('LOG_INTERVAL_MIN', '10.0'))
        self.interval_max = float(os.getenv('LOG_INTERVAL_MAX', '15.0'))
        self.burst_count = 0
        
        # Parse custom log fields
        self.extra_fields = {}
        fields_env = os.getenv('LOG_FIELDS', '')
        if fields_env:
            for item in fields_env.split(','):
                if '=' in item:
                    k, v = item.split('=', 1)
                    self.extra_fields[k.strip()] = v.strip()

log_config = LogConfig()
log_config_lock = threading.Lock()
burst_triggered_count = 0
start_time = time.time()

class DynamicFormatter(logging.Formatter):
    def format(self, record):
        try:
            with log_config_lock:
                fmt = log_config.format_type
                extra = dict(log_config.extra_fields)
            
            # Generate ISO 8601 UTC timestamp
            timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            
            if fmt == "JSON":
                log_entry = {
                    "timestamp": timestamp,
                    "level": record.levelname,
                    "message": record.getMessage(),
                    "logger": record.name,
                    "hostname": HOSTNAME,
                    "app": "log-generator"
                }
                if extra:
                    log_entry.update(extra)
                return json.dumps(log_entry)
            else:
                return f"{timestamp} - {record.levelname} - {record.getMessage()}"
        except Exception as e:
            return f"Formatter Error: {e} | Original: {record.getMessage()}"

class CounterHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.stats = {
            "DEBUG": 0,
            "INFO": 0,
            "WARNING": 0,
            "ERROR": 0,
            "CRITICAL": 0,
            "total": 0
        }
        self.latest_logs = []

    def emit(self, record):
        try:
            levelname = record.levelname
            log_str = self.formatter.format(record) if self.formatter else record.getMessage()
            
            with self.lock:
                if levelname in self.stats:
                    self.stats[levelname] += 1
                self.stats["total"] += 1
                
                self.latest_logs.append({
                    "line": log_str,
                    "level": levelname
                })
                if len(self.latest_logs) > 30:
                    self.latest_logs.pop(0)
        except Exception:
            pass

counter_handler = CounterHandler()
counter_handler.setFormatter(DynamicFormatter())

# Stunning inline CSS/HTML dashboard
DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Log Engine Control Center</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #080c14;
            --card-bg: rgba(15, 23, 42, 0.65);
            --card-border: rgba(255, 255, 255, 0.08);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --primary: #c084fc;
            --primary-hover: #a855f7;
            
            --color-debug: #94a3b8;
            --color-info: #34d399;
            --color-warning: #fbbf24;
            --color-error: #f87171;
            --color-critical: #f472b6;
            
            --glow-debug: rgba(148, 163, 184, 0.15);
            --glow-info: rgba(52, 211, 153, 0.2);
            --glow-warning: rgba(251, 191, 36, 0.2);
            --glow-error: rgba(248, 113, 113, 0.2);
            --glow-critical: rgba(244, 114, 182, 0.25);
        }
        
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            background-image: 
                radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.15) 0, transparent 50%),
                radial-gradient(at 100% 0%, rgba(168, 85, 247, 0.15) 0, transparent 50%),
                radial-gradient(at 50% 100%, rgba(20, 184, 166, 0.1) 0, transparent 50%);
            background-attachment: fixed;
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            line-height: 1.5;
        }
        
        header {
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            background: rgba(8, 12, 20, 0.7);
            border-bottom: 1px solid var(--card-border);
            padding: 1.25rem 2rem;
            position: sticky;
            top: 0;
            z-index: 100;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo-container {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        
        .logo-icon {
            width: 2.25rem;
            height: 2.25rem;
            background: linear-gradient(135deg, #a855f7, #06b6d4);
            border-radius: 0.75rem;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            color: #fff;
            box-shadow: 0 0 20px rgba(168, 85, 247, 0.4);
            font-size: 1.1rem;
        }
        
        h1 {
            font-size: 1.35rem;
            font-weight: 700;
            letter-spacing: -0.025em;
            background: linear-gradient(to right, #fff, #94a3b8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .status-badge {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(52, 211, 153, 0.08);
            border: 1px solid rgba(52, 211, 153, 0.2);
            color: var(--color-info);
            padding: 0.4rem 0.85rem;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 600;
            letter-spacing: 0.025em;
        }
        
        .status-pulse {
            width: 0.5rem;
            height: 0.5rem;
            background-color: var(--color-info);
            border-radius: 50%;
            animation: pulse 1.8s infinite;
        }
        
        @keyframes pulse {
            0% { transform: scale(0.95); opacity: 1; box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.5); }
            70% { transform: scale(1.1); opacity: 0.3; box-shadow: 0 0 0 6px rgba(52, 211, 153, 0); }
            100% { transform: scale(0.95); opacity: 1; box-shadow: 0 0 0 0 rgba(52, 211, 153, 0); }
        }
        
        main {
            max-width: 1440px;
            margin: 0 auto;
            padding: 2rem;
            width: 100%;
            display: grid;
            grid-template-columns: 1fr;
            gap: 2rem;
            flex-grow: 1;
        }
        
        @media (min-width: 1024px) {
            main {
                grid-template-columns: 340px 1fr;
            }
        }
        
        .sidebar {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }
        
        .dashboard-content {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }
        
        .glass-card {
            background: var(--card-bg);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid var(--card-border);
            border-radius: 1.25rem;
            padding: 1.75rem;
            box-shadow: 0 10px 40px -10px rgba(0, 0, 0, 0.5);
            transition: border-color 0.3s ease, box-shadow 0.3s ease;
        }
        
        .glass-card:hover {
            border-color: rgba(255, 255, 255, 0.12);
            box-shadow: 0 15px 45px -8px rgba(0, 0, 0, 0.6);
        }
        
        .card-title {
            font-size: 1.05rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            color: #fff;
            display: flex;
            align-items: center;
            gap: 0.6rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            padding-bottom: 0.85rem;
        }
        
        .card-title svg {
            width: 1.2rem;
            height: 1.2rem;
            color: var(--primary);
        }
        
        .form-group {
            margin-bottom: 1.35rem;
        }
        
        .form-group:last-child {
            margin-bottom: 0;
        }
        
        label {
            display: block;
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--text-muted);
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        select, input[type="text"], input[type="number"] {
            width: 100%;
            background: rgba(8, 12, 20, 0.7);
            border: 1px solid var(--card-border);
            border-radius: 0.6rem;
            padding: 0.75rem 0.85rem;
            color: #fff;
            font-family: inherit;
            font-size: 0.9rem;
            outline: none;
            transition: border-color 0.2s, box-shadow 0.2s;
        }
        
        select:focus, input[type="text"]:focus, input[type="number"]:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 2px rgba(168, 85, 247, 0.25);
        }
        
        .range-container {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }
        
        .range-inputs {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.25rem;
        }
        
        .range-inputs span {
            font-size: 0.85rem;
            color: var(--text-muted);
            font-weight: 500;
        }
        
        .range-slider {
            width: 100%;
            accent-color: var(--primary);
            margin: 0.5rem 0;
        }
        
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            padding: 0.75rem 1.25rem;
            font-weight: 600;
            font-size: 0.9rem;
            border-radius: 0.6rem;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            gap: 0.5rem;
            border: none;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, var(--primary), #8b5cf6);
            color: #fff;
            box-shadow: 0 4px 15px rgba(168, 85, 247, 0.25);
        }
        
        .btn-primary:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(168, 85, 247, 0.35);
        }
        
        .btn-secondary {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--card-border);
            color: #fff;
        }
        
        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.08);
            border-color: rgba(255, 255, 255, 0.15);
        }
        
        .btn-danger {
            background: linear-gradient(135deg, #ef4444, #dc2626);
            color: #fff;
            box-shadow: 0 4px 15px rgba(239, 68, 68, 0.25);
        }
        
        .btn-danger:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(239, 68, 68, 0.35);
        }
        
        .btn-warning {
            background: linear-gradient(135deg, #f59e0b, #d97706);
            color: #fff;
            box-shadow: 0 4px 15px rgba(245, 158, 11, 0.25);
        }
        
        .btn-warning:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(245, 158, 11, 0.35);
        }
        
        .action-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.75rem;
        }
        
        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
        }
        
        @media (min-width: 640px) {
            .stats-grid {
                grid-template-columns: repeat(3, 1fr);
            }
        }
        
        @media (min-width: 1200px) {
            .stats-grid {
                grid-template-columns: repeat(6, 1fr);
            }
        }
        
        .stat-card {
            padding: 1.35rem 1rem;
            text-align: center;
            border-radius: 1rem;
            border: 1px solid var(--card-border);
            background: rgba(15, 23, 42, 0.4);
            display: flex;
            flex-direction: column;
            gap: 0.35rem;
            position: relative;
            overflow: hidden;
            backdrop-filter: blur(8px);
            transition: transform 0.2s, border-color 0.2s;
        }
        
        .stat-card:hover {
            transform: translateY(-2px);
            border-color: rgba(255, 255, 255, 0.12);
        }
        
        .stat-card::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: var(--card-accent, var(--color-debug));
        }
        
        .stat-label {
            font-size: 0.7rem;
            font-weight: 700;
            color: var(--text-muted);
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        
        .stat-value {
            font-size: 1.75rem;
            font-weight: 700;
            color: #fff;
            font-family: 'Fira Code', monospace;
        }
        
        /* Terminal Console */
        .terminal-container {
            display: flex;
            flex-direction: column;
            height: 480px;
        }
        
        .terminal-header {
            background: #090d16;
            border-top-left-radius: 1rem;
            border-top-right-radius: 1rem;
            padding: 0.65rem 1.25rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--card-border);
        }
        
        .terminal-dots {
            display: flex;
            gap: 0.45rem;
        }
        
        .dot {
            width: 0.75rem;
            height: 0.75rem;
            border-radius: 50%;
        }
        
        .dot-red { background-color: #ef4444; }
        .dot-yellow { background-color: #f59e0b; }
        .dot-green { background-color: #10b981; }
        
        .terminal-title {
            font-family: 'Fira Code', monospace;
            font-size: 0.75rem;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .terminal-body {
            background: #02040a;
            flex-grow: 1;
            border-bottom-left-radius: 1rem;
            border-bottom-right-radius: 1rem;
            padding: 1.25rem;
            font-family: 'Fira Code', monospace;
            font-size: 0.8rem;
            overflow-y: auto;
            white-space: pre-wrap;
            color: #e2e8f0;
            scroll-behavior: smooth;
        }
        
        .log-line {
            margin-bottom: 0.45rem;
            line-height: 1.5;
            border-left: 2.5px solid transparent;
            padding-left: 0.5rem;
        }
        
        .log-DEBUG { border-left-color: var(--color-debug); color: var(--color-debug); }
        .log-INFO { border-left-color: var(--color-info); color: var(--color-info); }
        .log-WARNING { border-left-color: var(--color-warning); color: var(--color-warning); }
        .log-ERROR { border-left-color: var(--color-error); color: var(--color-error); }
        .log-CRITICAL { 
            border-left-color: var(--color-critical); 
            color: var(--color-critical); 
            font-weight: 600;
            background: rgba(244, 114, 182, 0.05);
            padding-top: 0.1rem;
            padding-bottom: 0.1rem;
        }
        
        .grid-2col {
            display: grid;
            grid-template-columns: 1fr;
            gap: 1.5rem;
        }
        
        @media (min-width: 768px) {
            .grid-2col {
                grid-template-columns: 3fr 2fr;
            }
        }
        
        /* Distribution bars */
        .dist-container {
            display: flex;
            flex-direction: column;
            gap: 0.85rem;
        }
        
        .dist-row {
            display: flex;
            align-items: center;
            gap: 1.25rem;
        }
        
        .dist-label {
            width: 90px;
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--text-muted);
        }
        
        .dist-bar-bg {
            flex-grow: 1;
            height: 10px;
            background: rgba(255, 255, 255, 0.04);
            border-radius: 9999px;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.02);
        }
        
        .dist-bar-fill {
            height: 100%;
            border-radius: 9999px;
            transition: width 0.6s cubic-bezier(0.16, 1, 0.3, 1);
            background-color: var(--bar-color, var(--color-debug));
            box-shadow: 0 0 10px var(--bar-glow, var(--glow-debug));
        }
        
        .dist-val {
            width: 45px;
            text-align: right;
            font-size: 0.85rem;
            font-weight: 700;
            font-family: 'Fira Code', monospace;
        }
        
        /* Toasts */
        .toast-container {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
            z-index: 1000;
        }
        
        .toast {
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid var(--card-border);
            padding: 0.85rem 1.35rem;
            border-radius: 0.75rem;
            color: #fff;
            font-size: 0.85rem;
            font-weight: 500;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.6);
            transform: translateY(100px);
            opacity: 0;
            transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .toast.show {
            transform: translateY(0);
            opacity: 1;
        }
        
        footer {
            margin-top: auto;
            text-align: center;
            padding: 2rem;
            color: var(--text-muted);
            font-size: 0.8rem;
            border-top: 1px solid var(--card-border);
            background: rgba(8, 12, 20, 0.4);
        }
        
        footer a {
            color: var(--primary);
            text-decoration: none;
            font-weight: 500;
        }
        
        footer a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <header>
        <div class="logo-container">
            <div class="logo-icon">L</div>
            <h1>Log Testing Console</h1>
        </div>
        <div class="status-badge">
            <span class="status-pulse"></span>
            ACTIVE GENERATOR
        </div>
    </header>
    
    <main>
        <div class="sidebar">
            <!-- Configuration Card -->
            <div class="glass-card">
                <div class="card-title">
                    <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.43l-1.003.828c-.293.241-.438.613-.43.992a7.723 7.723 0 010 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.43l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 010-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.281z"></path>
                        <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                    </svg>
                    Simulation Settings
                </div>
                
                <div class="form-group">
                    <label for="log-format">Log Format</label>
                    <select id="log-format" onchange="updateConfig()">
                        <option value="JSON">Structured JSON</option>
                        <option value="TEXT">Standard Text</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="log-pattern">Emission Pattern</label>
                    <select id="log-pattern" onchange="updateConfig()">
                        <option value="random">Random Spacing</option>
                        <option value="constant">Constant Interval</option>
                        <option value="sinewave">Sine Wave Traffic</option>
                        <option value="burst">Periodic Burst Spikes</option>
                    </select>
                </div>
                
                <div class="form-group range-container">
                    <label>Interval Bounds (sec)</label>
                    <div class="range-inputs">
                        <label style="font-size: 0.75rem; margin: 0;">Min:</label>
                        <span id="min-val-display">10.0s</span>
                    </div>
                    <input type="range" id="interval-min" class="range-slider" min="0.1" max="60" step="0.1" value="10.0" oninput="onSliderChange()" onchange="updateConfig()">
                    
                    <div class="range-inputs">
                        <label style="font-size: 0.75rem; margin: 0;">Max:</label>
                        <span id="max-val-display">15.0s</span>
                    </div>
                    <input type="range" id="interval-max" class="range-slider" min="0.2" max="60" step="0.1" value="15.0" oninput="onSliderChange()" onchange="updateConfig()">
                </div>
            </div>
            
            <!-- Quick Actions -->
            <div class="glass-card">
                <div class="card-title">
                    <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z"></path>
                    </svg>
                    Test Injections
                </div>
                <div class="action-grid">
                    <button class="btn btn-warning" onclick="triggerBurst(25)">
                        Error Spike
                    </button>
                    <button class="btn btn-danger" onclick="triggerBurst(50)">
                        System Panic
                    </button>
                </div>
            </div>
        </div>
        
        <div class="dashboard-content">
            <!-- Stats -->
            <div class="stats-grid">
                <div class="stat-card" style="--card-accent: #a855f7;">
                    <div class="stat-label">Total Emitted</div>
                    <div class="stat-value" id="stat-total">0</div>
                </div>
                <div class="stat-card" style="--card-accent: var(--color-debug);">
                    <div class="stat-label">Debug</div>
                    <div class="stat-value" id="stat-debug">0</div>
                </div>
                <div class="stat-card" style="--card-accent: var(--color-info);">
                    <div class="stat-label">Info</div>
                    <div class="stat-value" id="stat-info">0</div>
                </div>
                <div class="stat-card" style="--card-accent: var(--color-warning);">
                    <div class="stat-label">Warning</div>
                    <div class="stat-value" id="stat-warning">0</div>
                </div>
                <div class="stat-card" style="--card-accent: var(--color-error);">
                    <div class="stat-label">Error</div>
                    <div class="stat-value" id="stat-error">0</div>
                </div>
                <div class="stat-card" style="--card-accent: var(--color-critical);">
                    <div class="stat-label">Critical</div>
                    <div class="stat-value" id="stat-critical">0</div>
                </div>
            </div>
            
            <!-- Terminal console -->
            <div class="glass-card terminal-container">
                <div class="terminal-header">
                    <div class="terminal-dots">
                        <div class="dot dot-red"></div>
                        <div class="dot dot-yellow"></div>
                        <div class="dot dot-green"></div>
                    </div>
                    <div class="terminal-title">
                        <span>LIVE TERMINAL FEED (STDOUT)</span>
                    </div>
                    <div style="width: 50px;"></div>
                </div>
                <div class="terminal-body" id="terminal-body">
                    <div class="log-line log-INFO">Initializing Log Testing Dashboard...</div>
                </div>
            </div>
            
            <div class="grid-2col">
                <!-- Manual Log Trigger -->
                <div class="glass-card">
                    <div class="card-title">
                        <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v6m3-3H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                        Emit Custom Log Message
                    </div>
                    <form onsubmit="sendManualLog(event)" style="display: flex; flex-direction: column; gap: 1rem;">
                        <div style="display: grid; grid-template-columns: 1fr; gap: 1rem;">
                            <div>
                                <label for="manual-msg">Message</label>
                                <input type="text" id="manual-msg" placeholder="e.g. Out of memory check on service auth" required>
                            </div>
                            <div>
                                <label for="manual-level">Level</label>
                                <select id="manual-level">
                                    <option value="DEBUG">DEBUG</option>
                                    <option value="INFO" selected>INFO</option>
                                    <option value="WARNING">WARNING</option>
                                    <option value="ERROR">ERROR</option>
                                    <option value="CRITICAL">CRITICAL</option>
                                </select>
                            </div>
                        </div>
                        <button type="submit" class="btn btn-primary" style="margin-top: 0.5rem;">
                            Inject Custom Log
                        </button>
                    </form>
                </div>
                
                <!-- Log Level Ratio -->
                <div class="glass-card">
                    <div class="card-title">
                        <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 6a7.5 7.5 0 107.5 7.5h-7.5V6z"></path>
                            <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 10.5H21A7.5 7.5 0 0013.5 3v7.5z"></path>
                        </svg>
                        Log Severity Ratio
                    </div>
                    <div class="dist-container">
                        <div class="dist-row">
                            <div class="dist-label">DEBUG</div>
                            <div class="dist-bar-bg"><div class="dist-bar-fill" id="bar-debug" style="--bar-color: var(--color-debug); --bar-glow: var(--glow-debug); width: 0%;"></div></div>
                            <div class="dist-val" id="val-debug">0%</div>
                        </div>
                        <div class="dist-row">
                            <div class="dist-label">INFO</div>
                            <div class="dist-bar-bg"><div class="dist-bar-fill" id="bar-info" style="--bar-color: var(--color-info); --bar-glow: var(--glow-info); width: 0%;"></div></div>
                            <div class="dist-val" id="val-info">0%</div>
                        </div>
                        <div class="dist-row">
                            <div class="dist-label">WARNING</div>
                            <div class="dist-bar-bg"><div class="dist-bar-fill" id="bar-warning" style="--bar-color: var(--color-warning); --bar-glow: var(--glow-warning); width: 0%;"></div></div>
                            <div class="dist-val" id="val-warning">0%</div>
                        </div>
                        <div class="dist-row">
                            <div class="dist-label">ERROR</div>
                            <div class="dist-bar-bg"><div class="dist-bar-fill" id="bar-error" style="--bar-color: var(--color-error); --bar-glow: var(--glow-error); width: 0%;"></div></div>
                            <div class="dist-val" id="val-error">0%</div>
                        </div>
                        <div class="dist-row">
                            <div class="dist-label">CRITICAL</div>
                            <div class="dist-bar-bg"><div class="dist-bar-fill" id="bar-critical" style="--bar-color: var(--color-critical); --bar-glow: var(--glow-critical); width: 0%;"></div></div>
                            <div class="dist-val" id="val-critical">0%</div>
                        </div>
                    </div>
                </div>
            </div>
        </main>
        
        <footer>
            Log Generator Simulator | API: <a href="/metrics" target="_blank">/metrics</a> | <a href="/api/stats" target="_blank">/api/stats</a>
        </footer>
        
        <div class="toast-container" id="toast-container"></div>
        
        <script>
            let lastLogsEmittedCount = 0;
            let currentLogs = [];
            
            function showToast(message, type = 'info') {
                const container = document.getElementById('toast-container');
                const toast = document.createElement('div');
                toast.className = 'toast';
                
                let icon = 'ℹ️';
                if (type === 'success') icon = '✅';
                if (type === 'error') icon = '❌';
                
                toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
                container.appendChild(toast);
                
                setTimeout(() => toast.classList.add('show'), 10);
                
                setTimeout(() => {
                    toast.classList.remove('show');
                    setTimeout(() => toast.remove(), 400);
                }, 3000);
            }
            
            function onSliderChange() {
                const minVal = parseFloat(document.getElementById('interval-min').value);
                let maxVal = parseFloat(document.getElementById('interval-max').value);
                
                if (maxVal < minVal) {
                    maxVal = minVal;
                    document.getElementById('interval-max').value = maxVal;
                }
                
                document.getElementById('min-val-display').textContent = minVal.toFixed(1) + 's';
                document.getElementById('max-val-display').textContent = maxVal.toFixed(1) + 's';
            }
            
            async function fetchStats() {
                try {
                    const response = await fetch('/api/stats');
                    if (!response.ok) throw new Error('Network error fetching stats');
                    const data = await response.json();
                    
                    document.getElementById('stat-total').textContent = data.total_logs;
                    document.getElementById('stat-debug').textContent = data.stats.DEBUG || 0;
                    document.getElementById('stat-info').textContent = data.stats.INFO || 0;
                    document.getElementById('stat-warning').textContent = data.stats.WARNING || 0;
                    document.getElementById('stat-error').textContent = data.stats.ERROR || 0;
                    document.getElementById('stat-critical').textContent = data.stats.CRITICAL || 0;
                    
                    const total = data.total_logs || 1;
                    const levels = ['debug', 'info', 'warning', 'error', 'critical'];
                    levels.forEach(lvl => {
                        const count = data.stats[lvl.toUpperCase()] || 0;
                        const pct = Math.round((count / total) * 100);
                        document.getElementById(`bar-${lvl}`).style.width = pct + '%';
                        document.getElementById(`val-${lvl}`).textContent = pct + '%';
                    });
                    
                    if (document.activeElement !== document.getElementById('log-format')) {
                        document.getElementById('log-format').value = data.config.format_type;
                    }
                    if (document.activeElement !== document.getElementById('log-pattern')) {
                        document.getElementById('log-pattern').value = data.config.pattern;
                    }
                    if (document.activeElement !== document.getElementById('interval-min') &&
                        document.activeElement !== document.getElementById('interval-max')) {
                        document.getElementById('interval-min').value = data.config.interval_min;
                        document.getElementById('interval-max').value = data.config.interval_max;
                        onSliderChange();
                    }
                    
                    const logBody = document.getElementById('terminal-body');
                    const hasNewLogs = data.latest_logs.length !== currentLogs.length || 
                        JSON.stringify(data.latest_logs) !== JSON.stringify(currentLogs);
                        
                    if (hasNewLogs) {
                        currentLogs = data.latest_logs;
                        logBody.innerHTML = '';
                        currentLogs.forEach(log => {
                            const div = document.createElement('div');
                            div.className = `log-line log-${log.level}`;
                            div.textContent = log.line;
                            logBody.appendChild(div);
                        });
                        logBody.scrollTop = logBody.scrollHeight;
                        
                        if (data.total_logs > lastLogsEmittedCount) {
                            const card = document.getElementById('stat-total');
                            card.style.transform = 'scale(1.04)';
                            card.style.transition = 'transform 0.08s ease';
                            setTimeout(() => card.style.transform = 'scale(1)', 80);
                            lastLogsEmittedCount = data.total_logs;
                        }
                    }
                } catch (err) {
                    console.error('Error fetching stats:', err);
                }
            }
            
            async function updateConfig() {
                const format = document.getElementById('log-format').value;
                const pattern = document.getElementById('log-pattern').value;
                const minVal = parseFloat(document.getElementById('interval-min').value);
                const maxVal = parseFloat(document.getElementById('interval-max').value);
                
                try {
                    const response = await fetch('/api/config', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            format_type: format,
                            pattern: pattern,
                            interval_min: minVal,
                            interval_max: maxVal
                        })
                    });
                    if (!response.ok) throw new Error();
                    showToast('Simulation settings updated', 'success');
                } catch (err) {
                    showToast('Failed to update config', 'error');
                }
            }
            
            async function triggerBurst(count) {
                try {
                    const response = await fetch('/api/burst', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ count })
                    });
                    if (!response.ok) throw new Error();
                    showToast(`Injected burst of ${count} messages`, 'success');
                } catch (err) {
                    showToast('Failed to trigger burst', 'error');
                }
            }
            
            async function sendManualLog(event) {
                event.preventDefault();
                const msgInput = document.getElementById('manual-msg');
                const levelSelect = document.getElementById('manual-level');
                
                const message = msgInput.value;
                const level = levelSelect.value;
                
                try {
                    const response = await fetch('/api/log', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ level, message })
                    });
                    if (!response.ok) throw new Error();
                    showToast(`Log injected as ${level}`, 'success');
                    msgInput.value = '';
                } catch (err) {
                    showToast('Failed to inject log', 'error');
                }
            }
            
            fetchStats();
            setInterval(fetchStats, 1000);
        </script>
</body>
</html>"""

class RequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Redirect request logs to DEBUG so they don't spam stdout of the test system
        logger = logging.getLogger("http")
        logger.debug(format % args)

    def do_GET(self):
        if self.path == "/":
            body = DASHBOARD_HTML.encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/metrics":
            uptime = time.time() - start_time
            with counter_handler.lock:
                stats = counter_handler.stats.copy()
            
            lines = [
                "# HELP log_generator_emitted_logs_total Total number of logs generated.",
                "# TYPE log_generator_emitted_logs_total counter",
            ]
            for lvl, count in stats.items():
                if lvl != "total":
                    lines.append(f'log_generator_emitted_logs_total{{level="{lvl}"}} {count}')
            
            lines.extend([
                "# HELP log_generator_uptime_seconds Uptime of the log generator in seconds.",
                "# TYPE log_generator_uptime_seconds gauge",
                f"log_generator_uptime_seconds {uptime}",
                "# HELP log_generator_bursts_total Total number of bursts triggered.",
                "# TYPE log_generator_bursts_total counter",
                f"log_generator_bursts_total {burst_triggered_count}"
            ])
            body = ("\n".join(lines) + "\n").encode('utf-8')
            
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
            
        elif self.path == "/api/stats":
            uptime = time.time() - start_time
            with counter_handler.lock:
                stats = counter_handler.stats.copy()
                latest = list(counter_handler.latest_logs)
            
            with log_config_lock:
                config_data = {
                    "format_type": log_config.format_type,
                    "pattern": log_config.pattern,
                    "interval_min": log_config.interval_min,
                    "interval_max": log_config.interval_max,
                    "burst_count": log_config.burst_count
                }
                
            response = {
                "uptime": uptime,
                "total_logs": stats["total"],
                "stats": {k: v for k, v in stats.items() if k != "total"},
                "latest_logs": latest,
                "config": config_data
            }
            body = json.dumps(response).encode('utf-8')
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
        else:
            body = json.dumps({"error": "Not Found"}).encode('utf-8')
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
            
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8')) if post_data else {}
        except Exception:
            body = json.dumps({"error": "Invalid JSON"}).encode('utf-8')
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
            return
            
        if self.path == "/api/config":
            global log_config
            with log_config_lock:
                if "format_type" in data:
                    log_config.format_type = str(data["format_type"]).upper()
                if "pattern" in data:
                    log_config.pattern = str(data["pattern"]).lower()
                if "interval_min" in data:
                    log_config.interval_min = float(data["interval_min"])
                if "interval_max" in data:
                    log_config.interval_max = float(data["interval_max"])
                    
                resp_config = {
                    "format_type": log_config.format_type,
                    "pattern": log_config.pattern,
                    "interval_min": log_config.interval_min,
                    "interval_max": log_config.interval_max
                }
            body = json.dumps({"status": "success", "config": resp_config}).encode('utf-8')
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
            
        elif self.path == "/api/log":
            level_name = data.get("level", "INFO").upper()
            message = data.get("message", "Manual test log triggered")
            
            level_val = getattr(logging, level_name, logging.INFO)
            logging.getLogger("manual").log(level_val, message)
            
            body = json.dumps({"status": "success", "logged": {"level": level_name, "message": message}}).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
            
        elif self.path == "/api/burst":
            global burst_triggered_count
            count = int(data.get("count", 10))
            if count <= 0 or count > 500:
                body = json.dumps({"error": "Count must be between 1 and 500"}).encode('utf-8')
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(body)
                return
                
            with log_config_lock:
                log_config.burst_count += count
                burst_triggered_count += 1
                
            body = json.dumps({"status": "success", "burst_queued": count}).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
        else:
            body = json.dumps({"error": "Not Found"}).encode('utf-8')
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)

def log_generator_loop():
    levels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]
    start_loop_time = time.time()
    
    while True:
        has_burst = False
        with log_config_lock:
            if log_config.burst_count > 0:
                log_config.burst_count -= 1
                has_burst = True
        
        if has_burst:
            level = random.choice([logging.WARNING, logging.ERROR, logging.CRITICAL])
            msg = f"BURST ACTIVE: {random.choice(MESSAGES)}"
            logging.getLogger("generator").log(level, msg)
            time.sleep(0.08)
            continue
            
        level = random.choice(levels)
        msg = random.choice(MESSAGES)
        logging.getLogger("generator").log(level, msg)
        
        with log_config_lock:
            pattern = log_config.pattern
            interval_min = log_config.interval_min
            interval_max = log_config.interval_max
        
        if pattern == 'constant':
            delay = interval_min
        elif pattern == 'sinewave':
            elapsed = time.time() - start_loop_time
            sine_val = math.sin(elapsed * (2 * math.pi / 120.0))  # 120 second period
            normalized_sine = (sine_val + 1.0) / 2.0
            delay = interval_min + (1.0 - normalized_sine) * (interval_max - interval_min)
        elif pattern == 'burst':
            if random.random() < 0.05:  # 5% chance to start a burst
                with log_config_lock:
                    log_config.burst_count += random.randint(10, 25)
                delay = 0.1
            else:
                delay = random.uniform(interval_min, interval_max)
        else:  # random
            delay = random.uniform(interval_min, interval_max)
            
        # Responsive sleeping: sleep in 100ms chunks to allow interruption / config change
        sleep_end = time.time() + delay
        while time.time() < sleep_end:
            with log_config_lock:
                if log_config.burst_count > 0:
                    break
            time.sleep(0.1)

if __name__ == "__main__":
    # Clear existing handlers
    root_logger = logging.getLogger()
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)
        
    root_logger.setLevel(getattr(logging, LOG_LEVEL, logging.DEBUG))
    
    # Configure stdout stream handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(DynamicFormatter())
    root_logger.addHandler(stream_handler)
    
    # Configure counters handler
    root_logger.addHandler(counter_handler)
    
    # Start HTTP Server in daemon thread
    server_address = ('', PORT)
    httpd = ThreadingHTTPServer(server_address, RequestHandler)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    
    # Log startup configuration
    logging.info(f"Log Generator Service started (Listening on port {PORT})")
    logging.info(f"Dashboard available at http://localhost:{PORT}/")
    logging.info(f"Prometheus metrics at http://localhost:{PORT}/metrics")
    
    try:
        log_generator_loop()
    except KeyboardInterrupt:
        logging.info("Shutting down log generator...")
        httpd.shutdown()
        sys.exit(0)
