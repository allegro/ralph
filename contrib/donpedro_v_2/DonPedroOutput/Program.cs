using System;
using System.IO;
using DonPedro.Detectors;
using DonPedro.DTO;

namespace DonPedroOutput
{
	class Program
	{
		public static void Main(string[] args)
		{
			ArgsParser argsParser = new ArgsParser(args);
			
			if (argsParser.IsSet("help"))
			{
				HelpPrinter.Print();
			}
			else
			{
				Detector detector = new Detector();
				TextPrinter printer = new TextPrinter();
				
				if (argsParser.IsSet("file"))
				{
					string fileName = argsParser.GetArgValue("file");

					TextWriter nativeConsoleOutput = Console.Out;
					FileStream fstream;
					StreamWriter writer;
					
					try
					{
						fstream = new FileStream(
							fileName, 
							FileMode.Create, 
							FileAccess.Write
						);
        				writer = new StreamWriter(fstream);
					}
					catch (Exception e)
					{
						Console.WriteLine (String.Format("Cannot open `{0}` for writing.", fileName));
        				Console.WriteLine (e.Message);
        				return;
					}
					Console.SetOut(writer);
					
					printer.Print(detector, argsParser.IsSet("json"));
					
					Console.SetOut(nativeConsoleOutput);
					writer.Close();
					fstream.Close();
				}
				else
				{
					printer.Print(detector, argsParser.IsSet("json"));
				}
			}
		}
	}
}