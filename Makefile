all: build

build:
	@docker build --tag=ghcr.io/mountaintopsolutions/apt-cacher-ng .
