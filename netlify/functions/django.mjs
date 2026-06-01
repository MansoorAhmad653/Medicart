export default async (req) => {
  const djangoUrl = Netlify.env.get('DJANGO_BACKEND_URL')

  if (!djangoUrl) {
    return new Response(
      `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dicart – Setup Required</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 600px; margin: 80px auto; padding: 0 20px; color: #333; }
    h1 { color: #e53e3e; }
    code { background: #f5f5f5; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }
    .box { background: #fff8f0; border-left: 4px solid #ed8936; padding: 16px 20px; border-radius: 4px; margin: 20px 0; }
  </style>
</head>
<body>
  <h1>Backend Not Configured</h1>
  <p>The Dicart Django backend is not connected yet.</p>
  <div class="box">
    <strong>To complete setup:</strong>
    <ol>
      <li>Deploy the Django app to Railway or Render.</li>
      <li>Copy the deployed URL (e.g. <code>https://medicart-production.up.railway.app</code>).</li>
      <li>In Netlify → Site settings → Environment variables, add:<br>
        <code>DJANGO_BACKEND_URL = https://your-django-app-url</code>
      </li>
      <li>Trigger a new Netlify deploy.</li>
    </ol>
  </div>
</body>
</html>`,
      {
        status: 503,
        headers: { 'Content-Type': 'text/html; charset=utf-8' },
      }
    )
  }

  const base = djangoUrl.replace(/\/$/, '')
  const url = new URL(req.url)
  const target = base + url.pathname + url.search

  const proxyHeaders = new Headers(req.headers)
  proxyHeaders.set('X-Forwarded-Host', url.hostname)
  proxyHeaders.set('X-Forwarded-Proto', 'https')
  // Remove host header so the upstream server uses its own
  proxyHeaders.delete('host')

  const hasBody = !['GET', 'HEAD'].includes(req.method)

  const upstream = await fetch(target, {
    method: req.method,
    headers: proxyHeaders,
    body: hasBody ? req.body : undefined,
    redirect: 'manual',
  })

  // Rewrite redirect locations so the browser stays on the Netlify domain
  if ([301, 302, 303, 307, 308].includes(upstream.status)) {
    const location = upstream.headers.get('location')
    if (location && location.startsWith(base)) {
      const rewritten = new Headers(upstream.headers)
      rewritten.set('location', location.replace(base, url.origin))
      return new Response(upstream.body, {
        status: upstream.status,
        headers: rewritten,
      })
    }
  }

  return upstream
}
