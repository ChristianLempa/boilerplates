data "twingate_user" "admin" {
  id = ""  # FIXME Replace with actual user ID
}

resource "twingate_user" "new_user" {
  email       = "new.user@example.com"
  first_name  = "New"
  last_name   = "User"
  role        = "DEVOPS" # NOTE Defines the role, either ADMIN, DEVOPS, SUPPORT or MEMBER
  send_invite = true
}
