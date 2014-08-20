using System;

namespace DonPedroOutput
{
	public class HelpPrinter
	{		
		public static void Print()
		{
			Console.WriteLine("DonPedroOutput - help\n\n");
			Console.WriteLine("Possible options:");
			Console.WriteLine("\t--help\t\tshow this informations");
			Console.WriteLine("\t--json\t\tprint data in JSON format");
			Console.WriteLine("\t--file=FILE\twrite data to specific file");
		}
	}
}
