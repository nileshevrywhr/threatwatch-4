#!/bin/bash
# Generate secure JWT secret for production

echo "🔐 Generating secure JWT secret..."
JWT_SECRET=$(openssl rand -base64 32)
echo "Your secure JWT secret key:"
echo "JWT_SECRET_KEY=$JWT_SECRET"
echo ""
echo "⚠️  IMPORTANT: Save this secret securely and use it in your production environment!"
echo "   Do not commit this to version control."
