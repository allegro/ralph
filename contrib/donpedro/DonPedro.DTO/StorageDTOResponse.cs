/*
 * Created by SharpDevelop.
 * User: Andrzej Jankowski
 * Date: 9/25/2012
 * Time: 11:40 PM
 * 
 */
using System;
using DonPedro.DTO;

namespace DonPedro.DTO
{
	public class StorageDTOResponse : BaseDTOResponse
	{
		public string sn { get; set; }
		public string mount_point { get; set; }
		public string size { get; set; }
	}
}
