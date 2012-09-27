/*
 * Created by SharpDevelop.
 * User: Andrzej Jankowski
 * Date: 9/25/2012
 * Time: 11:22 PM
 * 
 */
using System;
using DonPedro.DTO;
using DonPedro.Detectors;
using System.Collections.Generic;
using System.Management;

namespace DonPedro.Detectors
{
	/// <summary>
	/// Detector
	/// </summary>
	public class Detector
	{
		WMIDetectorSource wmiDetector;
		
		public Detector()
		{
			wmiDetector = new WMIDetectorSource();
		}
		
		public List<ProcessorDTOResponse> GetProcessors()
		{
			return  wmiDetector.GetProcessors();
		}
		
		public List<MemoryDTOResponse> GetMemory()
		{
			return wmiDetector.GetMemory();
		}
		
		public List<BaseDTOResponse> GetAllComponents()
		{
			List<BaseDTOResponse> components = new List<BaseDTOResponse>();
			
			foreach (ProcessorDTOResponse obj in GetProcessors())
			{
				components.Add(obj);
			}
			
			foreach (MemoryDTOResponse obj in GetMemory())
			{
				components.Add(obj);
			}
				
			return components;
		}
	}
}
