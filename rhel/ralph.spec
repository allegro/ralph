%if 0%{?rhel} <= 7
%global _python_bytecompile_errors_terminate_build 0
%endif

Summary: DCIM/CMDB for Data Centers / Back Office
Name: ralph-core
Version: %{_version}
Release: 0
License: Apache v2.0 License
BuildArch: x86_64
URL: http://ralph.allegrogroup.com
Packager: opensource@allegro.pl
AutoReqProv: no
BuildRequires: git mariadb-devel openldap-devel python36 python36-devel python36-pip redhat-rpm-config rpm-build
Requires: python36

%{?systemd_requires}

%description
Ralph is an DCIM/CMDB - asset management for Data Centers/ Back Office.

%pre
/usr/bin/getent group ralphsrv >/dev/null || /usr/sbin/groupadd ralphsrv
/usr/bin/getent passwd ralphsrv >/dev/null || /usr/sbin/useradd -g ralphsrv -d /var/local/ralph -s /bin/bash -c "Ralph Service Account" ralphsrv

%prep
rsync -a --delete %{_ralphsrc}/ .

%install
/usr/bin/python3 -m venv %{buildroot}/opt/ralph/ralph-core
source %{buildroot}/opt/ralph/ralph-core/bin/activate
pip3 install nodeenv
nodeenv -p --node=10.16.3
npm install -g bower
# gulp 4 not supported at this time
npm install -g gulp@^3.9.0

make install
make install-test
install -p -D -m 644 contrib/common/etc/ralph/ralph.conf %{buildroot}%{_sysconfdir}/ralph/ralph.conf
install -p -D -m 644 contrib/common/etc/ralph/conf.d/cache.conf %{buildroot}%{_sysconfdir}/ralph/conf.d/cache.conf
install -p -D -m 644 contrib/common/etc/ralph/conf.d/redis.conf %{buildroot}%{_sysconfdir}/ralph/conf.d/redis.conf
install -p -D -m 644 contrib/common/etc/ralph/conf.d/gunicorn.conf %{buildroot}%{_sysconfdir}/ralph/conf.d/gunicorn.conf
install -p -D -m 644 contrib/common/gunicorn/gunicorn.ini %{buildroot}/var/local/ralph/gunicorn.ini
install -p -D -m 755 contrib/common/usr/bin/ralphctl %{buildroot}%{_bindir}/ralphctl
install -p -D -m 644 contrib/common/systemd/ralph.service %{buildroot}%{_unitdir}/ralph.service
cat << EOF > %{buildroot}%{_sysconfdir}/ralph/conf.d/database.conf
DATABASE_ENGINE=transaction_hooks.backends.mysql
DATABASE_HOST=127.0.0.1
DATABASE_PORT=3306
DATABASE_NAME=ralph_ng
DATABASE_USER=ralph_ng
DATABASE_PASSWORD='ralph_ng'
EOF

find %{buildroot} -name package.json -exec sed -i 's#%{buildroot}##g' {} +
find %{buildroot}/opt/ralph/ralph-core/bin -type f -exec sed -i 's#%{buildroot}##g' {} +

mkdir -p %{buildroot}/var/log/ralph
mkdir -p %{buildroot}/var/local/ralph/media
mkdir -p %{buildroot}/usr/share/ralph/static

%post
set -a
. /etc/ralph/ralph.conf
set +a
echo "Collecting django static files..."
/opt/ralph/ralph-core/bin/ralph collectstatic --noinput > /dev/null
echo "Static files collected successfuly."
chown -R ralphsrv:ralphsrv /var/log/ralph /var/local/ralph/media

%files
%defattr(-,root,root,-)
/opt/ralph/ralph-core
%dir %attr(-,ralphsrv,ralphsrv) /var/log/ralph
%dir %attr(-,ralphsrv,ralphsrv) /var/local/ralph
%dir /usr/share/ralph/static
%config %{_sysconfdir}/ralph/ralph.conf
%config %{_sysconfdir}/ralph/conf.d/database.conf
%config %{_sysconfdir}/ralph/conf.d/cache.conf
%config %{_sysconfdir}/ralph/conf.d/redis.conf
%config %{_sysconfdir}/ralph/conf.d/gunicorn.conf
%{_unitdir}/ralph.service
%{_bindir}/ralphctl
/var/local/ralph/gunicorn.ini
