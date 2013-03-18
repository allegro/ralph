using System;
using DonPedro.DTO;

namespace DonPedroOutput
{
	public class PropertiesPrinter
	{
		public PropertiesPrinter()
		{
		}
		
		public static void Print(BaseDTOResponse obj)
		{
			foreach(var prop in obj.GetType().GetProperties()) {
				Console.WriteLine("\t{0}: {1}", prop.Name, prop.GetValue(obj, null));
			}
			Console.WriteLine();
		}
	}
}
