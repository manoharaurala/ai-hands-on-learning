# QuickBite ETA

A containerized FastAPI service that predicts food delivery time from delivery distance, preparation time, rider availability, and weather conditions.

## Run with Docker

Run these commands from this directory:

```bash
docker build -t quickbite-eta:v1 .

docker images

docker run -d -p 8000:8000 --name eta-service quickbite-eta:v1

docker ps
```

Test the prediction endpoint:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"distance_km": 4.5, "prep_time_min": 15, "rider_available": 1, "is_raining": 1}'
```

Expected response format:

```json
{
  "eta_minutes": 40.5,
  "message": "Your food arrives in 40.5 minutes"
}
```

Open the interactive API documentation at http://localhost:8000/docs.

## Docker Operations

```bash
docker ps

docker ps -a

docker logs -f eta-service

docker exec -it eta-service bash

docker stop eta-service

docker rm eta-service
```
