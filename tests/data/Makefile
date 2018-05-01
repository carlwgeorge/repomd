RPMS := $(addsuffix .rpm,brisket chicken ribs sausage)

all: repo empty_repo

%.rpm:
	@rpmbuild --define "_topdir $(shell pwd)" --define "vendor Carl's BBQ" --define "packager Carl" -bb $(basename $@).spec
	@mv RPMS/noarch/*.rpm .
	@rm -r BUILD BUILDROOT RPMS SOURCES SPECS SRPMS

repo: $(RPMS)
	@mkdir repo
	@mv *.rpm repo
	@createrepo_c --simple-md-filenames --no-database --outputdir repo repo
	@rm repo/repodata/filelists.xml.gz repo/repodata/other.xml.gz repo/*.rpm

empty_repo:
	@mkdir empty_repo
	@createrepo_c --simple-md-filenames --no-database --outputdir empty_repo empty_repo
	@rm empty_repo/repodata/filelists.xml.gz empty_repo/repodata/other.xml.gz

clean:
	@if test -d repo; then rm -r repo; fi
	@if test -d empty_repo; then rm -r empty_repo; fi
