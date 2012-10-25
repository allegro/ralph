using System;
using System.Collections;

namespace DonPedro.DTO
{
	public abstract class BaseDTOResponse
	{
		public string Label { get; set; }

		public string ToJSON()
		{
			ArrayList parts = new ArrayList();

			foreach (var property in this.GetType().GetProperties())
			{
				try
				{
					parts.Add(
						string.Format(
							"\"{0}\":\"{1}\"", 
							property.Name.ToLower(),
							property.GetValue(this, null).ToString().Replace("\"", "\\\"")
						)
					);
				}
				catch (NullReferenceException)
				{
				}
			}

			return "{" + string.Join(",", (string[]) parts.ToArray(typeof(string))) + "}";
		}
	}
}
