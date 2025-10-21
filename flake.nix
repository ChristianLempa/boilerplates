{
  description = "A curated collection of production-ready templates for your homelab and infrastructure projects";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
  }:
    flake-utils.lib.eachDefaultSystem (
      system: let
        pkgs = nixpkgs.legacyPackages.${system};

        boilerplates = pkgs.python3Packages.buildPythonApplication {
          pname = "boilerplates";
          version = "0.0.6";

          src = ./.;

          format = "pyproject";

          nativeBuildInputs = with pkgs.python3Packages; [
            setuptools
            wheel
          ];

          propagatedBuildInputs = with pkgs.python3Packages; [
            typer
            rich
            pyyaml
            python-frontmatter
            jinja2
          ];

          meta = with pkgs.lib; {
            description = "A CLI for managing boilerplates and templates";
            homepage = "https://github.com/christianlempa/boilerplates";
            license = licenses.mit;
            maintainers = ["Théo Posty <theo+github@posty.fr>"];
            mainProgram = "boilerplates";
          };
        };
      in {
        packages = {
          default = boilerplates;
          boilerplates = boilerplates;
        };

        apps = {
          default = {
            type = "app";
            program = "${boilerplates}/bin/boilerplates";
          };
        };
      }
    );
}
