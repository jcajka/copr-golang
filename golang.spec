# build ids are not currently generated:
# https://code.google.com/p/go/issues/detail?id=5238
#
# also, debuginfo extraction currently fails with
# "Failed to write file: invalid section alignment"
%global debug_package %{nil}

# we are shipping the full contents of src in the data subpackage, which
# contains binary-like things (ELF data for tests, etc)
%global _binaries_in_noarch_packages_terminate_build 0

# Do not check any files in doc or src for requires
%global __requires_exclude_from ^(%{_datadir}|/usr/lib)/%{name}/(doc|src)/.*$

# Don't alter timestamps of especially the .a files (or else go will rebuild later)
# Actually, don't strip at all since we are not even building debug packages and this corrupts the dwarf testdata
%global __strip /bin/true

# rpmbuild magic to keep from having meta dependency on libc.so.6
%define _use_internal_dependency_generator 0
%define __find_requires %{nil}
%global __spec_install_post /usr/lib/rpm/check-rpaths   /usr/lib/rpm/check-buildroot  \
  /usr/lib/rpm/brp-compress

%if 0%{?rhel} > 5 || 0%{?fedora} < 21
%global gopath          %{_datadir}/gocode
%global golang_arches       %{ix86} x86_64 %{arm}
%endif

%global golibdir %{_libdir}/golang

# Golang build options.

# Buid golang using external/internal(close to cgo disabled) linking.
%ifarch %{golang_arches} %{power64} s390x
%global external_linker 1
%else
%global external_linker 0
%endif

# Build golang with cgo enabled/disabled(later equals more or less to internal linking).
%ifarch %{golang_arches} %{power64} s390x
%global cgo_enabled 1
%else
%global cgo_enabled 0
%endif

# Use golang/gcc-go as bootstrap compiler
%ifarch %{golang_arches}
%global golang_bootstrap 1
%else
%global golang_bootstrap 0
%endif
# boostrap(with internal linking) using gcc-go fails due to bug in tests(https://github.com/golang/go/issues/12629)
# make check not to fail due to it

# Controls what ever we fails on failed tests
%ifarch %{golang_arches} %{power64}
%global fail_on_tests 1
%else
%global fail_on_tests 0
%endif

# TODO get more support for shared objects
# Build golang shared objects for stdlib
%ifarch %{ix86} x86_64 ppc64le %{arm} aarch64
%global shared 1
%else
%global shared 0
%endif

# Fedora GOROOT
%global goroot          /usr/lib/%{name}

%ifarch x86_64
%global gohostarch  amd64
%endif
%ifarch %{ix86}
%global gohostarch  386
%endif
%ifarch %{arm}
%global gohostarch  arm
%endif
%ifarch aarch64
%global gohostarch  arm64
%endif
%ifarch ppc64
%global gohostarch  ppc64
%endif
%ifarch ppc64le
%global gohostarch  ppc64le
%endif
%ifarch s390x
%global gohostarch  s390x
%endif

%global go_api 1.7
%global go_version 1.7
%global go_commit c80e0d374ba3caf8ee32c6fe4a5474fa33928086
%global go_shortcommit %(c=%{go_commit}; echo ${c:0:7})

Name:           golang
Version:        1.7
Release:        0.39git%{go_shortcommit}%{?dist}
Summary:        The Go Programming Language
# source tree includes several copies of Mark.Twain-Tom.Sawyer.txt under Public Domain
License:        BSD and Public Domain
URL:            http://golang.org/
# upstream source tarball processed by source.sh in this repo 
# (folder renamed to go)
Source0:        https://github.com/golang/go/archive/%{go_commit}/golang-%{go_shortcommit}.tar.gz
# to avoid shipping whole tar-ed repo
# generated using `git log -n 1 --format="format:devel +%h %cd" HEAD > VERSION` on checked out repo
Source1: VERSION
Source2: macros.golang

# The compiler is written in Go. Needs go(1.4+) compiler for build.
%if !%{golang_bootstrap}
BuildRequires:  gcc-go >= 5
%else
BuildRequires:  golang > 1.4
%endif
%if 0%{?rhel} > 6 || 0%{?fedora} > 0
BuildRequires:  hostname
%else
BuildRequires:  net-tools
%endif
# for tests
BuildRequires:  pcre-devel, glibc-static, perl

%if 0%{?rhel}
Provides:       go-srpm-macros
%endif
Provides:       go = %{version}-%{release}
Requires:       %{name}-bin = %{version}-%{release}
Requires:       %{name}-src = %{version}-%{release}
%if 0%{?fedora} > 21
Requires:       go-srpm-macros
%endif


Patch0:         golang-1.2-verbose-build.patch

# https://bugzilla.redhat.com/show_bug.cgi?id=1038683
Patch1:         golang-1.2-remove-ECC-p224.patch

# use the arch dependent path in the bootstrap
Patch212:       golang-1.5-bootstrap-binary-path.patch

# disable TestGdbPython
# https://github.com/golang/go/issues/11214
Patch213:       go1.5beta1-disable-TestGdbPython.patch

# we had been just removing the zoneinfo.zip, but that caused tests to fail for users that 
# later run `go test -a std`. This makes it only use the zoneinfo.zip where needed in tests.
Patch215:       ./go1.5-zoneinfo_testing_only.patch

# Having documentation separate was broken
Obsoletes:      %{name}-docs < 1.1-4

# RPM can't handle symlink -> dir with subpackages, so merge back
Obsoletes:      %{name}-data < 1.1.1-4

# go1.4 deprecates a few packages
Obsoletes:      %{name}-vim < 1.4
Obsoletes:      emacs-%{name} < 1.4

# These are the only RHEL/Fedora architectures that we compile this package for
ExclusiveArch:  %{golang_arches} %{power64} s390x

Source100:      golang-gdbinit

%description
%{summary}.

