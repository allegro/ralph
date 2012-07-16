# iostat.rb

cmd = '/usr/bin/iostat -En'
if Facter.value(:kernel) == 'SunOS'
	iostat_list = Facter::Util::Resolution.exec(cmd)
	iostat = iostat_list.split(/Predictive Failure Analysis: \d+\s+\n/)
	re = /(\w+)\s+Soft Errors: (\d+) Hard Errors: (\d+) Transport Errors: (\d+)\s\nVendor: (.*?) Product: (.*?) Revision: (.*?) Serial No: (.*?)\s\nSize: (.*?) <(\d+) bytes>\s?\nMedia Error: (\d+) Device Not Ready: (\d+) No Device: (\d+) Recoverable: (\d+)\s\nIllegal Request: (\d+)/
	iostat.each do |line|
		if line.match(re)
			name,vend,prod,rev,sn,size,sizebyte = $1,$5,$6,$7,$8,$9,$10
			Facter.add("disk_#{name}_vendor") do
				setcode do
					vend
				end
			end
			Facter.add("disk_#{name}_product") do
				setcode do 
					prod
				end
			end
			Facter.add("disk_#{name}_revision") do
				setcode do
					rev
				end
			end
			Facter.add("disk_#{name}_serial") do
				setcode do
					sn
				end
			end
			Facter.add("disk_#{name}_size") do
				setcode do
					sizebyte
				end
			end
		end
	end
end
