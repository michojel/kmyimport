Conversion scripts for KMyMoney
------------------------------

Installation with nix under user
================================

Add the following to `~/.config/nixpkgs/config.nix`:

.. code-block:: nix
  with import <nixpkgs> {};

  let
    scriptsBaseDir = ~/wsp/my/kmyimport;
  in {
    packageOverrides = super: let self = super.pkgs; in {
      kmyimport = import "${scriptsBaseDir}/kmyimport.nix" {
        path    = "${scriptsBaseDir}";
        pkgs    = self;
      };
  };

Run `nix-enf -if '<nixpkgs>' kmymoney`.

Development under nix
=====================

`nix-shell shell.nix`


