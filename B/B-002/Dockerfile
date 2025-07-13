FROM ghcr.io/jmuchovej/devcontainers/latex:2025

USER root

# Note tikz is in the pgf package
RUN <<EOF
    tlmgr update --self
    tlmgr install setspace.sty transparent pdflscape svg pgf booktabs breqn caption ec fc gensymb lastpage makecell mathtools multirow paralist parskip sectsty subfig tex4ht tocbibind tocloft
    mktexpk --mfmode / --bdpi 600 --mag 1+0/600 --dpi 600 tcrm1095
    mktexpk --mfmode / --bdpi 600 --mag 1+0/600 --dpi 600 tcrm0900
    mktexpk --mfmode / --bdpi 600 --mag 1+0/600 --dpi 600 tcrm0600
    mktexpk --mfmode / --bdpi 600 --mag 1+0/600 --dpi 600 tcrm0800
EOF

USER vscode