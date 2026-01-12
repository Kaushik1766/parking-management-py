version = 1.0.5
build:
	uv export --no-dev --format requirements-txt --output-file requirements.txt
	docker build \
		-t parking-management-py:$(version) .

upload:
	docker tag parking-management-py:$(version) 513758042129.dkr.ecr.ap-south-1.amazonaws.com/parking-management-py:$(version)
	docker push 513758042129.dkr.ecr.ap-south-1.amazonaws.com/parking-management-py:$(version)
