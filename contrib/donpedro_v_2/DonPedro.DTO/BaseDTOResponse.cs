using System;
using System.Collections;
using System.Text.RegularExpressions;

namespace DonPedro.DTO
{
	public abstract class BaseDTOResponse
	{
		public static string AppendUnderscore(Match m) {
			return "_" + m.ToString();
		}
		
		public string ToJSON()
		{
			ArrayList parts = new ArrayList();
			int propertiesCount = this.GetType().GetProperties().Length;
			string propertyValue;

			foreach (var property in this.GetType().GetProperties())
			{
				propertyValue = property.GetValue(
					this, null
				).ToString().Replace(
					"\"", "\\\""
				).Replace(
					@"\", @"\\"
				);
				
				if (propertyValue.Length > 0) {
					if (propertiesCount == 1)
					{
						return "\"" + propertyValue + "\"";
					}
					
					try
					{
						parts.Add(
							string.Format(
								"\"{0}\":\"{1}\"", 
								Regex.Replace(
									property.Name,
									@"\B[A-Z]",
									new MatchEvaluator(BaseDTOResponse.AppendUnderscore)
								).ToLower().Trim(),
								propertyValue
							)
						);
					}
					catch (NullReferenceException) {}
				}
			}

			return "{" + string.Join(",", (string[]) parts.ToArray(typeof(string))) + "}";
		}
	}
}