%package       docs
Summary:       Golang compiler docs
Requires:      %{name} = %{version}-%{release}
BuildArch:     noarch
Obsoletes:     %{name}-docs < 1.1-4

%description   docs
%{summary}.

%package       misc
Summary:       Golang compiler miscellaneous sources
Requires:      %{name} = %{version}-%{release}
BuildArch:     noarch

%description   misc
%{summary}.

%package       tests
Summary:       Golang compiler tests for stdlib
Requires:      %{name} = %{version}-%{release}
BuildArch:     noarch

%description   tests
%{summary}.

%package        src
Summary:        Golang compiler source tree
BuildArch:      noarch
%description    src
%{summary}

%package        bin
Summary:        Golang core compiler tools
Requires:       go = %{version}-%{release}
# Pre-go1.5, all arches had to be bootstrapped individually, before usable, and
# env variables to compile for the target os-arch.
# Now the host compiler needs only the GOOS and GOARCH environment variables
# set to compile for the target os-arch.
Obsoletes:      %{name}-pkg-bin-linux-386 < 1.4.99
Obsoletes:      %{name}-pkg-bin-linux-amd64 < 1.4.99
Obsoletes:      %{name}-pkg-bin-linux-arm < 1.4.99
Obsoletes:      %{name}-pkg-linux-386 < 1.4.99
Obsoletes:      %{name}-pkg-linux-amd64 < 1.4.99
Obsoletes:      %{name}-pkg-linux-arm < 1.4.99
Obsoletes:      %{name}-pkg-darwin-386 < 1.4.99
Obsoletes:      %{name}-pkg-darwin-amd64 < 1.4.99
Obsoletes:      %{name}-pkg-windows-386 < 1.4.99
Obsoletes:      %{name}-pkg-windows-amd64 < 1.4.99
Obsoletes:      %{name}-pkg-plan9-386 < 1.4.99
Obsoletes:      %{name}-pkg-plan9-amd64 < 1.4.99
Obsoletes:      %{name}-pkg-freebsd-386 < 1.4.99
Obsoletes:      %{name}-pkg-freebsd-amd64 < 1.4.99
Obsoletes:      %{name}-pkg-freebsd-arm < 1.4.99
Obsoletes:      %{name}-pkg-netbsd-386 < 1.4.99
Obsoletes:      %{name}-pkg-netbsd-amd64 < 1.4.99
Obsoletes:      %{name}-pkg-netbsd-arm < 1.4.99
Obsoletes:      %{name}-pkg-openbsd-386 < 1.4.99
Obsoletes:      %{name}-pkg-openbsd-amd64 < 1.4.99

Requires(post): %{_sbindir}/update-alternatives
Requires(postun): %{_sbindir}/update-alternatives

# We strip the meta dependency, but go does require glibc.
# This is an odd issue, still looking for a better fix.
Requires:       glibc
Requires:       gcc
%description    bin
%{summary}

# Workaround old RPM bug of symlink-replaced-with-dir failure
%pretrans -p <lua>
for _,d in pairs({"api", "doc", "include", "lib", "src"}) do
  path = "%{goroot}/" .. d
  if posix.stat(path, "type") == "link" then
    os.remove(path)
    posix.mkdir(path)
  end
end

%if %{shared}
%package        shared
Summary:        Golang shared object libraries

%description    shared
%{summary}.
%endif

%prep
%setup -q -n go

# increase verbosity of build
%patch0 -p1 -b .verbose

# remove the P224 curve
%patch1 -p1 -b .curve

# use the arch dependent path in the bootstrap
%patch212 -p1 -b .bootstrap

# disable TestGdbPython
%patch213 -p1 -b .gdb

cp %{SOURCE1} .

%build
# print out system information
uname -a
cat /proc/cpuinfo
cat /proc/meminfo

# bootstrap compiler GOROOT
%if !%{golang_bootstrap}
export GOROOT_BOOTSTRAP=/
%else
export GOROOT_BOOTSTRAP=%{goroot}
%endif

# set up final install location
export GOROOT_FINAL=%{goroot}

export GOHOSTOS=linux
export GOHOSTARCH=%{gohostarch}

pushd src
# use our gcc options for this build, but store gcc as default for compiler
export CFLAGS="$RPM_OPT_FLAGS"
export LDFLAGS="$RPM_LD_FLAGS"
export CC="gcc"
export CC_FOR_TARGET="gcc"
export GOOS=linux
export GOARCH=%{gohostarch}
%if !%{external_linker}
export GO_LDFLAGS="-linkmode internal"
%endif
%if !%{cgo_enabled}
export CGO_ENABLED=0
%endif
./make.bash --no-clean
popd

# build shared std lib
%if %{shared}
GOROOT=$(pwd) PATH=$(pwd)/bin:$PATH go install -buildmode=shared -v -x std
%endif

%install
rm -rf $RPM_BUILD_ROOT

# create the top level directories
mkdir -p $RPM_BUILD_ROOT%{_bindir}
mkdir -p $RPM_BUILD_ROOT%{goroot}

# install everything into libdir (until symlink problems are fixed)
# https://code.google.com/p/go/issues/detail?id=5830
cp -apv api bin doc favicon.ico lib pkg robots.txt src misc test VERSION \
   $RPM_BUILD_ROOT%{goroot}

