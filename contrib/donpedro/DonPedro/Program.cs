using System;
using System.Diagnostics;
using System.IO;
using System.Net;

using DonPedro;
using DonPedro.Detectors;
using DonPedro.Utils;

namespace DonPedro
{
	class Program
	{
		static string JSONData  = "";
		static string RalphURL = Properties.app.Default.ralph_url;
		static string ReportURL = RalphURL + Properties.app.Default.api_path;
		static int MaxTries = Properties.app.Default.max_tries;
		static int SecondsInterval = Properties.app.Default.tries_interval;
		static string ApiUser = Properties.app.Default.api_user;
		static string ApiKey = Properties.app.Default.api_key;
		
		static void CurrentDomain_UnhandledException(object sender, UnhandledExceptionEventArgs e)
		{
			new Logger().LogFatal(e.ExceptionObject.ToString());
		}
		
		private static void setup()
		{
			AppDomain.CurrentDomain.UnhandledException += new UnhandledExceptionEventHandler(CurrentDomain_UnhandledException);
			ServicePointManager.ServerCertificateValidationCallback += delegate { return true; };
		}
		
		public static void Main(string[] args)
		{
			int tries = 0;
			string jsonData = "";
			string errorMessage = "";
			string serverMessage = "";
			setup();
			new Logger().LogDebug("Detecting config");
			Detectors.Detector d = new Detector();
			jsonData = d.getAllComponentsJSON();
			new Logger().LogDebug(jsonData);
			new Logger().LogDebug("Sending to: " + ReportURL);
			while (tries < MaxTries)
			{
				tries ++;
				try
				{
					new Rest().Post(ReportURL+"/?username="+ApiUser+"&api_key="+ApiKey, jsonData);
				}
				catch(System.Net.WebException e)
				{
	
					if (e.Response != null)
					{
						StreamReader s = new StreamReader(e.Response.GetResponseStream());
						serverMessage = s.ReadToEnd();
						errorMessage = e.Message;
					}
					new Logger().LogError(String.Format("Error while sending data to {0}: {1}. Full response:{2} Waiting for {3} try.",
					                                    RalphURL,	errorMessage,serverMessage, tries+1));
					System.Threading.Thread.Sleep(SecondsInterval*1000);
				}
			}
		}
	}
}