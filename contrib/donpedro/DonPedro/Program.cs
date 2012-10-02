using System;
using System.Diagnostics;
using System.IO;

using DonPedro;
using DonPedro.Detectors;
using DonPedro.Utils;

namespace DonPedro
{
	class Program
	{
		static string json_data  = "";
		static string ralph_url = Properties.app.Default.ralph_url;
		static string report_url = ralph_url + Properties.app.Default.api_path;
		static int max_tries = Properties.app.Default.max_tries;
		static int seconds_interval = Properties.app.Default.tries_interval;
		static string api_user = Properties.app.Default.api_user;
		static string api_key = Properties.app.Default.api_key;
		
		static void CurrentDomain_UnhandledException(object sender, UnhandledExceptionEventArgs e)
		{
			new Logger().LogFatal(e.ExceptionObject.ToString());
		}
		
		private static void setup()
		{
			AppDomain.CurrentDomain.UnhandledException += new UnhandledExceptionEventHandler(CurrentDomain_UnhandledException);
		}
		
		public static void Main(string[] args)
		{
			int tries = 0;
			string json_data = "";
			setup();
			new Logger().LogDebug("Detecting config");
			Detector d = new Detector();
			json_data = d.GetAllComponentsJSON();
			new Logger().LogDebug("Sending to: " + report_url);
			while (tries < max_tries)
			{
				tries ++;
				try
				{
					new Rest().Post(report_url+"/?username="+api_user+"&api_key="+api_key, json_data);
				}
				catch(System.Net.WebException e)
				{
					StreamReader s = new StreamReader(e.Response.GetResponseStream());
					string server_message = s.ReadToEnd();
					string error_message = e.Message;
					new Logger().LogError(String.Format("Error while sending data to {0}: {1}. Full response:{2} Waiting for {3} try.",
					                                    ralph_url,	error_message,server_message, tries+1));
					System.Threading.Thread.Sleep(seconds_interval*1000);
				}
			}
			Console.ReadKey();
		}
	}
}