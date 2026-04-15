.PHONY: install build-layout-tree align-layout-tree serve

install:
	uv sync


build:
	uv run ppx-align build ../output/resnet

serve:
	uv run ppx-align server ../output --slow
