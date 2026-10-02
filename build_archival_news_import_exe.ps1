$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$output = Join-Path $root "run_archival_news_import.exe"

$source = @'
using System;
using System.Diagnostics;
using System.IO;
using System.Text;

public static class ArchivalNewsImportLauncher
{
    public static int Main(string[] args)
    {
        string exePath = Process.GetCurrentProcess().MainModule.FileName;
        string directory = Path.GetDirectoryName(exePath) ?? Environment.CurrentDirectory;
        string batchPath = Path.Combine(directory, "run_archival_news_import.bat");

        if (!File.Exists(batchPath))
        {
            Console.Error.WriteLine("Could not find launcher batch file:");
            Console.Error.WriteLine("  " + batchPath);
            return 2;
        }

        string commandArgs = "/c \"\"" + batchPath.Replace("\"", "") + "\"";
        foreach (string arg in args)
        {
            commandArgs += " " + QuoteForCmd(arg);
        }
        commandArgs += "\"";

        ProcessStartInfo startInfo = new ProcessStartInfo("cmd.exe", commandArgs)
        {
            WorkingDirectory = directory,
            UseShellExecute = false
        };

        using (Process process = Process.Start(startInfo))
        {
            process.WaitForExit();
            return process.ExitCode;
        }
    }

    private static string QuoteForCmd(string value)
    {
        if (String.IsNullOrEmpty(value))
        {
            return "\"\"";
        }

        StringBuilder builder = new StringBuilder();
        builder.Append('"');
        foreach (char current in value)
        {
            if (current == '"')
            {
                builder.Append('\\');
            }
            builder.Append(current);
        }
        builder.Append('"');
        return builder.ToString();
    }
}
'@

Add-Type -TypeDefinition $source -Language CSharp -OutputAssembly $output -OutputType ConsoleApplication
Write-Host "Created $output"
