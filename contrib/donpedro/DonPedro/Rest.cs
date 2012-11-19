using System;
using System.IO;
using System.Net;
using System.Text;
using System.Runtime.Serialization;

namespace DonPedro
{
	public class Rest
	{
		public Rest()
		{
		}
		
		public string Post(string url, string jsonData)
		{
			HttpWebRequest req = WebRequest.Create(new Uri(url)) as HttpWebRequest;
			req.Method = "POST";
			req.ContentType = "application/json";
			req.UserAgent = "DonPedro " + System.Reflection.Assembly.GetExecutingAssembly().GetName().Version.ToString();
			StringBuilder s = new StringBuilder();
			byte[] formData = UTF8Encoding.UTF8.GetBytes(jsonData.ToString());
			req.ContentLength = formData.Length;
			using (Stream post = req.GetRequestStream())
			{
				post.Write(formData, 0, formData.Length);
			}
			string result = null;
			using (HttpWebResponse resp = req.GetResponse() as HttpWebResponse)
			{
				StreamReader reader = new StreamReader(resp.GetResponseStream());
				result = reader.ReadToEnd();
			}
			return result;
		}
		
		public string Get(string url)
		{
			HttpWebRequest req = WebRequest.Create(new Uri(url)) as HttpWebRequest;
			req.Method = "GET";
			req.ContentType = "application/json";
			req.UserAgent = "DonPedro " + System.Reflection.Assembly.GetExecutingAssembly().GetName().Version.ToString();
			StringBuilder s = new StringBuilder();
			string result = null;
			using (HttpWebResponse resp = req.GetResponse() as HttpWebResponse)
			{
				StreamReader reader = new StreamReader(resp.GetResponseStream());
				result = reader.ReadToEnd();
			}
			return result;
		}
	}
}
