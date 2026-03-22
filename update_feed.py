import sys

with open('src/components/IntelligenceFeed.js', 'r') as f:
    content = f.read()

# Replace monitor.term with monitor.query_text
content = content.replace('{monitor.term}', '{monitor.query_text}')
content = content.replace('monitor.term:', 'monitor.query_text:')
content = content.replace('monitor.term}', 'monitor.query_text}') # for the map key

# Replace monitor.monitor_id with monitor.id
content = content.replace('monitor.monitor_id', 'monitor.id')

with open('src/components/IntelligenceFeed.js', 'w') as f:
    f.write(content)
