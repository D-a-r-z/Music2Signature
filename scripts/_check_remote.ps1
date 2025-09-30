$r = Get-Random
$uri = "https://music2-signature.vercel.app/api/now-playing-svg?theme=bars&height=90&refresh=$r"
Write-Output "GET -> $uri"
try {
    $resp = Invoke-WebRequest -Uri $uri -UseBasicParsing -ErrorAction Stop
    $resp.Content | Out-File tmp_remote_bars.svg -Encoding utf8
    Write-Output "Status: $($resp.StatusCode)"
    Write-Output "Saved size: $(Get-Item tmp_remote_bars.svg).Length"
    Write-Output "Headers:"
    $resp.Headers
} catch {
    Write-Output "ERROR: $($_.Exception.Message)"
    if ($_.Exception.Response) {
        $s = $_.Exception.Response.GetResponseStream()
        $sr = New-Object System.IO.StreamReader($s)
        $body = $sr.ReadToEnd()
        $body | Out-File tmp_remote_bars.svg -Encoding utf8
        Write-Output "Saved error body size: $(Get-Item tmp_remote_bars.svg).Length"
    }
}
Write-Output "First 80 lines:"
if (Test-Path tmp_remote_bars.svg) {
    Get-Content tmp_remote_bars.svg -TotalCount 80
} else {
    Write-Output "No file saved."
}
