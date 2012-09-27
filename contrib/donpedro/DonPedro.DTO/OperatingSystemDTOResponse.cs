/*
 * Created by SharpDevelop.
 * User: Andrzej Jankowski
 * Date: 9/25/2012
 * Time: 11:37 PM
 * 
 */
using System;
using DonPedro.DTO;

namespace DonPedro.DTO
{
	public class OperatingSystemResponseDTO : BaseDTOResponse
	{
		public string memory { get; set; }
		public string storage { get; set; }
		public string cores_count { get; set; }
	}
}
