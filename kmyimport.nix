{ path ? ".", pkgs ? import <nixpkgs> {} }:

{
  kmyimport = with pkgs.python36Packages; buildPythonPackage rec {
    name = "kmyimport";
    src = "${path}/setup.py";
    propagatedBuildInputs = [];
  };
}
