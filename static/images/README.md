# Photo assets

GymTrack uses a handful of real photos to make the UI feel less bare. They're
**not committed as binaries by the agent** because this sandbox's shell can't
reach external image CDNs (corporate network allowlist) -- but your own
machine can, so grab them with the one-liner below.

All photos are from **Pexels**, covered by the
[Pexels License](https://www.pexels.com/license/): free for personal and
commercial use, **no attribution required**. Verified working direct URLs as
of the time this was put together.

## One-time download (run from the GymTrack repo root)

**PowerShell (Windows):**
```powershell
$dir = "static/images"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$photos = @{
    "gym-hero.jpg"        = "https://images.pexels.com/photos/1552242/pexels-photo-1552242.jpeg?auto=compress&cs=tinysrgb&w=1600"
    "dashboard-banner.jpg"= "https://images.pexels.com/photos/841130/pexels-photo-841130.jpeg?auto=compress&cs=tinysrgb&w=1600"
    "empty-programs.jpg"  = "https://images.pexels.com/photos/2294361/pexels-photo-2294361.jpeg?auto=compress&cs=tinysrgb&w=1600"
    "empty-history.jpg"   = "https://images.pexels.com/photos/3768916/pexels-photo-3768916.jpeg?auto=compress&cs=tinysrgb&w=1600"
    "guided-session.jpg"  = "https://images.pexels.com/photos/416778/pexels-photo-416778.jpeg?auto=compress&cs=tinysrgb&w=1600"
    "finish-line.jpg"     = "https://images.pexels.com/photos/3253501/pexels-photo-3253501.jpeg?auto=compress&cs=tinysrgb&w=1600"
}
foreach ($name in $photos.Keys) {
    Invoke-WebRequest -Uri $photos[$name] -OutFile "$dir/$name"
}
```

**bash/macOS/Linux:**
```bash
mkdir -p static/images
curl -sL "https://images.pexels.com/photos/1552242/pexels-photo-1552242.jpeg?auto=compress&cs=tinysrgb&w=1600" -o static/images/gym-hero.jpg
curl -sL "https://images.pexels.com/photos/841130/pexels-photo-841130.jpeg?auto=compress&cs=tinysrgb&w=1600" -o static/images/dashboard-banner.jpg
curl -sL "https://images.pexels.com/photos/2294361/pexels-photo-2294361.jpeg?auto=compress&cs=tinysrgb&w=1600" -o static/images/empty-programs.jpg
curl -sL "https://images.pexels.com/photos/3768916/pexels-photo-3768916.jpeg?auto=compress&cs=tinysrgb&w=1600" -o static/images/empty-history.jpg
curl -sL "https://images.pexels.com/photos/416778/pexels-photo-416778.jpeg?auto=compress&cs=tinysrgb&w=1600" -o static/images/guided-session.jpg
curl -sL "https://images.pexels.com/photos/3253501/pexels-photo-3253501.jpeg?auto=compress&cs=tinysrgb&w=1600" -o static/images/finish-line.jpg
```

Once the files land in `static/images/`, refresh the app -- no code changes
needed, the templates already reference these exact filenames via a
graceful-fallback macro (`templates/_photo.html`), so the app looked fine
before you ran this and will look better after.

## Where each photo shows up

| File | Used on |
|---|---|
| `gym-hero.jpg` | Login & Register page header strip |
| `dashboard-banner.jpg` | Dashboard "Ready to train?" hero panel |
| `empty-programs.jpg` | Programs page empty state ("No programs yet") |
| `empty-history.jpg` | History page empty state ("No sessions logged yet") |
| `guided-session.jpg` | Ambient background during a live Guided Session |
| `finish-line.jpg` | "Finish line!" card at the end of every session story |

## Swapping in your own photos later

Just overwrite any file in this folder with a same-named image (any aspect
ratio works reasonably well, `bg-cover` handles cropping) -- no template
changes required. Want a 7th spot decorated? Add a new `{{ photo.layer(...) }}`
call using the macro in `templates/_photo.html` and drop the matching file
here.
