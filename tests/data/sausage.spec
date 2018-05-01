Name: sausage
Version: 1.9.4
Release: 2%{?dist}
Summary: Sausage
License: BBQ
URL: https://example.com/%{name}
BuildArch: noarch

%description
%{summary}.

%prep
%setup -q -c -T

%build
cat > %{name} << EOF
#!/usr/bin/bash
echo "I love %{name}."
EOF

%install
install -D -p -m 755 %{name} %{buildroot}%{_bindir}/%{name}

%files
%{_bindir}/%{name}
