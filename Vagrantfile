# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
	config.vm.box = "quantal64"
	config.vm.box_url = "https://github.com/downloads/roderik/VagrantQuantal64Box/quantal64.box"

	config.vm.synced_folder ".", "/opt/satori/src"
	config.vm.provision :shell, :inline => "apt-get update -qq && apt-get install -y python-virtualenv python-dev libpopt-dev libcurl4-openssl-dev libpq-dev libyaml-dev libcap-dev make patch"
	config.vm.provision :shell, :inline => "chown vagrant:vagrant /opt/satori"
	config.vm.provision :shell, :inline => "su vagrant -c /opt/satori/src/vagrant/bootstrap.sh"

	config.vm.define :core do |core|
		core.vm.network :private_network, ip: "10.231.0.1"
		core.vm.provision :shell, :inline => "apt-get install -y postgresql postgresql-contrib"
		core.vm.provision :shell, :inline => "su postgres -c psql < /opt/satori/src/vagrant/pgsql_setup.sql"
	end
	
	config.vm.define :web do |web|
		web.vm.network :private_network, ip: "10.231.0.2"
	end
	
	config.vm.define :judge do |judge|
		judge.vm.network :private_network, ip: "10.231.0.3"
		judge.vm.provision :shell, :inline => "apt-get install -y libseccomp0 libseccomp-dev"
	end
end
