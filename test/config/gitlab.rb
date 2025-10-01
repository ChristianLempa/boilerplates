# GitLab Configuration
external_url 'https://gitlab.example.com'

# GitLab Shell SSH settings
gitlab_rails['gitlab_shell_ssh_port'] = 2424

# Internal web service settings
# Let's Encrypt certificate management (when not using Traefik)
letsencrypt['enable'] = true
letsencrypt['contact_emails'] = ['admin@example.com']
nginx['redirect_http_to_https'] = true



