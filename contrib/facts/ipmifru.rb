# ipmifru.rb
require 'zlib'

cmd = '/usr/sbin/ipmitool fru print'

cmd_out = Facter::Util::Resolution.exec(cmd)
unless cmd_out.nil?
	Facter.add('ipmifru') do
		setcode do
			z = Zlib::Deflate.new(9)
			z_cmd_out = z.deflate(cmd_out.chomp, Zlib::FINISH)
			z.close
			unless $0 =~ /facter/
				z_cmd_out
			else
				'compressed'
			end
		end
	end
end

