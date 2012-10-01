using System;
using System.Collections.Generic;
using System.Diagnostics;
using DonPedro.DTO;
using DonPedro.Detectors.Exceptions;

namespace DonPedro.Detectors
{
	public class FCInfoDetectorSource
	{
		public FCInfoDetectorSource()
		{
		}
		
		public List<FibreChannelDTOResponse> GetFibreChannelInfo()
		{
			List<FibreChannelDTOResponse> fc = new List<FibreChannelDTOResponse>();
			
			GetDataFromFcinfo();
			
			return fc;
		}
		
		protected string GetDataFromFcinfo()
		{
			string fcinfoResult;
			
			try
			{
				fcinfoResult = ExecuteFcinfoCommand();
			}
			catch (ExternalCommandExecutionException e)
			{
				return "";
			}
			
			// parsing...
			
			return fcinfoResult;
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
			ProcessStartInfo psi = new ProcessStartInfo("cmd.exe", "/C C:/Windows/System32/fcinfo.exe");
			psi.RedirectStandardOutput = true;
			psi.RedirectStandardError = true;
			psi.UseShellExecute = false;
			psi.CreateNoWindow = true;

			return psi;
		}
	}
}
