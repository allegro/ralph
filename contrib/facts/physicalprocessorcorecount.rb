# physicalprocessorcorecount.rb

if Facter.value(:kernel) == 'Linux'
  %x{cat /proc/cpuinfo}.split(/\n\n/)[0].each_line do |line|
    if line =~ /cpu cores\s+:\s+(\d+)/
      cores = $1.to_i * Facter.value(:physicalprocessorcount)
      Facter.add('physicalprocessorcorecount') do
        setcode do
          cores
        end
      end
    end
  end
end
