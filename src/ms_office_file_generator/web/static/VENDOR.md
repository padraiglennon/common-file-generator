# Vendored static assets

- `htmx.min.js` - HTMX **2.0.3**, fetched from
  <https://unpkg.com/htmx.org@2.0.3/dist/htmx.min.js>.

It is vendored (not loaded from a CDN) so the UI works offline. To update, fetch
the new minified file from unpkg, replace `htmx.min.js`, and bump the version
here. The file is excluded from the trailing-whitespace / end-of-file pre-commit
hooks so it stays byte-identical to upstream.
