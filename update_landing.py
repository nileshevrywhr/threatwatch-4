import sys

with open('src/components/LandingPage.js', 'r') as f:
    content = f.read()

old_code = """    try {
      const response = await axios.post(`${API}/monitors`, {
        term: formData.term,
        frequency: formData.frequency
      }, {
        headers: {
          'Authorization': `Bearer ${session?.access_token}`,
          'Content-Type': 'application/json'
        }
      });"""

new_code = """    try {
      await createMonitor({
        term: formData.term,
        frequency: formData.frequency
      });"""

if old_code in content:
    updated_content = content.replace(old_code, new_code)
    with open('src/components/LandingPage.js', 'w') as f:
        f.write(updated_content)
    print("Successfully updated LandingPage.js")
else:
    print("Old code block not found")
