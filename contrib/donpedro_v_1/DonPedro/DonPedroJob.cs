﻿using System;
using System.Diagnostics;
using System.IO;
using System.Net;
using DonPedro;
using DonPedro.Detectors;
using DonPedro.Utils;

namespace DonPedro
{
	public class DonPedroJob
	{
		private string RalphURL;
		private string ReportURL;
		private int MaxTries;
		private int SecondsInterval;
		private string ApiUser;
		private string ApiKey;
		
		private Rest apiClient;
		
		public DonPedroJob()
		{
			RalphURL = Properties.app.Default.ralph_url;
			ReportURL = RalphURL + Properties.app.Default.api_path;
			MaxTries = Properties.app.Default.max_tries;
			SecondsInterval = Properties.app.Default.tries_interval;
			ApiUser = Properties.app.Default.api_user;
			ApiKey = Properties.app.Default.api_key;
			
			ServicePointManager.ServerCertificateValidationCallback += delegate { return true; };
			
			apiClient = new Rest();
		}
		
		public void NotifyRalph(object stateObject)
		{
			Detector d = new Detector();
			string jsonData = d.GetAllComponentsJSON();

			Logger.Instance.LogInformation("Sending to: " + ReportURL + " Data: " + jsonData);

			int tries = 0;
			while (tries < MaxTries)
			{
				tries++;
				try
				{
					apiClient.Post(ReportURL + "/?username=" + ApiUser + "&api_key=" + ApiKey, jsonData);
				}
				catch (System.Net.WebException e)
				{
					string serverMessage = "";
					if (e.Response != null)
					{
						StreamReader s = new StreamReader(e.Response.GetResponseStream());
						serverMessage = s.ReadToEnd();
					}
					Logger.Instance.LogError(
						String.Format(
							"Error while sending data to {0}: {1}. Full response: \"{2}\". Waiting for {3} try.",
							RalphURL, 
							e.Message,
							serverMessage, 
							tries + 1
						)
					);
					System.Threading.Thread.Sleep(SecondsInterval * 1000);
				}
				catch (Exception e)
				{
					Logger.Instance.LogError(e.ToString());
				}
			}
		}
	}
}
