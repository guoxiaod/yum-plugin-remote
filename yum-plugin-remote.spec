Name: yum-plugin-remote
Version: 0.1.0
Release: 1%{?dist}
Summary: Run yum command on remote host Plugin for Yum

Group: System Environment/Base
License: GPL
URL: http://github.com/guoxiaod/%{name}
BuildArch: noarch
Source0: http://github.com/guoxiaod/%{name}-%{version}.tar.gz
BuildRoot: %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

Requires: yum, openssh, pexpect

%description
This plugin run yum command on remote host.
Just add an option "--host" to yum command line, so we can specific the remote host
we will run command on.

%prep
%setup -q

%build
# pass

%install
rm -rf %{buildroot}
%{__mkdir} -p %{buildroot}%{_sysconfdir}/yum/pluginconf.d/ \
                %{buildroot}%{_prefix}/lib/yum-plugins/

%{__install} -m 0644 remote.conf \
    %{buildroot}%{_sysconfdir}/yum/pluginconf.d/
%{__install} -m 0644 remote.py \
    %{buildroot}%{_prefix}/lib/yum-plugins/

%clean
rm -rf %{buildroot}


%files
%defattr(-,root,root,-)
%doc README LICENSE ChangeLog
%config(noreplace) %{_sysconfdir}/yum/pluginconf.d/remote.conf
%{_prefix}/lib/yum-plugins/remote.py*



%changelog
* Mon Feb 13 2012 Anders <gxd305@gmail.com> - 0.1.0
- The first version
