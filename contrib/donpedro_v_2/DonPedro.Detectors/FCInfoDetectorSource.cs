using System;
using System.Collections.Generic;
using System.Diagnostics;
using DonPedro.DTO;
using DonPedro.Detectors.Exceptions;
using System.Text.RegularExpressions;

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
				fcinfoResult = ExecuteFcinfoCommand();
			}
			catch (ExternalCommandExecutionException)
			{
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
		
		protected string ExecuteFcinfoCommand()
		{
			Process proc = new Process();
			proc.StartInfo = PrepareProcessStartInfo();
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
		
		protected ProcessStartInfo PrepareProcessStartInfo()
		{
			ProcessStartInfo psi = new ProcessStartInfo("cmd.exe", @"/C %windir%\\Sysnative\\fcinfo.exe /details");
			psi.RedirectStandardOutput = true;
			psi.RedirectStandardError = true;
			psi.UseShellExecute = false;
			psi.CreateNoWindow = true;

			return psi;
		}
	}
}
