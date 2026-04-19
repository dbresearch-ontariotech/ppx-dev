build:
	docker build -f docker/Dockerfile -t ppx .

run:
	docker run -p 3000:3000 -v $(PWD)/output:/data ppx
