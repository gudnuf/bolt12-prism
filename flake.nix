{
  description = "For developing CLN plugins";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        clightning = pkgs.clightning.overrideAttrs (final: prev: {
            version = "v23.11rc1";
            src = pkgs.fetchFromGitHub {
                owner = "ElementsProject";
                repo = "lightning";
                rev = "v23.11rc1";
                fetchSubmodules = true;
                sha256 = "sha256-qKmb++5DrJ8/hgg+mksOSPo3h5m3aAGOHBR6BkZw3TM=";
            };
            configureFlags = [ "--disable-valgrind" ];
            makeFlags = [ "VERSION=v23.11rc1" ];
        });
        pyln_bolt7 = pkgs.python3Packages.buildPythonPackage rec {
            pname = "pyln_bolt7";
            version = "cd894663";
            src = pkgs.fetchFromGitHub {
              owner = "niftynei";
              repo = "${pname}";
              rev = "${version}";
              sha256 = "sha256-//XG8aF2mW5DX0sBsAV1bL+9RLrvUXYpPSX9bz5f/OU=";
            };
            doCheck = false;
            propagatedBuildInputs = [];
        };
        bech32ref = pkgs.python3Packages.buildPythonPackage rec {
            pname = "bech32ref";
            version = "5f11b2e";
            src = pkgs.fetchFromGitHub {
              owner = "niftynei";
              repo = "${pname}";
              rev = "${version}";
              sha256 = "sha256-fvR6y2FpEE5sWLDOGLCOR180W15P5t+PmroHRNbWQbA=";
            };
            doCheck = false;
            propagatedBuildInputs = [];
        };
        pyln_proto = pkgs.python3Packages.buildPythonPackage rec {
            pname = "pyln_proto";
            version = "87643bed";
            src = pkgs.fetchFromGitHub {
              owner = "niftynei";
              repo = "${pname}";
              rev = "${version}";
              sha256 = "sha256-q8Qh39e23C0jyerRlfobArKwWB9Zj3ghFS479oxcep8=";
            };
            doCheck = false;
            propagatedBuildInputs = [];
        };
        pyln_client = pkgs.python3Packages.buildPythonPackage rec {
            pname = "pyln_client";
            version = "23.5.2";
            src = pkgs.fetchFromGitHub {
              inherit version;
              owner = "niftynei";
              repo = "${pname}";
              rev = "250b8a2";
              sha256 = "sha256-vhGyBA5C5bgi5nMHgs9hjIUGOOKTwV31/OeBnQJUaL0=";
            };
            doCheck = false;
            propagatedBuildInputs = [ pyln_proto pyln_bolt7];
        };
      in
      {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            bashInteractive
            jq
            bitcoind
            clightning
            git
            pyln_client
            pyln_proto
            pyln_bolt7
            bech32ref

            # deps for startup_regtest.sh
            libeatmydata
            gawk

            (python3.withPackages (ps: with ps; with python3Packages; [
              ipython
              pip
              base58
              bitstring
              pysocks
              cryptography
              coincurve
            ]))
          ];
          # Automatically run jupyter when entering the shell.
          shellHook = ''
            export PATH_TO_BITCOIN=$(pwd)/.bitcoin
            export PATH_TO_LIGHTNING=$(pwd)/.lightning_nodes
            mkdir -p $PATH_TO_BITCOIN
            mkdir -p $PATH_TO_LIGHTNING
          '';

          BITCOIN_BIN_DIR = "${pkgs.bitcoind}/bin";
          LIGHTNING_BIN_DIR= "${clightning}/bin";
        };
      });
}