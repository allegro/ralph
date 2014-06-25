using System;
using DonPedro.DTO;

namespace DonPedro.DTO
{
	public class MacAddressDTOResponse : BaseDTOResponse
	{
		private string macAddress;
		
		public string Mac { 
			get 
			{
				return macAddress;
			}
			
			set
			{
				macAddress = value.Replace(":", "").Replace("-", "").ToUpper();
			}
		}
	}
}
