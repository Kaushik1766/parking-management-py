version = 1.0.7
build:
	uv export --no-dev --format requirements-txt --output-file requirements.txt
	docker buildx build \
		--platform linux/amd64,linux/arm64 \
		-t 513758042129.dkr.ecr.ap-south-1.amazonaws.com/parking-management-py:$(version) \
		--push .

upload:
	docker tag parking-management-py:$(version) 513758042129.dkr.ecr.ap-south-1.amazonaws.com/parking-management-py:$(version)
	docker push 513758042129.dkr.ecr.ap-south-1.amazonaws.com/parking-management-py:$(version)
