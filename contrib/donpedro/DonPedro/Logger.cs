using System;
using System.IO;
using System.Reflection;

namespace DonPedro
{
	public class Logger : IDisposable
    {
        private StreamWriter sw;
        public Logger()
        {
        	String path = Path.Combine(
        		Path.GetDirectoryName(System.Reflection.Assembly.GetExecutingAssembly().Location),
        		"logs.txt"
        	);
            sw = new StreamWriter(path, true);
        }
 
        public void Log(string text)
        {
			#if DEBUG
            Console.WriteLine(string.Format("[{0}] {1}", DateTime.Now, text));
			#endif
            sw.WriteLine(string.Format("[{0}] {1}", DateTime.Now, text));
            sw.Flush();
        }
 
        public void LogDebug(string text)
        {
			#if DEBUG
            sw.WriteLine(string.Format("[{0}] [debug] {1}", DateTime.Now, text));
			#endif
			sw.Flush();
        }
 
        public void LogError(string text)
        {
            sw.WriteLine(string.Format("[{0}] [error] {1}", DateTime.Now, text));
            sw.Flush();
        }
 
        public void LogFatal(string text)
        {
            sw.WriteLine(string.Format("[{0}] [fatal] {1}", DateTime.Now, text));
            sw.Flush();
        }
 
        public void Dispose()
        {
            sw.Flush();
            sw.Close();
            sw.Dispose();
        }
 	}
}
