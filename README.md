# MyTBackendService
Backend service componenet of MyT application. Used to manager users cloud services credentials and deploy IoT platforms.

Currently supports
- AWS
- GCP
- Openstack

## How to use
### Build with docker

```bash
docker pull dmacklin/mytbackend
```

```bash
docker build mytbackend
```

Runs on Port 5000. Base Url:
```
http://<ip_address>:5000/v1
```
