using System;
using System.Collections.Generic;
using System.Diagnostics;
using DonPedro.DTO;
using DonPedro.Detectors.Exceptions;
using System.Text.RegularExpressions;
using DonPedro.Utils;

namespace DonPedro.Detectors
{
	public class FCInfoDetectorSource
	{
		public List<FibreChannelDTOResponse> GetFibreChannelInfo()
		{
			List<FibreChannelDTOResponse> fc = new List<FibreChannelDTOResponse>();
			string fcinfoResult;
			
			try
			{
				fcinfoResult = ExecuteFcinfoCommand("details");
			}
			catch (ExternalCommandExecutionException e)
			{
				Logger.Instance.LogWarning(
					"[GetFCInfo] To get informations about FC cards or disk shares install fcinfo tool."
				);
				Logger.Instance.LogError(e.ToString());
				return fc;
			}
			
			string[] lines = Regex.Split(fcinfoResult, "\r\n");
			FibreChannelDTOResponse card = null;
			string modelName = "";
			for (int i = 0; i < lines.Length; i++)
			{
				string line = lines[i].Trim();
				if (line.Length == 0)
				{
					continue;
				}

				string[] lineParts = line.Split(':');
				if (lineParts.Length != 2)
				{
					continue;
				}

				if (lineParts[0].ToLower() == "adapter")
				{
					if (card != null)
					{
						if (modelName.Length > 0)
						{
							card.ModelName = modelName;
						}
						fc.Add(card);
					}
					card = new FibreChannelDTOResponse();
					string[] adapterNameParts = lineParts[1].Trim().Split('-');
					if (adapterNameParts.Length > 0)
					{
						card.PhysicalId = adapterNameParts[adapterNameParts.Length - 1];
					}
				} else if (card != null) {
					switch (lineParts[0].ToLower())
					{
						case "descrp":
							card.Label = lineParts[1].Trim();
							break;
						case "model":
							if (modelName.Length > 0) 
							{
								modelName = " " + lineParts[1].Trim();
							} 
							else 
							{
								modelName = lineParts[1].Trim();
							}
							break;
						case "manfac":
							if (modelName.Length > 0) 
							{
								modelName = lineParts[1].Trim() + " " + modelName;
							}
							else
							{
								modelName = lineParts[1].Trim();
							}
							break;
					}
				}
			}
			if (card != null)
			{
				fc.Add(card);
			}
			
			return fc;
		}
		
		public string GetShareWWN(string serialNumber) {
			string fcinfoResult = "";
			try
			{
				fcinfoResult = ExecuteFcinfoCommand("mapping");
			}
			catch (ExternalCommandExecutionException e)
			{
				Logger.Instance.LogWarning(
					"[GetShareWWN] To get informations about FC cards or disk shares install fcinfo tool."
				);
				Logger.Instance.LogError(e.ToString());
				return "";
			}
						
			string[] lines = Regex.Split(fcinfoResult, "\r\n");
			Regex rgx = new Regex( @"[a-zA-Z0-9]{16}");
			for (int i = 0; i < lines.Length; i++)
			{
				string line = lines[i].Trim();
				if (line.Length == 0)
				{
					continue;
				}

				if (line.ToLower().Contains(serialNumber.ToLower()))
				{
					Match m = rgx.Match(line);
					if (m.Success)
					{
						return m.Value;
					}
				}
			}
			
			return "";
		}
		
		protected string ExecuteFcinfoCommand(string option)
		{
			Process proc = new Process();
			proc.StartInfo = PrepareProcessStartInfo(option);
			try
			{
				proc.Start();
			}
			catch (Exception e)
			{
				throw new ExternalCommandExecutionException(e.Message);
			}
			
			string errorMessage = proc.StandardError.ReadToEnd();
			if (errorMessage.Length > 0)
			{
				throw new ExternalCommandExecutionException(errorMessage);
			}

			return proc.StandardOutput.ReadToEnd();
		}
		
		protected ProcessStartInfo PrepareProcessStartInfo(string option)
		{
			ProcessStartInfo psi = new ProcessStartInfo();
			psi.FileName = "fcinfo.exe";
			psi.Arguments = "/" + option;
			psi.RedirectStandardOutput = true;
			psi.RedirectStandardError = true;
			psi.UseShellExecute = false;
			psi.CreateNoWindow = true;

			return psi;
		}
	}
}
