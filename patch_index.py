import re

with open('/home/runner/work/WebMCP/WebMCP/index.html', 'r') as f:
    content = f.read()

# Add meta tags and fonts
meta_and_fonts = """    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="
        default-src 'self';
        script-src 'self' 'unsafe-inline' 'unsafe-eval';
        style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
        font-src 'self' https://fonts.gstatic.com;
        connect-src 'self' ws://localhost:* wss://localhost:* ws://127.0.0.1:* wss://127.0.0.1:*;
        img-src 'self' data:;
        base-uri 'self';
        form-action 'self';
    " />
    <meta http-equiv="X-Content-Type-Options" content="nosniff" />
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Geist:wght@100..900&family=Geist+Mono:wght@100..900&display=swap" rel="stylesheet">"""

content = re.sub(r'    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">', meta_and_fonts, content)

# Replace styles
new_styles = """
    <style>
        :root {
            --space: #0A1628;
            --cyan: #00E5FF;
            --amber: #FFB300;
            --crimson: #FF3D5A;
            --violet: #B388FF;
            --green: #38E8A0;
        }

        body {
            font-family: "Geist", Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.5;
            background-color: var(--space);
            color: #e0e0e0;
        }

        h1, h2, h3 {
            color: var(--cyan);
        }

        .demo-section {
            margin-bottom: 30px;
            padding: 20px;
            background-color: rgba(14, 30, 54, 0.55);
            backdrop-filter: blur(14px);
            border: 1px solid rgba(120, 170, 230, 0.14);
            border-radius: 16px;
        }
        
        .demo-section.glass-strong {
            background-color: rgba(10, 22, 40, 0.78);
            backdrop-filter: blur(18px);
        }

        code, pre {
            font-family: "Geist Mono", monospace;
        }

        code {
            background-color: rgba(0, 0, 0, 0.3);
            padding: 2px 4px;
            border-radius: 3px;
            color: var(--amber);
        }

        pre {
            background-color: rgba(0, 0, 0, 0.4);
            padding: 10px;
            border-radius: 8px;
            overflow-x: auto;
            border: 1px solid rgba(120, 170, 230, 0.1);
        }

        button {
            padding: 8px 15px;
            background-color: var(--cyan);
            color: var(--space);
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin-right: 10px;
            margin-bottom: 5px;
            font-weight: bold;
            transition: opacity 0.2s;
        }
        
        button:hover {
            opacity: 0.8;
        }

        input[type="text"] {
            padding: 8px;
            border: 1px solid rgba(120, 170, 230, 0.3);
            border-radius: 5px;
            background-color: rgba(0, 0, 0, 0.2);
            color: white;
            margin-right: 10px;
        }

        .tab-container {
            display: flex;
            margin-bottom: 20px;
            border-bottom: 1px solid rgba(120, 170, 230, 0.2);
        }

        .tab {
            padding: 10px 20px;
            cursor: pointer;
            background-color: transparent;
            color: #aaa;
            border-bottom: 3px solid transparent;
            border-radius: 0;
            margin: 0;
        }

        .tab.active {
            color: var(--cyan);
            border-bottom: 3px solid var(--cyan);
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        .status-box {
            padding: 10px;
            border-radius: 5px;
            margin-top: 20px;
            background-color: rgba(0, 0, 0, 0.2);
            border-left: 4px solid #666;
        }

        .status-connected {
            border-left-color: var(--green);
        }

        .status-disconnected {
            border-left-color: var(--crimson);
        }
        
        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: transparent;
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(120, 170, 230, 0.22);
            border-radius: 3px;
        }
    </style>
"""

# replace the style tag
content = re.sub(r'    <style>.*?</style>', new_styles, content, flags=re.DOTALL)

with open('/home/runner/work/WebMCP/WebMCP/index.html', 'w') as f:
    f.write(content)
