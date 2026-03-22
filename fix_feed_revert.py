import sys

with open('src/components/IntelligenceFeed.js', 'r') as f:
    content = f.read()

# Revert monitor.query_text back to monitor.term
content = content.replace('{monitor.query_text}', '{monitor.term}')
content = content.replace('monitor.query_text:', 'monitor.term:')
content = content.replace('monitor.query_text}', 'monitor.term}')
content = content.replace('selectedMonitor.query_text', 'selectedMonitor.term')
content = content.replace('monitor.query_text', 'monitor.term')

# Revert monitor.id back to monitor.monitor_id
content = content.replace('selectedMonitor?.id', 'selectedMonitor?.monitor_id')
content = content.replace('monitor.id', 'monitor.monitor_id')

with open('src/components/IntelligenceFeed.js', 'w') as f:
    f.write(content)
