VERSION=$(poetry version -s)

echo "Building image with version: ${VERSION}"

docker build -t lqbot:${VERSION} .

VERSION=$VERSION docker compose up -d
