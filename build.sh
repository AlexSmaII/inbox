set -eu

cleanup() {
    docker rm -f "pod" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

docker build -t pod:test .

docker run --rm --name pod -p 8080:8080 pod:test