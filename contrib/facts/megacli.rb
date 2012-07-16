require 'set'

cmd = '/opt/MegaRAID/MegaCli/MegaCli64'
cmd_opts = 'PDList -aALL -NoLog'

supported_attributes = Set.new ['WWN', 'PD Type', 'Raw Size',
                                'Non Coerced Size', 'Coerced Size',
                                'Device Firmware Level', 'Inquiry Data',
                                'Media Type']

cmd_list = Facter::Util::Resolution.exec(cmd + ' ' + cmd_opts)
unless cmd_list.nil?
  adapter_id = nil
  device_id = nil
  cmd_list.each_line do |l|
    if l =~ /^(\s*)([^:]+): (.+)$/
      value = $3
      if $2 == 'Device Id'
        device_id = $3
      elsif !adapter_id.nil? && !device_id.nil?
        if supported_attributes.member? $2
          fact_name = $2.downcase.gsub(/ /, '_')
          Facter.add("megacli_#{adapter_id}_#{device_id}__#{fact_name}") do
            setcode do
              value.chomp
            end
          end
        end
      end
    elsif l =~ /^(\s*)Adapter #(\d+)(.*)$/
      adapter_id = $2
    elsif l =~ /^(\s*)$/
      device_id = nil
    end
  end
end
