{
  description = "Flake for github:mahyarmirrashed/ham-radio-course";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        pythonEnv = pkgs.python312.withPackages (
          ps: with ps; [
            typer
            requests
          ]
        );
      in
      {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            pnpm
            pythonEnv
          ];
          shellHook = ''
            export PATH="$PATH:$(pnpm bin)"
          '';
        };
      }
    );
}
