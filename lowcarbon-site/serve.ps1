# Simple local HTTP server for testing lowcarbon.co.za redesign
# Run this script, then open http://localhost:8080

$port = 8081
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Serving lowcarbon.co.za at http://localhost:$port" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow

$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://localhost:$port/")
$listener.Start()

while ($listener.IsListening) {
    $context = $listener.GetContext()
    $request = $context.Request
    $response = $context.Response

    $path = $request.Url.AbsolutePath
    if ($path -eq '/' -or $path -eq '') { $path = '/index.html' }

    $fullPath = [System.IO.Path]::Combine($root, $path.TrimStart('/'))
    $fullPath = [System.IO.Path]::GetFullPath($fullPath)

    if ((Test-Path $fullPath) -and $fullPath.StartsWith($root)) {
        $ext = [System.IO.Path]::GetExtension($fullPath).ToLower()
        $mimeMap = @{
            '.html' = 'text/html'
            '.css' = 'text/css'
            '.js' = 'application/javascript'
            '.svg' = 'image/svg+xml'
            '.png' = 'image/png'
            '.jpg' = 'image/jpeg'
            '.json' = 'application/json'
            '.xml' = 'application/xml'
            '.txt' = 'text/plain'
            '.ico' = 'image/x-icon'
        }
        $contentType = if ($mimeMap.ContainsKey($ext)) { $mimeMap[$ext] } else { 'application/octet-stream' }
        $response.ContentType = $contentType
        $buffer = [System.IO.File]::ReadAllBytes($fullPath)
        $response.ContentLength64 = $buffer.Length
        $response.OutputStream.Write($buffer, 0, $buffer.Length)
        Write-Host "200 $path" -ForegroundColor Green
    } else {
        $response.StatusCode = 404
        $notFound = [System.IO.File]::ReadAllBytes([System.IO.Path]::Combine($root, '404.html'))
        $response.ContentType = 'text/html'
        $response.OutputStream.Write($notFound, 0, $notFound.Length)
        Write-Host "404 $path" -ForegroundColor Red
    }

    $response.Close()
}

$listener.Stop()
