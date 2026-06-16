
# Easy Lazy Morning — scheduled trigger
# Calls the AgentBase runtime endpoint to start the morning briefing.
# Designed to run via Windows Task Scheduler at 10:15 AM Mon-Fri.

$endpoint = "https://endpoint-e90e7faa-d43e-4d4e-802f-3d6296a7135c.agentbase-runtime.aiplatform.vngcloud.vn/invocations"
$logFile  = "$PSScriptRoot\trigger.log"
$today    = (Get-Date).ToString("yyyy-MM-dd")
$timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")

try {
    Add-Type -AssemblyName System.Net.Http
    $httpClient = New-Object System.Net.Http.HttpClient
    $httpClient.DefaultRequestHeaders.Add("X-GreenNode-AgentBase-User-Id", "morning-briefing")
    $httpClient.DefaultRequestHeaders.Add("X-GreenNode-AgentBase-Session-Id", $today)
    $httpClient.Timeout = [System.TimeSpan]::FromSeconds(300)

    $body    = '{"trigger":"scheduled"}'
    $content = New-Object System.Net.Http.StringContent($body, [System.Text.Encoding]::UTF8, "application/json")
    $result  = $httpClient.PostAsync($endpoint, $content).Result
    $resp    = $result.Content.ReadAsStringAsync().Result
    $status  = [int]$result.StatusCode
    $msg     = "[$timestamp] HTTP $status — OK"
} catch {
    $msg = "[$timestamp] ERROR — $_"
}

Add-Content -Path $logFile -Value $msg
Write-Output $msg
