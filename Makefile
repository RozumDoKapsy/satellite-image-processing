.PHONY: install-terraform install-kubectl install-docker install-all  uninstall-terraform uninstall-kubectl uninstall-docker uninstall-all

install-terraform:
	@echo "Installing terraform..."
	@if ! command -v terraform >/dev/null 2>&1; then \
		sudo apt-get update && sudo apt-get install -y gnupg software-properties-common; \
		wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg > /dev/null; \
		echo "deb [arch=$$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $$(grep -oP '(?<=UBUNTU_CODENAME=).*' /etc/os-release || lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list; \
		sudo apt update; \
		sudo apt-get install terraform; \
	fi
	@terraform -version

install-kubectl:
	@echo "Installing kubectl..."
	@ if ! command -v kubectl >/dev/null 2>&1; then \
		curl -LO "https://dl.k8s.io/release/$$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"; \
		chmod +x ./kubectl; \
		sudo mv ./kubectl /usr/local/bin/kubectl; \
	  fi
	@kubectl version --client

install-docker:
	@echo "Installing Docker.."
	@if ! command -v docker >/dev/null 2>&1; then \
		sudo apt-get update; \
		sudo mkdir -p /etc/apt/keyrings; \
		curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg; \
		sudo chmod a+r /etc/apt/keyrings/docker.gpg; \
		curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg; \
		echo "deb [arch=$$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $$(grep -oP '(?<=UBUNTU_CODENAME=).*' /etc/os-release || lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null; \
		sudo apt-get update; \
		sudo apt-get install -y docker-ce docker-ce-cli containerd.io; \
		sudo usermod -aG docker $${USER}; \
		newgrp docker; \
	fi
	@docker run hello-world

install-all: install-terraform install-kubectl install-docker

uninstall-terraform:
	@echo "Uninstalling terraform..."
	sudo apt remove terraform
	sudo rm -f /etc/apt/sources.list.d/hashicorp.list
	sudo rm -f /usr/share/keyrings/hashicorp-archive-keyring.gpg
	sudo apt update
	@echo "Terraform has been uninstalled."

uninstall-kubectl:
	@echo "Uninstalling kubectl..."
	sudo rm -f /usr/local/bin/kubectl
	@echo "Kubectl has been uninstalled."

uninstall-docker:
	@echo "Uninstalling Docker..."
	sudo systemctl stop docker.socket docker.service docker-containerd || true
	sudo apt purge docker-ce docker-ce-cli containerd.io docker-compose-plugin || true
	sudo rm -rf /var/lib/docker || true
	sudo rm -rf /var/lib/containerd || true
	sudo rm -f /etc/apt/sources.list.d/docker.list || true
	sudo rm -f /usr/share/keyrings/docker-archive-keyring.gpg || true
	sudo rm -f /etc/apt/keyrings/docker.gpg || true
	sudo rm -rf /etc/apt/keyrings/docker.asc
	sudo apt-get autoremove -y || true
	@echo "Docker has been uninstalled."

uninstall-all: uninstall-terraform uninstall-kubectl uninstall-docker
