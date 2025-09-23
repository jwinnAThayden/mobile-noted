# PowerShell Profile Function for Easy Mobile Noted Deployment
# Add this to your PowerShell profile for quick deployments

function Push-MobileNoted {
    param(
        [string]$Message = "Update mobile noted app"
    )
    
    $scriptPath = "c:\Users\jwinn\OneDrive - Hayden Beverage\Documents\py\noted\deploy.ps1"
    
    if (Test-Path $scriptPath) {
        & $scriptPath -CommitMessage $Message
    } else {
        Write-Host "❌ Deploy script not found at $scriptPath" -ForegroundColor Red
    }
}

# Aliases for convenience
Set-Alias deploy Push-MobileNoted
Set-Alias push-noted Push-MobileNoted

# Export functions if this is loaded as a module
Export-ModuleMember -Function Push-MobileNoted -Alias deploy, push-noted