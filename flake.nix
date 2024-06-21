{
  description = "EasyCSV the easiest way to parse CSV";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; }) mkPoetryEnv;
        env = mkPoetryEnv {
          projectDir = ./.;
          editablePackageSources = { easy-csv = ./easy_csv; };
          preferWheels = true;
          python = pkgs.python310;
        };
      in {
        devShells.default = pkgs.mkShell {
          buildInputs = [ env ];
          packages = [ pkgs.poetry pkgs.ruff pkgs.pyright ];
        };
      });
}
