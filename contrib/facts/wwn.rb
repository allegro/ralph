wwn_cmd = '/sbin/multipath'
wwn_cmd_opts = wwn_cmd + ' -l'

if FileTest.exists?(wwn_cmd)
  wwn_cmd_list = Facter::Util::Resolution.exec(wwn_cmd_opts)
  unless wwn_cmd_list.nil?
    wwns = Hash.new
    wwn_cmd_list.each_line { |l| wwns[$1] = $2 if l =~ /(mpath[^\s]+)\s+\(([0-9a-fA-F]+)\)/ }
    if wwns.length != 0
      wwns.keys.sort.each do |k|
        Facter.add("wwn_#{k}") do
          setcode do
            wwns[k].chomp
          end
        end
      end
    end
  end
end
