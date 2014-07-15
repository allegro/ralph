using System;

namespace DonPedro.DTO
{
	public class DiskShareMountDTOResponse : BaseDTOResponse
	{
		private string wwn;
		
		public string Volume { get; set; }
		
		public string Size { get; set; }
		
		public string SerialNumber { 
			get {
				return wwn;
			}
			
			set {
				wwn = NormalizeWWN(value);
			}
		}
		
		private string NormalizeWWN(string wwn)
		{
			wwn = wwn.Replace(
				":", ""
			).Replace(
				" ", ""
			).Replace(
				".", ""
			).Trim().ToUpper();
			
			if (wwn.Length == 16)
			{
				// 3PAR
			}
			else if (wwn.Length == 17)
			{
				// 3PAR - multipath
				wwn = wwn.Substring(1);
			}
			else if (wwn.Length == 33 && wwn.Substring(27).Equals("000000") && wwn.Substring(8, 3).Equals("000"))
			{
				// MSA - multipath
				wwn = wwn.Substring(11, 16);
			}
			else if (wwn.Length == 32 && wwn.Substring(27).Equals("000000") && wwn.Substring(12, 4).Equals("0000"))
			{
				// MSA
				wwn = wwn.Substring(6, 6) + wwn.Substring(16, 10);
			}
			else if (wwn.Length == 33 && wwn.Substring(25).Equals("00000000") && wwn.StartsWith("36000402"))
			{
				// NEXSAN
				wwn = wwn.Substring(0, 25);
			}
			else if (wwn.Length == 32 && wwn.StartsWith("600A0B80"))
			{
				// IBM
			}
			else if (
				wwn.Length == 33 && 
				(
					wwn.StartsWith("3600A0B80") ||
					wwn.StartsWith("3600508B1") ||
					wwn.StartsWith("3600144F0")
				)
			)
			{
				// IBM - multipath
            	// HP logical volume - multipath
            	// SUN - multipath
            	wwn = wwn.Substring(1);
			}

			return wwn;
		}
	}
}
