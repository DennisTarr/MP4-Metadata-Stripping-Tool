using System;
using System.IO;
using System.Diagnostics;
using System.Linq;
using System.Collections.Generic;

class Program
{
    static int RunProcessWithStdin(string exe, string args, string stdinData)
    {
        var psi = new ProcessStartInfo();
        psi.FileName = exe;
        psi.Arguments = args;
        psi.RedirectStandardInput = true;
        psi.RedirectStandardOutput = true;
        psi.RedirectStandardError = true;
        psi.UseShellExecute = false;
        psi.CreateNoWindow = true;

        var p = Process.Start(psi);
        if (p == null) return -1;
        
        p.StandardInput.Write(stdinData + "\n");
        p.StandardInput.Close();
        
        p.OutputDataReceived += (s, e) => { };
        p.ErrorDataReceived += (s, e) => { };
        
        p.BeginOutputReadLine();
        p.BeginErrorReadLine();
        p.WaitForExit();
        
        return p.ExitCode;
    }

    static bool Try7z(string exe, string fullPath, string pass)
    {
        string args = "t \"" + fullPath + "\"";
        int exitCode = RunProcessWithStdin(exe, args, pass);
        return exitCode == 0;
    }

    static bool TryUnrar(string exe, string fullPath, string pass)
    {
        string args = "t \"" + fullPath + "\"";
        int exitCode = RunProcessWithStdin(exe, args, pass);
        return exitCode == 0;
    }

    static bool TryRar(string exe, string fullPath, string pass)
    {
        string args = "t \"" + fullPath + "\" -y";
        int exitCode = RunProcessWithStdin(exe, args, pass);
        return exitCode == 0 || exitCode == 1;
    }

    static string Find7z()
    {
        foreach (string p in new string[] {
            @"C:\Program Files (x86)\7-Zip\7z.exe",
            @"C:\Program Files\7-Zip\7z.exe"
        })
            if (File.Exists(p)) return p;
        return null;
    }

    static void PrintColor(string text, ConsoleColor color)
    {
        var old = Console.ForegroundColor;
        Console.ForegroundColor = color;
        Console.WriteLine(text);
        Console.ForegroundColor = old;
    }

    static void PrintGreen(string text) => PrintColor(text, ConsoleColor.Green);
    static void PrintYellow(string text) => PrintColor(text, ConsoleColor.Yellow);
    static void PrintCyan(string text) => PrintColor(text, ConsoleColor.Cyan);
    static void PrintWhite(string text) => PrintColor(text, ConsoleColor.White);

    static void Main()
    {
        PrintCyan("=== Password Cracker ===");

        // Load passwords from all *.txt files in current directory
        var passwordFiles = Directory.GetFiles(".", "*.txt").ToList();
        
        if (passwordFiles.Count == 0)
        {
            PrintColor("ERROR: No password files (*.txt) found in current directory", ConsoleColor.Red);
            return;
        }

        var allLines = new List<string>();
        foreach (string pwFile in passwordFiles)
        {
            PrintCyan("Loading passwords from: " + pwFile);
            allLines.AddRange(File.ReadAllLines(pwFile));
        }

        var passwords = allLines
            .Where(l => l != null && !string.IsNullOrEmpty(l))
            .Select(l => l.Replace("\r", "").Replace("\uFEFF", "").Trim())
            .Where(l => !string.IsNullOrEmpty(l))
            .ToArray();

        Console.WriteLine();
        PrintCyan("Loaded " + passwords.Length + " passwords");
        for (int i = 0; i < Math.Min(5, passwords.Length); i++)
            Console.WriteLine("  [" + i + "] " + passwords[i]);

        // Find archives
        var archives = new List<string>();
        if (Directory.Exists("arc"))
        {
            foreach (string f in Directory.GetFiles("arc"))
            {
                string ext = Path.GetExtension(f).ToLower();
                if (".7z .zip .rar .gz .tar .bz .xz .iso".Split(' ').Contains(ext))
                    archives.Add(f);
            }
        }
        foreach (string ext in new string[] { "*.7z", "*.zip", "*.rar", "*.gz", "*.tar", "*.bz", "*.xz", "*.iso" })
        {
            foreach (string f in Directory.GetFiles(".", ext))
            {
                if (!archives.Contains(f))
                    archives.Add(f);
            }
        }

        Console.WriteLine();
        PrintCyan("Found " + archives.Count + " archive(s):");
        foreach (string a in archives)
            Console.WriteLine("  " + a);

        // Find tools
        string unrarPath = @"C:\Program Files\WinRAR\unrar.exe";
        string rarPath = @"C:\Program Files\WinRAR\rar.exe";
        string sevenZPath = Find7z();

        Console.WriteLine();
        PrintYellow("Tools:");
        Console.WriteLine("  7z: " + (sevenZPath ?? "NOT FOUND"));
        Console.WriteLine("  unrar: " + (File.Exists(unrarPath) ? "YES" : "NO"));
        Console.WriteLine("  rar: " + (File.Exists(rarPath) ? "YES" : "NO"));
        Console.WriteLine();

        // Process archives
        foreach (string archive in archives)
        {
            string ext = Path.GetExtension(archive).ToLower();

            if (ext == ".7z" || ext == ".zip")
            {
                if (sevenZPath != null)
                {
                    PrintYellow("Testing: " + archive + " (7z)");
                    foreach (string pwd in passwords)
                    {
                        if (Try7z(sevenZPath, Path.GetFullPath(archive), pwd))
                        {
                            PrintGreen("  [+] Password found: " + pwd);
                            goto next_archive;
                        }
                    }
                    PrintWhite("  [-] No password found");
                }
            }
            else if (ext == ".rar")
            {
                bool found = false;
                
                if (File.Exists(unrarPath))
                {
                    PrintYellow("Testing: " + archive + " (unrar)");
                    foreach (string pwd in passwords)
                    {
                        if (TryUnrar(unrarPath, Path.GetFullPath(archive), pwd))
                        {
                            PrintGreen("  [+] Password found: " + pwd);
                            found = true;
                            break;
                        }
                    }
                    if (found) goto next_archive;
                }
                
                if (File.Exists(rarPath))
                {
                    PrintYellow("Testing: " + archive + " (rar)");
                    foreach (string pwd in passwords)
                    {
                        if (TryRar(rarPath, Path.GetFullPath(archive), pwd))
                        {
                            PrintGreen("  [+] Password found: " + pwd);
                            found = true;
                            break;
                        }
                    }
                }
                
                if (!found)
                    PrintWhite("  [-] No password found");
            }
            
            next_archive:
            Console.WriteLine();
        }
    }
}
