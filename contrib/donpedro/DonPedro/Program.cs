using System;
using DonPedro.Detectors;

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
			throw new Exception("wyjatek");
		}
	}
}