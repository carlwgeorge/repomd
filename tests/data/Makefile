RPMS := $(addsuffix .rpm,brisket chicken ribs sausage)

all: repo empty_repo sqlite_repo

%.rpm:
	@rpmbuild --define "_topdir $(shell pwd)" --define "vendor Carl's BBQ" --define "packager Carl" --define "dist .fc27" -bb $(basename $@).spec
	@mv RPMS/noarch/*.rpm .
	-rpm -q --qf '%{name}-%{version}-%{release}.%{arch}.rpm %{buildtime}\n' *rpm > buildtimes
	@rm -rf BUILD BUILDROOT RPMS SOURCES SPECS SRPMS

repo: $(RPMS)
	@mkdir repo
	@cp *.rpm repo
	@createrepo --simple-md-filenames --no-database --outputdir repo repo
	@rm repo/repodata/filelists.xml.gz repo/repodata/other.xml.gz repo/*.rpm

empty_repo:
	@mkdir empty_repo
	@createrepo --simple-md-filenames --no-database --outputdir empty_repo empty_repo
	@rm empty_repo/repodata/filelists.xml.gz empty_repo/repodata/other.xml.gz

sqlite_repo:
	@mkdir sqlite_repo
	@cp *.rpm sqlite_repo
	@createrepo --outputdir sqlite_repo sqlite_repo
	@rm sqlite_repo/repodata/*filelists.xml.* sqlite_repo/repodata/*other.xml.* sqlite_repo/*.rpm

clean:
	@if test -d repo; then rm -r repo; fi
	@if test -d empty_repo; then rm -r empty_repo; fi
	@if test -d sqlite_repo; then rm -r sqlite_repo; fi
	@if test -f "*.rpm"; then rm *.rpm; fi
	@if test -f buildtimes; then rm buildtimes; fi
