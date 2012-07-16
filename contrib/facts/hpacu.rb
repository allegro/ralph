require 'set'

cmd = 'hpacucli'
cmd_opts = 'ctrl all show config detail'

logical_attributes = Set.new ['Disk Name', 'Fault Tolerance', 'Mount Points',
                              'Status']
physical_attributes = Set.new ['Interface Type', 'Size', 'Rotational Speed',
                               'Firmware Revision', 'Serial Number', 'Model',
                               'Status']


cmd_list = Facter::Util::Resolution.exec(cmd + ' ' + cmd_opts)
unless cmd_list.nil?
  log_id = nil
  log_indent = 0
  physical_id = nil
  physical_indent = 0
  cmd_list.each_line do |l|
    if l =~ /^(\s*)([^:]+): (.+)$/
      value = $3
      if $2 == 'Logical Drive'
        log_id = value
        log_indent = $1.length
        physical_id = nil
        physical_indent = 0
      elsif !log_id.nil? && physical_id.nil? && $1.length > log_indent
        if logical_attributes.member? $2
          fact_name = $2.downcase.gsub(/ /, '_')
          Facter.add("hpacu_#{log_id}__#{fact_name}") do
            setcode do
              value.chomp
            end
          end
        end
      elsif !log_id.nil? && !physical_id.nil? && $1.length > physical_indent
        if physical_attributes.member? $2
          fact_name = $2.downcase.gsub(/ /, '_')
          Facter.add("hpacu_#{log_id}__#{physical_id}__#{fact_name}") do
            setcode do
              value.chomp
            end
          end
        end
      end
    elsif l =~ /^(\s*)physicaldrive (.*)$/
      physical_id = $2
      physical_indent = $1.length
    end
  end
end
