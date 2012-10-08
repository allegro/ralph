using System;
using System.ServiceProcess;
using System.Threading;
using DonPedro.Utils;

namespace DonPedro
{
	public class DonPedroService : ServiceBase
	{
		private DonPedroJob job;
		private Timer stateTimer;
		private TimerCallback timerDelegate;
		
		public DonPedroService()
		{
			this.ServiceName = "DonPedro";
			this.CanStop = true;
			this.CanPauseAndContinue = false;
			this.AutoLog = false;
		}
		
		public static void DonPedroUnhandledException(object sender, UnhandledExceptionEventArgs e)
		{
			Logger.Instance.LogError(e.ExceptionObject.ToString());
		}
		
		public static void Main()
		{
			AppDomain.CurrentDomain.UnhandledException += new UnhandledExceptionEventHandler(DonPedroUnhandledException);
			ServiceBase.Run(new DonPedroService());
		}
		
		protected override void OnStart(string[] args)
		{
			int notificationsInterval = Properties.app.Default.notifications_interval;

			job = new DonPedroJob();
			timerDelegate = new TimerCallback(job.NotifyRalph);
			stateTimer = new Timer(timerDelegate, null, 1000, notificationsInterval * 1000);
		}
		
		protected override void OnStop()
		{
			stateTimer.Dispose();
		}
	}
}
