using System;

namespace DonPedro.DTO
{
	public class DiskShareMountDTOResponse : BaseDTOResponse
	{
		public string Volume { 
			get {
				return this.Label;
			}
			set {
				this.Label = value;
			}
		}
		public string Sn { get; set; }
	}
}
