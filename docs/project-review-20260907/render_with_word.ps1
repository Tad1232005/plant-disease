$ErrorActionPreference = 'Stop'
$packRoot = [IO.Path]::GetFullPath('C:/Project/plant-disease/docs/project-review-20260907')
$inputs = Get-ChildItem -LiteralPath "$packRoot/word" -Filter '*.docx'
$wordApp = $null
try {
    $wordApp = New-Object -ComObject Word.Application
    $wordApp.Visible = $false
    $wordApp.DisplayAlerts = 0
    $wordApp.AutomationSecurity = 3
    foreach ($file in $inputs) {
        $doc = $null
        $qaDir = Join-Path "$packRoot/qa" $file.BaseName
        New-Item -ItemType Directory -Path $qaDir -Force | Out-Null
        try {
            $doc = $wordApp.Documents.Open($file.FullName, $false, $true, $false)
            $doc.Repaginate()
            $pdfPath = Join-Path $qaDir ($file.BaseName + '.pdf')
            $doc.ExportAsFixedFormat($pdfPath, 17)
            Write-Output $pdfPath
        } finally {
            if ($null -ne $doc) { $doc.Close(0); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($doc) }
        }
    }
} finally {
    if ($null -ne $wordApp) { $wordApp.Quit(0); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($wordApp) }
}
