$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$output = Join-Path $root "AI1SAD_Registry.exe"

$source = @'
using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Windows.Forms;

public static class AI1SADRegistryLauncher
{
    [STAThread]
    public static int Main(string[] args)
    {
        string exePath = Process.GetCurrentProcess().MainModule.FileName;
        string directory = Path.GetDirectoryName(exePath) ?? Environment.CurrentDirectory;
        string python = File.Exists(@"F:\Python310\python.exe") ? @"F:\Python310\python.exe" : "python";
        string arguments = "-m app.services.incident_registry_viewer " + String.Join(" ", args.Select(Quote));

        try
        {
            ProcessStartInfo startInfo = new ProcessStartInfo(python, arguments)
            {
                WorkingDirectory = directory,
                UseShellExecute = false,
                CreateNoWindow = true,
                RedirectStandardError = true
            };
            using (Process process = Process.Start(startInfo))
            {
                string error = process.StandardError.ReadToEnd();
                process.WaitForExit();
                if (process.ExitCode != 0)
                {
                    MessageBox.Show(error, "AI1SAD Registry", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
                return process.ExitCode;
            }
        }
        catch (Exception exc)
        {
            MessageBox.Show(exc.Message, "AI1SAD Registry", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 2;
        }
    }

    private static string Quote(string value)
    {
        return "\"" + value.Replace("\"", "\\\"") + "\"";
    }
}
'@

Add-Type -TypeDefinition $source -Language CSharp -ReferencedAssemblies System.Windows.Forms -OutputAssembly $output -OutputType WindowsApplication
Write-Host "Created $output"
