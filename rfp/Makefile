# Variables
PROFILE=dor_justt_development
REGION=us-east-1
ACCOUNT=295246714779
REPO_NAME=rfp-server
ECR_URL=$(ACCOUNT).dkr.ecr.$(REGION).amazonaws.com

# Build the Docker image
build:
	docker build -t $(REPO_NAME):latest .

# Create repository (you only need to run this once)
# create-repo:
#	aws ecr create-repository --repository-name $(REPO_NAME) --profile $(PROFILE) --region $(REGION)

# Login, tag, and push
push: build
	aws ecr get-login-password --region $(REGION) --profile $(PROFILE) | docker login --username AWS --password-stdin $(ECR_URL)
	docker tag $(REPO_NAME):latest $(ECR_URL)/$(REPO_NAME):latest
	docker push $(ECR_URL)/$(REPO_NAME):latest

# See what's in the repository
list-images:
	aws ecr list-images --repository-name $(REPO_NAME) --profile $(PROFILE) --region $(REGION)