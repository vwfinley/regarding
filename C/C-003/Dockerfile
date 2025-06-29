FROM ghcr.io/jmuchovej/devcontainers/latex:2025

USER root

RUN <<EOF
    tlmgr install booktabs breqn caption ec fc gensymb lastpage makecell mathtools multirow paralist parskip pgf sectsty subfig tex4ht tocbibind tocloft
    mktexpk --mfmode / --bdpi 600 --mag 1+0/600 --dpi 600 tcrm1095
    mktexpk --mfmode / --bdpi 600 --mag 1+0/600 --dpi 600 tcrm0900
    mktexpk --mfmode / --bdpi 600 --mag 1+0/600 --dpi 600 tcrm0600
    mktexpk --mfmode / --bdpi 600 --mag 1+0/600 --dpi 600 tcrm0800
EOF

USER vscode



# FROM mcr.microsoft.com/devcontainers/base:dev-debian-12
# 
# RUN apt-get update
# 
# RUN <<EOF
#     cd /tmp
#     wget https://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz
#     zcat < install-tl-unx.tar.gz | tar xf -
#     cd install-tl-2*
#     perl ./install-tl --scheme=basic --no-interaction --no-doc-install --no-src-install
#     export PATH=$PATH:/usr/local/texlive/2025/bin/x86_64-linux
#     tlmgr update --all
#     rm -r /tmp/install-tl-*
# EOF
# 
# RUN <<EOF
#     echo 'PATH=$PATH:/usr/local/texlive/2025/bin/x86_64-linux' > /etc/profile.d/texlive_path.sh
#     echo 'export PATH=$PATH:/usr/local/texlive/2025/bin/x86_64-linux' >> ~/.bashrc
# EOF
# 
# 
# # Add extra packages
# #USER root
# RUN <<EOF
#     export PATH=$PATH:/usr/local/texlive/2025/bin/x86_64-linux
#     tlmgr install booktabs breqn caption ec fc gensymb lastpage makecell mathtools multirow paralist parskip pgf sectsty subfig tex4ht tocbibind tocloft
#     mktexpk --mfmode / --bdpi 600 --mag 1+0/600 --dpi 600 tcrm1095
#     mktexpk --mfmode / --bdpi 600 --mag 1+0/600 --dpi 600 tcrm0900
#     mktexpk --mfmode / --bdpi 600 --mag 1+0/600 --dpi 600 tcrm0600
#     mktexpk --mfmode / --bdpi 600 --mag 1+0/600 --dpi 600 tcrm0800
# EOF
# #USER vscode
# 