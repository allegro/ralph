# lshw.rb
require 'zlib'

cmd = 'lshw'
cmd_opts = '-xml -quiet'

cmd_out = Facter::Util::Resolution.exec(cmd + ' ' + cmd_opts)
unless cmd_out.nil?
  Facter.add('lshw') do
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
