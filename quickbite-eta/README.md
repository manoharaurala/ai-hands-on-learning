# QuickBite ETA

QuickBite ETA is a containerized FastAPI service that predicts food delivery
time from delivery distance, preparation time, rider availability, and rain.
The Docker image trains the sample model during the image build.

Run these commands from the `quickbite-eta` directory.

## Build and run

```bash
docker build -t quickbite-eta:v1 .

docker images

docker run -d -p 8000:8000 --name eta-service quickbite-eta:v1
```

## Test the prediction endpoint

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"distance_km": 4.5, "prep_time_min": 15, "rider_available": 1, "is_raining": 1}'
```

Open the interactive API documentation at:

```text
http://localhost:8000/docs
```

## Inspect the container

```bash
docker ps
docker ps -a
docker logs -f eta-service
docker exec -it eta-service bash
```

## Stop and remove the container

```bash
docker stop eta-service
docker rm eta-service
```

## Rebuild after code changes

```bash
docker build -t quickbite-eta:v1 .
docker rm -f eta-service
docker run -d -p 8000:8000 --name eta-service quickbite-eta:v1
```
