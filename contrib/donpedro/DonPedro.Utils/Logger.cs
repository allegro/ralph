using System;
using System.Diagnostics;

namespace DonPedro.Utils
{
	public sealed class Logger
	{
		private static Logger instance = new Logger();
		private EventLog log;
		
		public static Logger Instance {
			get {
				return instance;
			}
		}
		
		public void LogInformation(string msg)
		{
			log.WriteEntry(msg, EventLogEntryType.Information);
		}
		
		public void LogWarning(string msg)
		{
			log.WriteEntry(msg, EventLogEntryType.Warning);
		}
		
		public void LogError(string msg)
		{
			log.WriteEntry(msg, EventLogEntryType.Error);
		}
		
		private Logger()
		{
			if(!EventLog.SourceExists("DonPedro"))
			{
				EventLog.CreateEventSource("DonPedro", "DonPedroLogs");
			}
			log = new EventLog();
			log.Source = "DonPedro";
		}
	}
}
