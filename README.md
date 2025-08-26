# template

Juncture website template

## Local Development

Run a local Jekyll server

```bash
jekyll serve --disable-disk-cache -d /tmp
```

or

```bash
docker run --rm -it -p 4000:4000 -p 35729:35729 -v "$PWD":/srv/jekyll -v "$PWD/.bundle":/usr/local/bundle -w /srv/jekyll jekyll/jekyll:4 bash -lc 'bundle install && jekyll serve --livereload --host 0.0.0.0 -d /tmp'
```