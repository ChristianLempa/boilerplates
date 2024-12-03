# -- Change GitLab settings here...
external_url 'https://your-gitlab-fqdn'  # <-- Replace with your GitLab FQDN

# -- (Optional) Change GitLab Shell settings here...
gitlab_rails['gitlab_shell_ssh_port'] = 2424

# -- Change internal web service settings here...
letsencrypt['enable'] = false
nginx['listen_port']  = 80
nginx['listen_https'] = false

# --> (Optional) Enable Container Registry settings here...
# registry_external_url 'https://your-registry-fqdn'  # <-- Replace with your registry FQDN
# gitlab_rails['registry_enabled']  = true
# registry_nginx['listen_https']    = false
# registry_nginx['listen_port']     = 5678  # <-- Replace with your registry port
# <--

# --> (Optional) Add Authentik settings here...
# gitlab_rails['omniauth_auto_link_user'] = ['openid_connect']
# gitlab_rails['omniauth_providers'] = [
#   {
#     name: "openid_connect",  #  !-- Do not change this parameter
#     label: "Authentik",  # <-- (Optional) Change name for login button, defaults to "Openid Connect"
#     icon: "https://avatars.githubusercontent.com/u/82976448?s=200&v=4",
#     args: {
#       name: "openid_connect",
#       scope: ["openid","profile","email"],
#       response_type: "code",
#       issuer: "https://your-authentik-fqdn/application/o/your-gitlab-slug/",  # <-- Replace with your Authentik FQDN and GitLab slug
#       discovery: true,
#       client_auth_method: "query",
#       uid_field: "email",
#       send_scope_to_token_endpoint: "false",
#       pkce: true,
#       client_options: {
#         identifier: "your-authentik-provider-client-id",  # <-- Replace with your Authentik provider client ID
#         secret: "your-authentik-provider-client-secret",  # <-- Replace with your Authentik provider client secret
#         redirect_uri: "https://your-authentik-fqdn/users/auth/openid_connect/callback"  # <-- Replace with your Authentik FQDN
#       }
#     }
#   }
# ]
# <--

# --> (Optional) Change SMTP settings here...
# gitlab_rails['smtp_enable']           = true
# gitlab_rails['smtp_address']          = "your-smtp-server-addr"  # <-- Replace with your SMTP server address
# gitlab_rails['smtp_port']             = 465
# gitlab_rails['smtp_user_name']        = "your-smtp-username"  # <-- Replace with your SMTP username
# gitlab_rails['smtp_password']         = "your-smtp-password"  # <-- Replace with your SMTP password
# gitlab_rails['smtp_domain']           = "your-smtp-domain"  # <-- Replace with your SMTP domain
# gitlab_rails['smtp_authentication']   = "login"
# gitlab_rails['smtp_ssl']              = true
# gitlab_rails['smtp_force_ssl']        = true
# gitlab_rails['gitlab_email_from']     = 'your-email-from-addr'  # <-- Replace with your email from address
# gitlab_rails['gitlab_email_reply_to'] = 'your-email-replyto-addr'  # <-- Replace with your email reply-to address
# <--