# bz1099206
find $RPM_BUILD_ROOT%{goroot}/src -exec touch -r $RPM_BUILD_ROOT%{goroot}/VERSION "{}" \;
# and level out all the built archives
touch $RPM_BUILD_ROOT%{goroot}/pkg
find $RPM_BUILD_ROOT%{goroot}/pkg -exec touch -r $RPM_BUILD_ROOT%{goroot}/pkg "{}" \;
# generate the spec file ownership of this source tree and packages
cwd=$(pwd)
src_list=$cwd/go-src.list
pkg_list=$cwd/go-pkg.list
shared_list=$cwd/go-shared.list
misc_list=$cwd/go-misc.list
docs_list=$cwd/go-docs.list
tests_list=$cwd/go-tests.list
rm -f $src_list $pkg_list $docs_list $misc_list $tests_list $shared_list
touch $src_list $pkg_list $docs_list $misc_list $tests_list $shared_list
pushd $RPM_BUILD_ROOT%{goroot}
	find src/ -type d -a \( ! -name testdata -a ! -ipath '*/testdata/*' \) -printf '%%%dir %{goroot}/%p\n' >> $src_list
	find src/ ! -type d -a \( ! -ipath '*/testdata/*' -a ! -name '*_test*.go' \) -printf '%{goroot}/%p\n' >> $src_list

	find bin/ pkg/ -type d -a ! -path '*_dynlink/*' -printf '%%%dir %{goroot}/%p\n' >> $pkg_list
	find bin/ pkg/ ! -type d -a ! -path '*_dynlink/*' -printf '%{goroot}/%p\n' >> $pkg_list

	find doc/ -type d -printf '%%%dir %{goroot}/%p\n' >> $docs_list
	find doc/ ! -type d -printf '%{goroot}/%p\n' >> $docs_list

	find misc/ -type d -printf '%%%dir %{goroot}/%p\n' >> $misc_list
	find misc/ ! -type d -printf '%{goroot}/%p\n' >> $misc_list

