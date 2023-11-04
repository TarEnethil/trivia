TARGET=trivia
TAG=latest

all:
	sudo docker build . --tag ${TARGET}:${TAG}
