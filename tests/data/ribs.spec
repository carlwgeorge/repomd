Name: ribs
Version: 3.2.0
Release: 1%{?dist}
Summary: Ribs
License: BBQ
URL: https://example.com/%{name}
BuildArch: noarch

%description
%{summary}.

%package -n beef-ribs
Summary: Beef ribs

%description -n beef-ribs
Beef ribs.

%package -n pork-ribs
Summary: Pork ribs

%description -n pork-ribs
Pork ribs.

%prep
%setup -q -c -T

%build
cat > beef-ribs << EOF
#!/usr/bin/bash
echo "I love beef ribs."
EOF
cat > pork-ribs << EOF
#!/usr/bin/bash
echo "I love pork ribs."
EOF

%install
install -D -p -m 755 beef-ribs %{buildroot}%{_bindir}/beef-ribs
install -D -p -m 755 pork-ribs %{buildroot}%{_bindir}/pork-ribs

%files -n beef-ribs
%{_bindir}/beef-ribs

%files -n pork-ribs
%{_bindir}/pork-ribs
