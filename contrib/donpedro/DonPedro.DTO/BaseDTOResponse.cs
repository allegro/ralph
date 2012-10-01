using System;
using System.Collections;

namespace DonPedro.DTO
{
	public abstract class BaseDTOResponse
	{
		public string Label { get; set; }

		public string ToJson()
		{
			ArrayList parts = new ArrayList();

			foreach (var property in this.GetType().GetProperties())
			{
				parts.Add(
					string.Format(
						"\"{0}\":\"{1}\"", property.Name, property.GetValue(this, null)
					)
				);
			}

			return "{" + String.Join(",", (String[]) parts.ToArray(typeof(string))) + "}";
		}
	}
}
