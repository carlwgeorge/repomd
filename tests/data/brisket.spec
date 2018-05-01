Name: brisket
Epoch: 1
Version: 5.1.1
Release: 1%{?dist}
Summary: Brisket
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
