# Deploying Palanaeum to k3s (x86_64)

These manifests deploy Palanaeum onto a single-node **k3s** VM (`linux/amd64`) behind a TLS-terminating reverse proxy such as Cloudflare.

## Stack Overview

- **`web` Deployment:** Gunicorn (`palanaeum.wsgi:application`) + Nginx sidecar (serves `/collected-statics/`, `/media/` with HTTP `206` byte-range support for audio seeking, and handles 500 MB uploads), with `initContainers` that sync static files and run `manage.py migrate` on every rollout.
- **`celery-worker` & `celery-beat` Deployments:** Background audio transcoding, snippet extraction/muting, ZIP backups, and periodic cloud uploads.
- **`postgres` StatefulSet + `redis` Deployment:** Internal `ClusterIP` services only (not exposed on `NodePort`).
- **`db-backup` CronJob:** Daily (`15:00` UTC) PostgreSQL dump (`pg_dump | gzip`) to `backups-pvc` (`/backups/db/backup-YYYY-MM-DD.sql.gz`), Backblaze B2 sync (`--keep-days 90 --replace-newer`), and local pruning (`> 10` days).
- **PVCs (`local-path`):** Persistent volumes for Postgres data (`6Gi`), uploaded/transcoded media (`40Gi`), and backups (`10Gi`).
- **Ingress (`traefik`):** Routes your configured hostname to the `web` service.

---

## 1. Build and Push the Image to GHCR

GitHub Container Registry (`ghcr.io`) pairs directly with `17thshard/palanaeum`.

1. Authenticate Docker with a GitHub **Personal Access Token (classic)** (`ghp_...`) with the `write:packages` scope (which also enables `read:packages`; fine-grained `github_pat_...` tokens are not supported by GHCR):
   ```bash
   echo "$GITHUB_TOKEN" | docker login ghcr.io -u <your-github-username> --password-stdin
   ```

2. Build and push the `linux/amd64` image (passing the current commit SHA as `PALA_VERSION_TAG` keeps `?v=...` static cache-busting tags identical across Gunicorn workers):
   ```bash
   SHA=$(git rev-parse --short HEAD)
   docker build --platform linux/amd64 \
     --build-arg PALA_VERSION_TAG="$SHA" \
     -t ghcr.io/17thshard/palanaeum:latest \
     -t "ghcr.io/17thshard/palanaeum:$SHA" \
     .
   docker push ghcr.io/17thshard/palanaeum:latest
   docker push "ghcr.io/17thshard/palanaeum:$SHA"
   ```

3. On your first push, open the package page on GitHub (`https://github.com/orgs/17thshard/packages` -> `palanaeum` -> **Package settings**) and either:
   - set visibility to **Public** so k3s can pull without credentials, **or**
   - create a `docker-registry` pull secret in the `palanaeum` namespace (`imagePullSecrets`) if keeping the package private.

---

## 2. Prepare the k3s VM

1. Install k3s (includes Traefik ingress and `local-path` storage out of the box):
   ```bash
   curl -sfL https://get.k3s.io | sh -
   ```
2. Open TCP ports `80` and `443` (plus SSH) in your host/cloud firewall; keep `30000-32767` closed and restrict `6443` if managing remotely.
3. Point your DNS record (`A` / `AAAA`) to the VM (proxied through Cloudflare if using Cloudflare).

---

## 3. Configure & Apply Manifests

1. Update the domain placeholders in:
   - `deploy/k3s/configmap.yaml`: `PALA_ALLOWED_HOSTS` and `PALA_CSRF_TRUSTED_ORIGINS`
   - `deploy/k3s/ingress.yaml`: `spec.rules[0].host`

2. Create your gitignored Secret from the template and fill in strong random values:
   ```bash
   cp deploy/k3s/secret.example.yaml deploy/k3s/secret.yaml
   # Edit deploy/k3s/secret.yaml (set PALA_SECRET_KEY, POSTGRES_PASSWORD, and B2_APPLICATION_KEY_ID / B2_APPLICATION_KEY)
   ```

3. Apply namespace, secret, and Kustomize bundle:
   ```bash
   kubectl apply -f deploy/k3s/namespace.yaml
   kubectl apply -f deploy/k3s/secret.yaml
   kubectl apply -k deploy/k3s
   ```

4. Watch pods come up:
   ```bash
   kubectl -n palanaeum get pods -w
   ```

---

## 4. First-Time App Bootstrap

Create an admin superuser and update Django's `Site` domain (used in feeds, sitemaps, and password-reset emails):

```bash
kubectl -n palanaeum exec -it deploy/web -c web -- python3 manage.py createsuperuser
kubectl -n palanaeum exec -it deploy/web -c web -- python3 manage.py shell -c \
  "from django.contrib.sites.models import Site; Site.objects.filter(id=1).update(domain='palanaeum.example.com', name='Palanaeum')"
```

---

## Cloudflare / Reverse Proxy Notes

- **SSL/TLS mode:** Using Cloudflare **Full** (Traefik serves a default cert on `:443`) ensures Traefik sees an HTTPS connection and preserves `X-Forwarded-Proto: https` cleanly. If using **Flexible** (proxy hits VM `:80` over HTTP), Traefik strips untrusted `X-Forwarded-Proto` headers by default, so make sure `PALA_CSRF_TRUSTED_ORIGINS` includes `https://<your-domain>` so form/admin logins pass CSRF checks.
- **Large audio uploads:** Fine Uploader chunks audio uploads by default, which works within Cloudflare's 100 MB per-request limit while Nginx allows up to `500m`.
- **Secure cookies:** Once HTTPS is verified, set `PALA_SECURE_COOKIES: "True"` in `deploy/k3s/configmap.yaml` and re-apply.

---

## Updating & Backups

- **Deploy a newly pushed `:latest` image:**
  ```bash
  kubectl -n palanaeum rollout restart deployment/web deployment/celery-worker deployment/celery-beat
  ```
- **Automated daily PostgreSQL backups (`db-backup` CronJob):**
  Runs daily at `15:00` UTC in three sequential steps inside one Pod:
  1. `pg-dump`: dumps PostgreSQL to `backups-pvc` at `/backups/db/backup-YYYY-MM-DD.sql.gz` (atomic write + `gzip -t` integrity check).
  2. `b2-sync`: syncs `/backups/db/` to `PALA_BACKUP_B2_DEST` (`b2://Arcanum/backups/`) with `--keep-days 90 --replace-newer`.
  3. `prune-local`: deletes local SQL dumps older than `PALA_BACKUP_LOCAL_RETENTION_DAYS` (`10`) days — only after both `pg-dump` and `b2-sync` succeed.

  Trigger a manual test run and inspect logs for all three stages:
  ```bash
  kubectl -n palanaeum create job --from=cronjob/db-backup db-backup-manual
  kubectl -n palanaeum wait --for=condition=complete job/db-backup-manual --timeout=10m
  kubectl -n palanaeum logs job/db-backup-manual --all-containers=true
  ```
- **Create a Django ZIP backup archive in `/app/backups` (`backups-pvc`):**
  ```bash
  kubectl -n palanaeum exec deploy/web -c web -- python3 manage.py backup
  ```
