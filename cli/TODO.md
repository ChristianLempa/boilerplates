# TODO ITEMS

* Consider creating a "secret" variable type that automatically handles sensitive data and masks input during prompts, which also should be set via .env file and not directly in the compose files or other templates.
  * Implement multi-file support for templates, allowing jinja2 in other files as well
  * Mask secrets in rendering output (e.g. when displaying the final docker-compose file, mask secret values)
  * Add support for --out to specify a directory
* Add support for more complex validation rules for environment variables, such as regex patterns or value ranges.
* Add configuration support to allow users to override module and template spec with their own (e.g. defaults -> compose -> spec -> general ...)
* Add an installation script when cloning the repo and setup necessary commands
* Add an automatic update script to keep the tool up-to-date with the latest version from the repository.
* Add compose deploy command to deploy a generated compose project to a local or remote docker environment