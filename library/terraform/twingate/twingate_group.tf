resource "twingate_group" "administrators" {
  name = "Administrators"

  user_ids = [
    data.twingate_user.admin.id
  ]
}
