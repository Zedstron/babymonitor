
Run a published image (recommended for end users)

1. Create a `.env` in the project root containing at minimum:

   SECRET_KEY=your_jwt_secret
   OPENWEATHER_KEY=your_openweather_api_key

2. Pull and run the prebuilt image (replace `yourdocker/babyguard:tag` with the published tag for your platform):

   docker pull yourdocker/babyguard:tag
   docker run -d --name babyguard -p 443:443 -v "$(pwd)/media:/app/media" --env-file .env yourdocker/babyguard:tag

Notes for Raspberry Pi / ARM hosts

- Use an image tag built for your architecture (for example `:armv7` or `:arm64`) or set the platform when running Docker on systems that support multi-arch emulation:

  docker run --platform linux/arm/v7 -d --name babyguard -p 443:443 -v "$(pwd)/media:/app/media" --env-file .env yourdocker/babyguard:armv7

- This repository includes `docker/docker-compose.yml` which by default pulls the registry image. To run with compose from the `docker/` folder, set the `IMAGE` (and optionally `PLATFORM`) env var and run:

  IMAGE=yourdocker/babyguard:tag PLATFORM=linux/arm/v7 docker compose up -d

Developer / Maintainer: building and publishing multi-arch images

- We will publish multi-arch images to a registry so end users don't need to build locally. See `docker/BUILD.md` for the `docker buildx` commands used to produce and push multi-arch manifest tags.

- The container auto-generates a self-signed certificate at `cert/cert.pem`/`cert/key.pem` (non-interactive) if none are present. For production, mount your own certs into `cert/`.

