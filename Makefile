APPNAME="predi"
TYPE=python
PYTHONVERSION="3.10"
EXTRAS="none"
BEM_URL_BASE="https://github.com/terminal-labs/bash-environment-manager"
BEM_BRANCH="pyproject"
SHELF_BRANCH="master"

help:
	@echo "usage: make [command]"

download_bash_environment_manager:
	@if test ! -d ".tmp/bash-environment-manager";then \
		sudo su -m $(SUDO_USER) -c "mkdir -p .tmp"; \
		sudo su -m $(SUDO_USER) -c "cd .tmp; wget -O bash-environment-manager.zip $(BEM_URL_BASE)/archive/refs/heads/$(BEM_BRANCH).zip"; \
		sudo su -m $(SUDO_USER) -c "cd .tmp; unzip bash-environment-manager.zip"; \
		sudo su -m $(SUDO_USER) -c "cd .tmp; mv bash-environment-manager-$(BEM_BRANCH) bash-environment-manager"; \
		sudo su -m $(SUDO_USER) -c "cd .tmp; mkdir -p download; mv bash-environment-manager.zip download/bash-environment-manager.zip"; \
	fi

conda: NAMESPACE="conda"
conda: HOSTTYPE="host"
conda: download_bash_environment_manager
	@sudo bash .tmp/bash-environment-manager/configuration/namespaces/types/$(TYPE)/assemble.sh $(APPNAME) $(SUDO_USER) $(NAMESPACE) $(TYPE) $(PYTHONVERSION) $(HOSTTYPE)

vagrant.conda: NAMESPACE="vagrant-conda"
conda: HOSTTYPE="vagrant"
vagrant.conda: download_bash_environment_manager
	@if test ! -f "Vagrantfile";then \
		wget https://raw.githubusercontent.com/terminal-labs/bash-environment-shelf/$(SHELF_BRANCH)/vagrantfiles/Vagrantfile; \
		chown $(SUDO_USER) Vagrantfile; \
	fi
	@sudo bash .tmp/bash-environment-manager/configuration/namespaces/types/$(TYPE)/assemble.sh $(APPNAME) $(SUDO_USER) $(NAMESPACE) $(TYPE) $(PYTHONVERSION) $(HOSTTYPE)
nuke:
	@if test -f "Vagrantfile";then \
		vagrant destroy -f; \
	fi
	@if test -f ".reset_env.sh";then \
		sudo bash .reset_env.sh; \
	fi
	@git clean -Xdf;

blacken:
	@black --line-length 150 .;
lint: blacken
	@flake8 --max-line-length=150  --exclude .tmp/ . || true;
