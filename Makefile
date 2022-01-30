version := $(shell git describe --tags)
build :
	docker buildx build \
	-f "Dockerfile" \
	--platform linux/arm/v7,linux/amd64,linux/arm64 \
	-t abathargh/telegram-update-notifier:$(version) \
	-t abathargh/telegram-update-notifier:latest \
	--push .

.PHONY : build