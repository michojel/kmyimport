with import <nixpkgs> {};
with pkgs.python36Packages;

buildPythonPackage rec {
  name = "kmyimport";
  src = "./";
  propagatedBuildInputs = [ autopep8 pylint yapf flake8 ];
}
