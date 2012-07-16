require 'set'

cmd = 'smartctl'
cmd_opts = '-i'

supported_attributes = Set.new ['Vendor', 'Product', 'Revision', 'User Capacity',
                                 'Serial number', 'Device type', 'Transport protocol']

Facter::Util::Resolution.exec('modprobe sg')

Dir["/dev/sg*"].each { |disk|
  disk_id = disk.split(/\//)[-1]
  cmd_list = Facter::Util::Resolution.exec(cmd + ' ' + cmd_opts + ' ' + disk)
  unless cmd_list.nil?
    cmd_list.each_line do |l|
      if l =~ /^(\s*)([^:]+): (.+)$/
        value = $3
        if supported_attributes.member? $2
          fact_name = $2.downcase.gsub(/ /, '_')
          Facter.add("smartctl_#{disk_id}__#{fact_name}") do
            setcode do
              value.chomp
            end
          end
        end
      end
    end
  end
}
