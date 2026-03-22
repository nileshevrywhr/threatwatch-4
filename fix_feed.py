import sys

with open('src/components/IntelligenceFeed.js', 'r') as f:
    content = f.read()

# Fix selectedMonitor?.monitor_id to selectedMonitor?.id
content = content.replace('selectedMonitor?.monitor_id', 'selectedMonitor?.id')

# Fix monitor.term inside the template literal for gathering intelligence
content = content.replace('selectedMonitor.term', 'selectedMonitor.query_text')

# Fix enrichment term
content = content.replace('monitor.term', 'monitor.query_text')

with open('src/components/IntelligenceFeed.js', 'w') as f:
    f.write(content)
