# Third-party source notices

`fetch.py` downloads these exact upstream Git commits as GitHub codeload
archives, verifies the archive SHA-256 in `pins.json`, and retains the upstream
trees (including license material) in the selected installation directory.

| Project | Pinned revision | License and attribution |
| --- | --- | --- |
| [zsh-autosuggestions](https://github.com/zsh-users/zsh-autosuggestions) | `85919cd1ffa7d2d5412f6d3fe437ebdbeeec4fc5` | MIT. Copyright (c) 2013 Thiago de Arruda; Copyright (c) 2016-2021 Eric Freese. The archive contains `LICENSE`. |
| [zsh-history-substring-search](https://github.com/zsh-users/zsh-history-substring-search) | `a0bdb0d47dbaba31dba2db7af8c48a5d9c74049a` | BSD-3-Clause terms and contributor notices are in the upstream script header. This pinned tree has no separate license file; its README history also records the three-clause BSD release. |
| [zsh-syntax-highlighting](https://github.com/zsh-users/zsh-syntax-highlighting) | `e6683f20e5c38d3e5447f45845d04ddda75d0f23` | BSD-3-Clause. Copyright (c) 2010-2020 zsh-syntax-highlighting contributors. The archive contains `COPYING.md`. |
| [Powerlevel10k](https://github.com/romkatv/powerlevel10k) | `d05a1b00f9a61f9578bf9dc19b8451942dde8734` | MIT. The archive also contains the bundled `gitstatus` component under GPL-3.0; both upstream `LICENSE` files are retained. Powerlevel10k and earlier Powerlevel9k copyright notices remain in the top-level license. |

The shared Zsh core and exported Powerlevel10k files are first-party Niri Plus
source. The prompt preserves the selected native semantic color roles. Its
portable proc/sys roots and quiet file reader make status probes testable; they
default to the ordinary Linux interfaces. Caller-specific history and cache
paths, Ghostty, SDK, CLI, editor, and browser setup remain caller-owned.

These files are not upstream files. The custom prompt functions retain their
own Niri Plus attribution in this repository.
