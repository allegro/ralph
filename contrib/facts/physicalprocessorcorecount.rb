# physicalprocessorcorecount.rb

if Facter.value(:kernel) == 'Linux'
  corepercpu = 0
  cpuinfo = %x{cat /proc/cpuinfo}.split(/\n\n/)
  cpuinfo[0].each_line do |line|
    if line =~ /cpu cores\s+:\s+(\d+)/
      corepercpu = $1.to_i
    end
  end
  cpus = %x{grep 'physical id' /proc/cpuinfo | sort | uniq | wc -l}.chomp.to_i
  Facter.add('physicalprocessorcorecount') do
    setcode do
      cpus * corepercpu
    end
  end
end
