using System;
using DonPedro;

namespace DonPedro
{
	class Program
	{
		static void CurrentDomain_UnhandledException(object sender, UnhandledExceptionEventArgs e)
		{
			new Logger().LogFatal(e.ExceptionObject.ToString());
		}
		
		public static void Main(string[] args)
		{
			AppDomain.CurrentDomain.UnhandledException += new UnhandledExceptionEventHandler(CurrentDomain_UnhandledException);
			
		}
	}
}