%if %{shared}
    mkdir -p %{buildroot}/%{_libdir}/
    mkdir -p %{buildroot}/%{golibdir}/
    for file in $(find .  -iname "*.so" ); do
        chmod 755 $file
        mv  $file %{buildroot}/%{golibdir}
        pushd $(dirname $file)
        ln -fs %{golibdir}/$(basename $file) $(basename $file)
        popd
        echo "%%{goroot}/$file" >> $shared_list
        echo "%%{golibdir}/$(basename $file)" >> $shared_list
    done
    
	find pkg/*_dynlink/ -type d -printf '%%%dir %{goroot}/%p\n' >> $shared_list
	find pkg/*_dynlink/ ! -type d -printf '%{goroot}/%p\n' >> $shared_list
%endif

	find test/ -type d -printf '%%%dir %{goroot}/%p\n' >> $tests_list
	find test/ ! -type d -printf '%{goroot}/%p\n' >> $tests_list
	find src/ -type d -a \( -name testdata -o -ipath '*/testdata/*' \) -printf '%%%dir %{goroot}/%p\n' >> $tests_list
	find src/ ! -type d -a \( -ipath '*/testdata/*' -o -name '*_test*.go' \) -printf '%{goroot}/%p\n' >> $tests_list
	# this is only the zoneinfo.zip
	find lib/ -type d -printf '%%%dir %{goroot}/%p\n' >> $tests_list
	find lib/ ! -type d -printf '%{goroot}/%p\n' >> $tests_list
popd

# remove the doc Makefile
rm -rfv $RPM_BUILD_ROOT%{goroot}/doc/Makefile

# put binaries to bindir, linked to the arch we're building,
# leave the arch independent pieces in {goroot}
mkdir -p $RPM_BUILD_ROOT%{goroot}/bin/linux_%{gohostarch}
ln -sf %{goroot}/bin/go $RPM_BUILD_ROOT%{goroot}/bin/linux_%{gohostarch}/go
ln -sf %{goroot}/bin/gofmt $RPM_BUILD_ROOT%{goroot}/bin/linux_%{gohostarch}/gofmt

# ensure these exist and are owned
mkdir -p $RPM_BUILD_ROOT%{gopath}/src/github.com
mkdir -p $RPM_BUILD_ROOT%{gopath}/src/bitbucket.org
mkdir -p $RPM_BUILD_ROOT%{gopath}/src/code.google.com/p
mkdir -p $RPM_BUILD_ROOT%{gopath}/src/golang.org/x

# make sure these files exist and point to alternatives
rm -f $RPM_BUILD_ROOT%{_bindir}/go
ln -sf /etc/alternatives/go $RPM_BUILD_ROOT%{_bindir}/go
rm -f $RPM_BUILD_ROOT%{_bindir}/gofmt
ln -sf /etc/alternatives/gofmt $RPM_BUILD_ROOT%{_bindir}/gofmt

# gdbinit
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/gdbinit.d
cp -av %{SOURCE100} $RPM_BUILD_ROOT%{_sysconfdir}/gdbinit.d/golang.gdb

#macros.golang
%if 0%{?rhel} > 5 || 0%{?fedora} < 21
%if 0%{?rhel} > 6 || 0%{?fedora} > 0
mkdir -p $RPM_BUILD_ROOT%{_rpmconfigdir}/macros.d
cp -av %{SOURCE2} $RPM_BUILD_ROOT%{_rpmconfigdir}/macros.d/macros.golang
%else
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/rpm
cp -av %{SOURCE2} $RPM_BUILD_ROOT%{_sysconfdir}/rpm/macros.golang
%endif
%endif


%check
export GOROOT=$(pwd -P)
export PATH="$GOROOT"/bin:"$PATH"
cd src

export CC="gcc"
export CFLAGS="$RPM_OPT_FLAGS"
export LDFLAGS="$RPM_LD_FLAGS"
%if !%{external_linker}
export GO_LDFLAGS="-linkmode internal"
%endif
%if !%{cgo_enabled} || !%{external_linker}
export CGO_ENABLED=0
%endif

# make sure to not timeout
export GO_TEST_TIMEOUT_SCALE=2

%if %{fail_on_tests}
./run.bash --no-rebuild -v -v -v -k
%else
./run.bash --no-rebuild -v -v -v -k || :
%endif
cd ..


%post bin
%{_sbindir}/update-alternatives --install %{_bindir}/go \
    go %{goroot}/bin/go 90 \
    --slave %{_bindir}/gofmt gofmt %{goroot}/bin/gofmt

%preun bin
if [ $1 = 0 ]; then
    %{_sbindir}/update-alternatives --remove go %{goroot}/bin/go
fi


%files
%doc AUTHORS CONTRIBUTORS LICENSE PATENTS
# VERSION has to be present in the GOROOT, for `go install std` to work
%doc %{goroot}/VERSION
%dir %{goroot}/doc
%doc %{goroot}/doc/*

# go files
%dir %{goroot}
%exclude %{goroot}/bin/
%exclude %{goroot}/pkg/
%exclude %{goroot}/src/
%exclude %{goroot}/doc/
%exclude %{goroot}/misc/
%{goroot}/*
%if 0%{?rhel} > 5 || 0%{?fedora} < 21
%if 0%{?rhel} > 6 || 0%{?fedora} > 0
%{_rpmconfigdir}/macros.d/macros.golang
%else
%{_sysconfdir}/rpm/macros.golang
%endif
%endif

# ensure directory ownership, so they are cleaned up if empty
%dir %{gopath}
%dir %{gopath}/src
%dir %{gopath}/src/github.com/
%dir %{gopath}/src/bitbucket.org/
%dir %{gopath}/src/code.google.com/
%dir %{gopath}/src/code.google.com/p/
%dir %{gopath}/src/golang.org
%dir %{gopath}/src/golang.org/x


# gdbinit (for gdb debugging)
%{_sysconfdir}/gdbinit.d

%files -f go-src.list src

%files -f go-docs.list docs

%files -f go-misc.list misc

%files -f go-tests.list tests

%files -f go-pkg.list bin
%{_bindir}/go
%{_bindir}/gofmt

%if %{shared}
%files -f go-shared.list shared
%endif

%changelog
* Wed Jul 27 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.39gitc80e0d3
- rebase to c80e0d374ba3caf8ee32c6fe4a5474fa33928086

* Tue Jul 26 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.38gitea2376f
- rebase to ea2376fcea0be75c856ebd199c0ad0f98192d406

* Tue Jul 12 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.37gita84b18a
- rebase to a84b18ac865257c50d8812e39d244b57809fc8c8

* Mon Jul 04 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.36git003a68b
- rebase to 003a68bc7fcb917b5a4d92a5c2244bb1adf8f690

* Tue Jun 28 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.35gite0c8af0
- rebase to e0c8af090ea1ccc32d06ae75b653446d2a9d6f87

* Tue Jun 21 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.34gitd282427
- rebase to d28242724872c6ab82d53a71fc775095d1171ee7

* Mon Jun 13 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.33git595426c
- rebase to 595426c0d903a3686bdfe6d0e8ef268a60c19896

* Fri Jun 03 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.32gita871464
- rebase to a871464e5aca9b81a6dc54cde8c31629387cb785
- bootstrap patch clean up

* Thu Jun 02 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.31gitba22172
- rebase to ba22172832a971f0884106a5a8ff26a98a65623c

* Wed Jun 01 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.30git88ae649
- rebase to 88ae6495d086ed5b0acb94d5adc49434ec47a675

* Thu May 26 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.29git8a1dc32
- fix build for 32bit intel
- rebase to 8a1dc3244725c2afd170025fc616df840b464a99

* Wed May 25 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.28git72eb46c
- new shared lib packaging
- rebase to 72eb46c5a086051e3677579a0810922724eb6a6d

* Tue May 24 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.27git7a9f6c2
- rebase to 7a9f6c2b56bd87ff7f9296344c9e63cc46194428

* Mon May 16 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.26gita101b85
- rebase to a101b85e00f302706d8b1de1d2173a154d5f54cc

* Fri May 13 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.25git15f2d0e
- rebase to 15f2d0e45227f68024f3415d9466055877b70426

* Thu May 12 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.24git81b70f3
- rebase to 81b70f3751374ccd1eda2f536156dd91cd9f9c9b

* Wed May 11 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.23gitb4538d7
- rebase to b4538d7aaa1a600dc1d3724f9aecb5c8039e1324

* Mon May 09 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.21git87a2ae1
- rebase to 87a2ae1fa25677dc9097a25292c54b7b9dac2c9d

* Tue May 03 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.20git2f41edf
- rebase to 2f41edf120923000c92ed65ab501590fb1c8c548

* Tue May 03 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.19gitfcd7c02
- rebase to fcd7c02c70a110c6f6dbac30ad4ac3eb435ac3fd

* Mon May 02 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.18gite50346d
- rebase to e50346d26a935cd43023856d0df65a158d867c00

* Thu Apr 28 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.17git80e9a7f
- rebase to 80e9a7f0797c73b27471eb4b371baa1c7ccb427b

* Mon Apr 25 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.16git093ac15
- rebase to 093ac15a14137b4a9454442ae9fea282e5c09180

* Mon Apr 18 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.15git95df0c6
- rebase to 95df0c6ab93f6a42bdc9fd45500fd4d56bfc9add

* Fri Apr 15 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.14git8955745
- rebase to 8955745bfb9a3682e78b71fb8cb343abc4bd72a6

* Wed Apr 13 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.13gitb6531fa
- rebase to 6531fab06fc4667b7d167c7e3ee936f28bac68e2

* Tue Apr 12 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.12gitb6cd6d7
- rebase to b6cd6d7d3211bd9030dec4115b6202d93fe570a3

* Mon Apr 11 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.11git720c4c0
- rebase to 720c4c016c75d37d14e0621696127819c8a73b0b

* Fri Apr 08 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.10git4dae828
- rebase to 4dae828f77a37ed87401f7877998b241f0d2c33e

* Tue Apr 05 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.9git3bbede0
- rebase to 3bbede0c512ca645fa19522480c0200ee4711bf3

* Fri Apr 01 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.8gitea306ae
- rebase to ea306ae625d001a43ef20163739593a21be51f97

* Wed Mar 30 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.7git897dcdb
- rebase to 897dcdb5ecc001fac328c53806f8a1dbf2e8c3fd

* Tue Mar 29 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.6git45d334e
- rebase to 45d334ecf1b2bcbf0f8667d4c772ef3db0e03587

* Thu Mar 24 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.5gitebd67ba
- rebase to ebd67ba588eabd5bf968b5bd14dff21a1a1b1be4

* Wed Mar 23 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.4git1374515
- rebase to 1374515a1cf2279c2e47a4ee03a3616781814ad0

* Tue Mar 22 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.3git77f4b77
- prepare for s390x
- rebase to 77f4b773e72b0840a1ce0b314cba44dff9fbaf31

* Mon Mar 21 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.2gitcd187e9
- rebase to cd187e9102bd6c55bb611a0b0f35fc4a7e0fbc51

* Mon Mar 07 2016 Jakub Čajka <jcajka@redhat.com> - 1.7-0.1gited81169
- rebase to ed8116989d84ba50f16cf7a88b5c0a44aa650087
- rebased p224 removal patch
- move to 1.7

* Wed Feb 03 2016 Jakub Čajka <jcajka@redhat.com> - 1.6-0.33git0ed70ef
- rebase to 0ed70efc6b7ec096603c58f27c2668af3862bb3c

* Tue Feb 02 2016 Jakub Čajka <jcajka@redhat.com> - 1.6-0.32gitf309bf3
- rebase to f309bf3eeff8343e557a9798e42ac72b37da3f0a

* Mon Feb 01 2016 Jakub Čajka <jcajka@redhat.com> - 1.6-0.31gitaf15bee
- rebase to af15beeab5ff9cde411c3db086ca9a24ace4c898

* Tue Jan 26 2016 Jakub Čajka <jcajka@redhat.com> - 1.6-0.30git0408ca7
- rebase to 0408ca7de12d72025d40c4d28fd8d9fb142b3c87

* Mon Jan 25 2016 Jakub Čajka <jcajka@redhat.com> - 1.6-0.29git801bebe
- rebase to 801bebefa91205b0b69f2458701aac8169294884

* Fri Jan 22 2016 Jakub Čajka <jcajka@redhat.com> - 1.6-0.28git1b6d55a
- rebase to 1b6d55acab9199e09f9134ff3ac359647767f741

* Tue Jan 19 2016 Jakub Čajka <jcajka@redhat.com> - 1.6-0.27gitc7754c8
- rebase to c7754c8f54a1ace5fc0a8e36df809c713d2623d6

* Mon Jan 18 2016 Jakub Čajka <jcajka@redhat.com> - 1.6-0.26git01b8640
- rebase to 01b86400d94e3261f4163a9fc894596a4596571f

* Thu Jan 14 2016 Jakub Čajka <jcajka@redhat.com> - 1.6-0.25gitefd93a4
- rebase to efd93a412eb5941d767b70097e93a589747de34f

* Wed Jan 13 2016 Jakub Čajka <jcajka@redhat.com> - 1.6-0.24git771da53
- rebase to 771da53958618108c8ea56a69412eaeaae79e0ae

* Mon Jan 11 2016 Jakub Čajka <jcajka@redhat.com> - 1.6-0.23git109d54a
- rebase to 109d54a32d15b805769d4c05e78367f126a8d7f0

* Thu Jan 07 2016 Jakub Čajka <jcajka@redhat.com> - 1.6-0.22git305b4ba
- rebase to 305b4baf41ecbaa3469428b7debb389bd1527804
- mention Public Domain in License tag

* Wed Jan 06 2016 Jakub Čajka <jcajka@redhat.com> - 1.6-0.21git91f997b
- rebase to 91f997be723a0f88df0c42051f29c23ef90db0c5

* Tue Jan 05 2016 Jakub Čajka <jcajka@redhat.com> - 1.6-0.20git4b0bc7c
- rebase to 4b0bc7c3a14ac446bc13d22098de8db382205401

* Mon Jan 04 2016 Jakub Čajka <jcajka@redhat.com> - 1.6-0.19gite2093cd
- rebase to e2093cdeef8dcf0303ce3d8e79247c71ed53507d

* Tue Dec 15 2015 Jakub Čajka <jcajka@redhat.com> - 1.6-0.18git3540376
- rebase to 3540376b7067911fe1e02cb25e10b34ff789c630

* Mon Dec 14 2015 Jakub Čajka <jcajka@redhat.com> - 1.6-0.17git24a7955
- rebase to 24a7955c74e5617492c256bfad03904d6f169b10

* Fri Dec 11 2015 Jakub Čajka <jcajka@redhat.com> - 1.6-0.16git8545ea9
- rebase to 8545ea9cee087fd0fbac41bba7616d2fc4f2bc19

* Thu Dec 10 2015 Jakub Čajka <jcajka@redhat.com> - 1.6-0.15gite05b48e
- rebase to e05b48e22c3cc4ad334fdd9542bb9a69370cf79a

* Wed Dec 09 2015 Jakub Čajka <jcajka@redhat.com> - 1.6-0.14git9a89ac3
- rebase to 9a89ac35fe5d5dfaed307544b5cc290bd821dea1

* Tue Dec 08 2015 Jakub Čajka <jcajka@redhat.com> - 1.6-0.13gitaa487e6
- rebase to aa487e66f869785837275ee20441a53888a51bb2

* Mon Dec 07 2015 Jakub Čajka <jcajka@redhat.com> - 1.6-0.12git84a875c
- rebase to 84a875caa6de1b404dad596b1b6949e436168c76

* Fri Dec 04 2015 Jakub Čajka <jcajka@redhat.com> - 1.6-0.11git8854bdb
- rebase to 8854bdbd76d66a39b35980cee6643b4d4bd48fd4

* Wed Dec 02 2015 Jakub Čajka <jcajka@redhat.com> - 1.6-0.10git0ea1c1f
- rebase to 0ea1c1f6715c6fe33c38b6292ce2bdccaa86f0e2

* Tue Dec 01 2015 Jakub Čajka <jcajka@redhat.com> - 1.6-0.9gitf000523
- rebase to f000523018e80471f51e29cae117831157d8dfb8

* Fri Nov 27 2015 Jakub Čajka <jcajka@redhat.com> - 1.6-0.8git98abf29
- rebase to 98abf2937e42d560f0a8ba3c9e5bd5351c5316e6

* Thu Nov 26 2015 Jakub Čajka <jcajka@redhat.com> - 1.6-0.7git21efa7b
- rebase to 21efa7b2bc872958bcb252f5ab4dc52b2b0abeae
- removed go1.5beta2-disable-TestCloneNEWUSERAndRemapNoRootDisableSetgroups.patch
- make check 'more' verbose

* Wed Nov 25 2015 Jakub Čajka <jcajka@redhat.com> - 1.6-0.6gite5956bc
- rebase to e5956bca418bb8528509665ae753eada2024b9e3

* Tue Nov 24 2015 Jakub Čajka <jcajka@redhat.com> - 1.6-0.5gitc28a8e4
- rebase to c28a8e4553fed920425c6c9cb32d20f2da2f7a9a
- enable shared build on i686

* Mon Nov 23 2015 Jakub Čajka <jcajka@redhat.com> - 1.6-0.4git0417872
- rebase to 041787280976d0bad15c646fc7c7bbfef76d7ee5
- use golang as bootstrap compiler on ppc64le

* Thu Nov 19 2015 Jakub Čajka <jcajka@redhat.com> - 1.6-0.3gitaae81d9
- rebase to aae81d948cb7b4fb6e55b96cbba6ae2131d46e25
- minor spec tweak

* Mon Nov 16 2015 Jakub Čajka <jcajka@redhat.com> - 1.6-0.2git25a28da
- EPEL support

* Mon Nov 16 2015 Jakub Čajka <jcajka@redhat.com> - 1.6-0.1git25a28da
- rebase to 25a28da0807f3fa85588fb219f6fa40314bde675

* Fri Nov 13 2015 Jakub Čajka <jcajka@redhat.com> - 1.6-0.git3073797
- rebase to upstream master branch commit 3073797c37e168f3671880c683a228f9f8f942e3

* Tue Nov 03 2015 Jakub Čajka <jcajka@redhat.com> - 1.5.1-2
- spec file clean up
- added build options
- added powerpc build support

* Mon Oct 19 2015 Vincent Batts <vbatts@fedoraproject.org> - 1.5.1-1
- bz1271709 include patch from upstream fix

* Wed Sep 09 2015 Vincent Batts <vbatts@fedoraproject.org> - 1.5.1-0
- update to go1.5.1

* Fri Sep 04 2015 Vincent Batts <vbatts@fedoraproject.org> - 1.5-8
- bz1258166 remove srpm macros, for go-srpm-macros

* Thu Sep 03 2015 Vincent Batts <vbatts@fedoraproject.org> - 1.5-7
- bz1258166 remove srpm macros, for go-srpm-macros

* Thu Aug 27 2015 Vincent Batts <vbatts@fedoraproject.org> - 1.5-6
- starting a shared object subpackage. This will be x86_64 only until upstream supports more arches shared objects.

* Thu Aug 27 2015 Vincent Batts <vbatts@fedoraproject.org> - 1.5-5
- bz991759 gdb path fix

* Wed Aug 26 2015 Vincent Batts <vbatts@fedoraproject.org> - 1.5-4
- disable shared object until linux/386 is ironned out
- including the test/ directory for tests

* Tue Aug 25 2015 Vincent Batts <vbatts@fedoraproject.org> - 1.5-3
- bz1256910 only allow the golang zoneinfo.zip to be used in tests
- bz1166611 add golang.org/x directory
- bz1256525 include stdlib shared object. This will let other libraries and binaries
  build with `go build -buildmode=shared -linkshared ...` or similar.

* Sun Aug 23 2015 Peter Robinson <pbrobinson@fedoraproject.org> 1.5-2
- Enable aarch64
- Minor cleanups

* Thu Aug 20 2015 Vincent Batts <vbatts@fedoraproject.org> - 1.5-1
- updating to go1.5

* Thu Aug 06 2015 Vincent Batts <vbatts@fedoraproject.org> - 1.5-0.11.rc1
- fixing the sources reference

* Thu Aug 06 2015 Vincent Batts <vbatts@fedoraproject.org> - 1.5-0.10.rc1
- updating to go1.5rc1
- checks are back in place

* Tue Aug 04 2015 Vincent Batts <vbatts@fedoraproject.org> - 1.5-0.9.beta3
- pull in upstream archive/tar fix

* Thu Jul 30 2015 Vincent Batts <vbatts@fedoraproject.org> - 1.5-0.8.beta3
- updating to go1.5beta3

* Thu Jul 30 2015 Vincent Batts <vbatts@fedoraproject.org> - 1.5-0.7.beta2
- add the patch ..

* Thu Jul 30 2015 Vincent Batts <vbatts@fedoraproject.org> - 1.5-0.6.beta2
- increase ELFRESERVE (bz1248071)

* Tue Jul 28 2015 Lokesh Mandvekar <lsm5@fedoraproject.org> - 1.5-0.5.beta2
- correct package version and release tags as per naming guidelines

* Fri Jul 17 2015 Vincent Batts <vbatts@fedoraproject.org> - 1.4.99-4.1.5beta2
- adding test output, for visibility

* Fri Jul 10 2015 Vincent Batts <vbatts@fedoraproject.org> - 1.4.99-3.1.5beta2
- updating to go1.5beta2

* Fri Jul 10 2015 Vincent Batts <vbatts@fedoraproject.org> - 1.4.99-2.1.5beta1
- add checksum to sources and fixed one patch

* Fri Jul 10 2015 Vincent Batts <vbatts@fedoraproject.org> - 1.4.99-1.1.5beta1
- updating to go1.5beta1

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.4.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Wed Mar 18 2015 Vincent Batts <vbatts@fedoraproject.org> - 1.4.2-2
- obsoleting deprecated packages

* Wed Feb 18 2015 Vincent Batts <vbatts@fedoraproject.org> - 1.4.2-1
- updating to go1.4.2

* Fri Jan 16 2015 Vincent Batts <vbatts@fedoraproject.org> - 1.4.1-1
- updating to go1.4.1

* Fri Jan 02 2015 Vincent Batts <vbatts@fedoraproject.org> - 1.4-2
- doc organizing

* Thu Dec 11 2014 Vincent Batts <vbatts@fedoraproject.org> - 1.4-1
- update to go1.4 release

* Wed Dec 03 2014 Vincent Batts <vbatts@fedoraproject.org> - 1.3.99-3.1.4rc2
- update to go1.4rc2

* Mon Nov 17 2014 Vincent Batts <vbatts@fedoraproject.org> - 1.3.99-2.1.4rc1
- update to go1.4rc1

* Thu Oct 30 2014 Vincent Batts <vbatts@fedoraproject.org> - 1.3.99-1.1.4beta1
- update to go1.4beta1

* Thu Oct 30 2014 Vincent Batts <vbatts@fedoraproject.org> - 1.3.3-3
- macros will need to be in their own rpm

* Fri Oct 24 2014 Vincent Batts <vbatts@fedoraproject.org> - 1.3.3-2
- split out rpm macros (bz1156129)
- progress on gccgo accomodation

* Wed Oct 01 2014 Vincent Batts <vbatts@fedoraproject.org> - 1.3.3-1
- update to go1.3.3 (bz1146882)

* Mon Sep 29 2014 Vincent Batts <vbatts@fedoraproject.org> - 1.3.2-1
- update to go1.3.2 (bz1147324)

* Thu Sep 11 2014 Vincent Batts <vbatts@fedoraproject.org> - 1.3.1-3
- patching the tzinfo failure

* Sat Aug 16 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.3.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Wed Aug 13 2014 Vincent Batts <vbatts@fedoraproject.org> - 1.3.1-1
- update to go1.3.1

* Wed Aug 13 2014 Vincent Batts <vbatts@fedoraproject.org> - 1.3-11
- merged a line wrong

* Wed Aug 13 2014 Vincent Batts <vbatts@fedoraproject.org> - 1.3-10
- more work to get cgo.a timestamps to line up, due to build-env
- explicitly list all the files and directories for the source and packages trees
- touch all the built archives to be the same

* Mon Aug 11 2014 Vincent Batts <vbatts@fedoraproject.org> - 1.3-9
- make golang-src 'noarch' again, since that was not a fix, and takes up more space

* Mon Aug 11 2014 Vincent Batts <vbatts@fedoraproject.org> - 1.3-8
- update timestamps of source files during %%install bz1099206

* Fri Aug 08 2014 Vincent Batts <vbatts@fedoraproject.org> - 1.3-7
- update timestamps of source during %%install bz1099206

* Wed Aug 06 2014 Vincent Batts <vbatts@fedoraproject.org> - 1.3-6
- make the source subpackage arch'ed, instead of noarch

* Mon Jul 21 2014 Vincent Batts <vbatts@fedoraproject.org> - 1.3-5
- fix the writing of pax headers

* Tue Jul 15 2014 Vincent Batts <vbatts@fedoraproject.org> - 1.3-4
- fix the loading of gdb safe-path. bz981356

* Tue Jul 08 2014 Vincent Batts <vbatts@fedoraproject.org> - 1.3-3
- `go install std` requires gcc, to build cgo. bz1105901, bz1101508

* Mon Jul 07 2014 Vincent Batts <vbatts@fedoraproject.org> - 1.3-2
- archive/tar memory allocation improvements

* Thu Jun 19 2014 Vincent Batts <vbatts@fedoraproject.org> - 1.3-1
- update to go1.3

* Fri Jun 13 2014 Vincent Batts <vbatts@fedoraproject.org> - 1.3rc2-1
- update to go1.3rc2

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.3rc1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Tue Jun 03 2014 Vincent Batts <vbatts@redhat.com> 1.3rc1-1
- update to go1.3rc1
- new arch file shuffling

* Wed May 21 2014 Vincent Batts <vbatts@redhat.com> 1.3beta2-1
- update to go1.3beta2
- no longer provides go-mode for xemacs (emacs only)

* Wed May 21 2014 Vincent Batts <vbatts@redhat.com> 1.2.2-7
- bz1099206 ghost files are not what is needed

* Tue May 20 2014 Vincent Batts <vbatts@redhat.com> 1.2.2-6
- bz1099206 more fixing. The packages %%post need golang-bin present first

* Tue May 20 2014 Vincent Batts <vbatts@redhat.com> 1.2.2-5
- bz1099206 more fixing. Let go fix its own timestamps and freshness

* Tue May 20 2014 Vincent Batts <vbatts@redhat.com> 1.2.2-4
- fix the existence and alternatives of `go` and `gofmt`

* Mon May 19 2014 Vincent Batts <vbatts@redhat.com> 1.2.2-3
- bz1099206 fix timestamp issue caused by koji builders

* Fri May 09 2014 Vincent Batts <vbatts@redhat.com> 1.2.2-2
- more arch file shuffling

* Fri May 09 2014 Vincent Batts <vbatts@redhat.com> 1.2.2-1
- update to go1.2.2

* Thu May 08 2014 Vincent Batts <vbatts@redhat.com> 1.2.1-8
- RHEL6 rpm macros can't %%exlude missing files

* Wed May 07 2014 Vincent Batts <vbatts@redhat.com> 1.2.1-7
- missed two arch-dependent src files

* Wed May 07 2014 Vincent Batts <vbatts@redhat.com> 1.2.1-6
- put generated arch-dependent src in their respective RPMs

* Fri Apr 11 2014 Vincent Batts <vbatts@redhat.com> 1.2.1-5
- skip test that is causing a SIGABRT on fc21 bz1086900

* Thu Apr 10 2014 Vincent Batts <vbatts@fedoraproject.org> 1.2.1-4
- fixing file and directory ownership bz1010713

* Wed Apr 09 2014 Vincent Batts <vbatts@fedoraproject.org> 1.2.1-3
- including more to macros (%%go_arches)
- set a standard goroot as /usr/lib/golang, regardless of arch
- include sub-packages for compiler toolchains, for all golang supported architectures

* Wed Mar 26 2014 Vincent Batts <vbatts@fedoraproject.org> 1.2.1-2
- provide a system rpm macros. Starting with %gopath

* Tue Mar 04 2014 Adam Miller <maxamillion@fedoraproject.org> 1.2.1-1
- Update to latest upstream

* Thu Feb 20 2014 Adam Miller <maxamillion@fedoraproject.org> 1.2-7
- Remove  _BSD_SOURCE and _SVID_SOURCE, they are deprecated in recent
  versions of glibc and aren't needed

* Wed Feb 19 2014 Adam Miller <maxamillion@fedoraproject.org> 1.2-6
- pull in upstream archive/tar implementation that supports xattr for
  docker 0.8.1

* Tue Feb 18 2014 Vincent Batts <vbatts@redhat.com> 1.2-5
- provide 'go', so users can yum install 'go'

* Fri Jan 24 2014 Vincent Batts <vbatts@redhat.com> 1.2-4
- skip a flaky test that is sporadically failing on the build server

* Thu Jan 16 2014 Vincent Batts <vbatts@redhat.com> 1.2-3
- remove golang-godoc dependency. cyclic dependency on compiling godoc

* Wed Dec 18 2013 Vincent Batts <vbatts@redhat.com> - 1.2-2
- removing P224 ECC curve

* Mon Dec 2 2013 Vincent Batts <vbatts@fedoraproject.org> - 1.2-1
- Update to upstream 1.2 release
- remove the pax tar patches

* Tue Nov 26 2013 Vincent Batts <vbatts@redhat.com> - 1.1.2-8
- fix the rpmspec conditional for rhel and fedora

* Thu Nov 21 2013 Vincent Batts <vbatts@redhat.com> - 1.1.2-7
- patch tests for testing on rawhide
- let the same spec work for rhel and fedora

* Wed Nov 20 2013 Vincent Batts <vbatts@redhat.com> - 1.1.2-6
- don't symlink /usr/bin out to ../lib..., move the file
- seperate out godoc, to accomodate the go.tools godoc

* Fri Sep 20 2013 Adam Miller <maxamillion@fedoraproject.org> - 1.1.2-5
- Pull upstream patches for BZ#1010271
- Add glibc requirement that got dropped because of meta dep fix

* Fri Aug 30 2013 Adam Miller <maxamillion@fedoraproject.org> - 1.1.2-4
- fix the libc meta dependency (thanks to vbatts [at] redhat.com for the fix)

* Tue Aug 27 2013 Adam Miller <maxamillion@fedoraproject.org> - 1.1.2-3
- Revert incorrect merged changelog

* Tue Aug 27 2013 Adam Miller <maxamillion@fedoraproject.org> - 1.1.2-2
- This was reverted, just a placeholder changelog entry for bad merge

* Tue Aug 20 2013 Adam Miller <maxamillion@fedoraproject.org> - 1.1.2-1
- Update to latest upstream

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.1.1-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Wed Jul 17 2013 Petr Pisar <ppisar@redhat.com> - 1.1.1-6
- Perl 5.18 rebuild

* Wed Jul 10 2013 Adam Goode <adam@spicenitz.org> - 1.1.1-5
- Blacklist testdata files from prelink
- Again try to fix #973842

* Fri Jul  5 2013 Adam Goode <adam@spicenitz.org> - 1.1.1-4
- Move src to libdir for now (#973842) (upstream issue https://code.google.com/p/go/issues/detail?id=5830)
- Eliminate noarch data package to work around RPM bug (#975909)
- Try to add runtime-gdb.py to the gdb safe-path (#981356)

* Wed Jun 19 2013 Adam Goode <adam@spicenitz.org> - 1.1.1-3
- Use lua for pretrans (http://fedoraproject.org/wiki/Packaging:Guidelines#The_.25pretrans_scriptlet)

* Mon Jun 17 2013 Adam Goode <adam@spicenitz.org> - 1.1.1-2
- Hopefully really fix #973842
- Fix update from pre-1.1.1 (#974840)

* Thu Jun 13 2013 Adam Goode <adam@spicenitz.org> - 1.1.1-1
- Update to 1.1.1
- Fix basically useless package (#973842)

* Sat May 25 2013 Dan Horák <dan[at]danny.cz> - 1.1-3
- set ExclusiveArch

* Fri May 24 2013 Adam Goode <adam@spicenitz.org> - 1.1-2
- Fix noarch package discrepancies

* Fri May 24 2013 Adam Goode <adam@spicenitz.org> - 1.1-1
- Initial Fedora release.
- Update to 1.1

* Thu May  9 2013 Adam Goode <adam@spicenitz.org> - 1.1-0.3.rc3
- Update to rc3

* Thu Apr 11 2013 Adam Goode <adam@spicenitz.org> - 1.1-0.2.beta2
- Update to beta2

* Tue Apr  9 2013 Adam Goode <adam@spicenitz.org> - 1.1-0.1.beta1
- Initial packaging.
