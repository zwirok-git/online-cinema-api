
set -e

if [ -z "$API_USER" ] || [ -z "$API_PASSWORD" ]; then
    echo "ERROR: API_USER and API_PASSWORD must be set."
    exit 1
fi

echo "Creating .htpasswd file."

if [ ! -f /etc/nginx/.htpasswd ]; then
    printf '%s' "$API_PASSWORD" | htpasswd -ci /etc/nginx/.htpasswd "$API_USER"
else
    printf '%s' "$API_PASSWORD" | htpasswd -i /etc/nginx/.htpasswd "$API_USER"
fi

cat <<EOL > /etc/nginx/conf.d/auth.conf
auth_basic "Restricted Access";
auth_basic_user_file /etc/nginx/.htpasswd;
EOL

echo "Basic Auth setup complete."

exec "$@"
