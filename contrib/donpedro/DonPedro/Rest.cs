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
		
		public string Post(string url, string json_data)
		{
		  HttpWebRequest req = WebRequest.Create(new Uri(url)) as HttpWebRequest;
		  req.Method = "POST";  
		  req.ContentType = "application/json";
		  StringBuilder s = new StringBuilder();
		  byte[] formData = UTF8Encoding.UTF8.GetBytes(json_data.ToString());
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
