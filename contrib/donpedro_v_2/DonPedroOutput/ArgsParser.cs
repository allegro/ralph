using System;

namespace DonPedroOutput
{
	public class ArgsParser
	{
		protected string[] PassedArgs;
		
		public ArgsParser(string[] args)
		{
			PassedArgs = args;
		}
		
		public bool IsSet(string arg)
		{
			foreach(string item in PassedArgs)
			{
				string rawItem = item.Split('=')[0].Replace("--", "");
				if (rawItem.Equals(arg))
				{
					return true;
				}
			}
			
			return false;
		}
		
		public string GetArgValue(string arg)
		{
			foreach(string item in PassedArgs)
			{
				string[] parts = item.Split('=');
				if (!parts[0].Replace("--", "").Equals(arg))
				{
					continue;
				}
				
				if (parts.Length == 1)
				{
					return "";
				}
				
				return parts[1];
			}
			
			return "";
		}
	}
}
