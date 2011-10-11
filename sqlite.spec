# bcond default logic is nicely backwards...
%bcond_without tcl
%bcond_with static
%bcond_without check

%define realver 3070603
%define docver 3070600
%define rpmver %(echo %{realver}|sed -e "s/00//g" -e "s/0/./g")

Summary: Library that implements an embeddable SQL database engine
Name: sqlite
Version: %{rpmver}
Release: 1.el6.R
License: Public Domain
Group: Applications/Databases
URL: http://www.sqlite.org/
Source0: http://www.sqlite.org/sqlite-src-%{realver}.zip
Source1: http://www.sqlite.org/sqlite-doc-%{docver}.zip
# Fix build with --enable-load-extension, upstream ticket #3137
Patch1: sqlite-3.6.12-libdl.patch
# Support a system-wide lemon template
Patch2: sqlite-3.6.23-lemon-system-template.patch
# Fixup test-suite expectations wrt SQLITE_DISABLE_DIRSYNC 
Patch3: sqlite-3.7.4-wal2-nodirsync.patch
# Shut up stupid tests depending on system settings of allowed open fd's
Patch4: sqlite-3.7.6-stupid-openfiles-test.patch
BuildRequires: ncurses-devel readline-devel glibc-devel
# libdl patch needs
BuildRequires: autoconf
%if %{with tcl}
BuildRequires: /usr/bin/tclsh
BuildRequires: tcl-devel
%{!?tcl_version: %global tcl_version 8.5}
%{!?tcl_sitearch: %global tcl_sitearch %{_libdir}/tcl%{tcl_version}}
%endif
BuildRoot: %{_tmppath}/%{name}-root

%description
SQLite is a C library that implements an SQL database engine. A large
subset of SQL92 is supported. A complete database is stored in a
single disk file. The API is designed for convenience and ease of use.
Applications that link against SQLite can enjoy the power and
flexibility of an SQL database without the administrative hassles of
supporting a separate database server.  Version 2 and version 3 binaries
are named to permit each to be installed on a single host

%package devel
Summary: Development tools for the sqlite3 embeddable SQL database engine
Group: Development/Libraries
Requires: %{name} = %{version}-%{release}
Requires: pkgconfig

%description devel
This package contains the header files and development documentation 
for %{name}. If you like to develop programs using %{name}, you will need 
to install %{name}-devel.

%package doc
Summary: Documentation for sqlite
Group: Documentation
BuildArch: noarch

%description doc
This package contains most of the static HTML files that comprise the
www.sqlite.org website, including all of the SQL Syntax and the 
C/C++ interface specs and other miscellaneous documentation.

%package -n lemon
Summary: A parser generator
Group: Development/Tools

%description -n lemon
Lemon is an LALR(1) parser generator for C or C++. It does the same
job as bison and yacc. But lemon is not another bison or yacc
clone. It uses a different grammar syntax which is designed to reduce
the number of coding errors. Lemon also uses a more sophisticated
parsing engine that is faster than yacc and bison and which is both
reentrant and thread-safe. Furthermore, Lemon implements features
that can be used to eliminate resource leaks, making is suitable for
use in long-running programs such as graphical user interfaces or
embedded controllers.

%if %{with tcl}
%package tcl
Summary: Tcl module for the sqlite3 embeddable SQL database engine
Group: Development/Languages
Requires: %{name} = %{version}-%{release}
Requires: tcl(abi) = %{tcl_version}

%description tcl
This package contains the tcl modules for %{name}.
%endif

%prep
%setup -q -a1 -n %{name}-src-%{realver}
%patch1 -p1 -b .libdl
%patch2 -p1 -b .lemon-system-template
%patch3 -p1 -b .wal2-nodirsync
%patch4 -p1 -b .stupid-openfiles-test

# Remove cgi-script erroneously included in sqlite-doc-3070500
rm -f %{name}-doc-%{realver}/search

%build
autoconf
export CFLAGS="$RPM_OPT_FLAGS -DSQLITE_ENABLE_COLUMN_METADATA=1 -DSQLITE_DISABLE_DIRSYNC=1 -DSQLITE_ENABLE_FTS3=3 -DSQLITE_ENABLE_RTREE=1 -DSQLITE_SECURE_DELETE=1 -DSQLITE_ENABLE_UNLOCK_NOTIFY=1 -Wall -fno-strict-aliasing"
%configure %{!?with_tcl:--disable-tcl} \
           --enable-threadsafe \
           --enable-threads-override-locks \
           --enable-load-extension \
           %{?with_tcl:TCLLIBDIR=%{tcl_sitearch}/sqlite3}

# rpath removal
sed -i 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g' libtool
sed -i 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' libtool

make %{?_smp_mflags}

%install
rm -rf $RPM_BUILD_ROOT

make DESTDIR=${RPM_BUILD_ROOT} install

install -D -m0644 sqlite3.1 $RPM_BUILD_ROOT/%{_mandir}/man1/sqlite3.1
install -D -m0755 lemon $RPM_BUILD_ROOT/%{_bindir}/lemon
install -D -m0644 tool/lempar.c $RPM_BUILD_ROOT/%{_datadir}/lemon/lempar.c

%if %{with tcl}
# fix up permissions to enable dep extraction
chmod 0755 ${RPM_BUILD_ROOT}/%{tcl_sitearch}/sqlite3/*.so
%endif

%if ! %{with static}
rm -f $RPM_BUILD_ROOT/%{_libdir}/*.{la,a}
%endif

%if %{with check}
%check
%ifarch s390 s390x ppc ppc64 %{sparc} %{arm}
make test || :
%else
make test
%endif
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%files
%defattr(-, root, root)
%doc README
%{_bindir}/sqlite3
%{_libdir}/*.so.*
%{_mandir}/man?/*

%files devel
%defattr(-, root, root)
%{_includedir}/*.h
%{_libdir}/*.so
%{_libdir}/pkgconfig/*.pc
%if %{with static}
%{_libdir}/*.a
%exclude %{_libdir}/*.la
%endif

%files doc
%defattr(-, root, root)
%doc %{name}-doc-%{docver}/*

%files -n lemon
%defattr(-, root, root)
%{_bindir}/lemon
%{_datadir}/lemon

%if %{with tcl}
%files tcl
%defattr(-, root, root)
%{tcl_sitearch}/sqlite3
%endif

%changelog
* Wed May 25 2011 Panu Matilainen <pmatilai@redhat.com> - 3.7.6.3-1.el6.R
- update to 3.7.6.3 (http://www.sqlite.org/releaselog/3_7_6_3.html)

* Sat May 21 2011 Peter Robinson <pbrobinson@gmail.com> - 3.7.6.2-3
- add arm to the exclude from tests list

* Fri Apr 29 2011 Panu Matilainen <pmatilai@redhat.com> - 3.7.6.2-2
- comment out stupid tests causing very bogus build failure on koji

* Thu Apr 21 2011 Panu Matilainen <pmatilai@redhat.com> - 3.7.6.2-1
- update to 3.7.6.2 (http://www.sqlite.org/releaselog/3_7_6_2.html)

* Fri Feb 25 2011 Dennis Gilmore <dennis@ausil.us> - 3.7.5-4
- build tests on sparc expecting failures same as the other big endian arches

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.7.5-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Wed Feb 2 2011 Panu Matilainen <pmatilai@redhat.com> - 3.7.5-2
- unwanted cgi-script in docs creating broken dependencies, remove it
- make doc sub-package noarch

* Tue Feb 1 2011 Panu Matilainen <pmatilai@redhat.com> - 3.7.5-1
- update to 3.7.5 (http://www.sqlite.org/releaselog/3_7_5.html)

* Thu Dec 9 2010 Panu Matilainen <pmatilai@redhat.com> - 3.7.4-1
- update to 3.7.4 (http://www.sqlite.org/releaselog/3_7_4.html)
- deal with upstream source naming, versioning and format changing
- fixup wal2-test expections wrt SQLITE_DISABLE_DIRSYNC use

* Fri Nov 5 2010 Dan Horák <dan[at]danny.cz> - 3.7.3-2
- expect test failures also on s390x

* Mon Nov 1 2010 Panu Matilainen <pmatilai@redhat.com> - 3.7.3-1
- update to 3.7.3 (http://www.sqlite.org/releaselog/3_7_3.html)

* Tue Sep  2 2010 Tom "spot" Callaway <tcallawa@redhat.com> - 3.7.0.1-2
- enable SQLITE_SECURE_DELETE, SQLITE_ENABLE_UNLOCK_NOTIFY for firefox 4

* Fri Aug 13 2010 Panu Matilainen <pmatilai@redhat.com> - 3.7.0.1-1
- update to 3.7.0.1 (http://www.sqlite.org/releaselog/3_7_0_1.html)

* Sat Jul  3 2010 Dan Horák <dan[at]danny.cz> - 3.6.23.1-2
- some tests are failing on s390 and ppc/ppc64 so don't fail the whole build there

* Mon Apr 19 2010 Panu Matilainen <pmatilai@redhat.com> - 3.6.23.1-1
- update to 3.6.23.1 (http://www.sqlite.org/releaselog/3_6_23_1.html)

* Wed Mar 10 2010 Panu Matilainen <pmatilai@redhat.com> - 3.6.23-1
- update to 3.6.23 (http://www.sqlite.org/releaselog/3_6_23.html)
- drop the lemon sprintf patch, upstream doesn't want it
- make test-suite errors fail build finally

* Mon Jan 18 2010 Panu Matilainen <pmatilai@redhat.com> - 3.6.22-1
- update to 3.6.22 (http://www.sqlite.org/releaselog/3_6_22.html)

* Tue Dec 08 2009 Panu Matilainen <pmatilai@redhat.com> - 3.6.21-1
- update to 3.6.21 (http://www.sqlite.org/releaselog/3_6_21.html)

* Tue Nov 17 2009 Panu Matilainen <pmatilai@redhat.com> - 3.6.20-1
- update to 3.6.20 (http://www.sqlite.org/releaselog/3_6_20.html)

* Tue Oct 06 2009 Panu Matilainen <pmatilai@redhat.com> - 3.6.18-1
- update to 3.6.18 (http://www.sqlite.org/releaselog/3_6_18.html)
- drop no longer needed test-disabler patches

* Fri Aug 21 2009 Panu Matilainen <pmatilai@redhat.com> - 3.6.17-1
- update to 3.6.17 (http://www.sqlite.org/releaselog/3_6_17.html)
- disable to failing tests until upstream fixes

* Sun Jul 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.6.14.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Fri Jun 12 2009 Panu Matilainen <pmatilai@redhat.com> - 3.6.14.2-1
- update to 3.6.14.2 (#505229)

* Mon May 18 2009 Panu Matilainen <pmatilai@redhat.com> - 3.6.14-2
- disable rpath
- add -doc subpackage instead of patching out reference to it

* Thu May 14 2009 Panu Matilainen <pmatilai@redhat.com> - 3.6.14-1
- update to 3.6.14 (http://www.sqlite.org/releaselog/3_6_14.html)
- merge-review cosmetics (#226429)
  - drop ancient sqlite3 obsoletes
  - fix tab vs space whitespace issues
  - remove commas from summaries
- fixup io-test fsync expectations wrt SQLITE_DISABLE_DIRSYNC

* Wed Apr 15 2009 Panu Matilainen <pmatilai@redhat.com> - 3.6.13-1
- update to 3.6.13

* Thu Apr 09 2009 Dennis Gilmore <dennis@ausil.us> - 3.6.12-3
- apply upstream patch for memory alignment issue (#494906)

* Tue Apr 07 2009 Panu Matilainen <pmatilai@redhat.com> - 3.6.12-2
- disable strict aliasing to work around brokenness on 3.6.12 (#494266)
- run test-suite on build but let it fail for now

* Fri Apr 03 2009 Panu Matilainen <pmatilai@redhat.com> - 3.6.12-1
- update to 3.6.12 (#492662)
- remove reference to non-existent sqlite-doc from manual (#488883)

* Wed Feb 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.6.10-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Wed Feb 04 2009 Panu Matilainen <pmatilai@redhat.com> - 3.6.10-3
- enable RTREE and FTS3 extensions (#481417)

* Thu Jan 22 2009 Panu Matilainen <pmatilai@redhat.com> - 3.6.10-2
- upstream fix yum breakage caused by new keywords (#481189)

* Thu Jan 22 2009 Panu Matilainen <pmatilai@redhat.com> - 3.6.10-1
- update to 3.6.10

* Wed Dec 31 2008 Panu Matilainen <pmatilai@redhat.com> - 3.6.7-1
- update to 3.6.7
- avoid lemon ending up in main sqlite package too

* Fri Dec 05 2008 Panu Matilainen <pmatilai@redhat.com> - 3.6.6.2-4
- add lemon subpackage

* Thu Dec  4 2008 Matthias Clasen <mclasen@redhat.com> - 3.6.6.2-3
- Rebuild for pkg-config provides 

* Tue Dec 02 2008 Panu Matilainen <pmatilai@redhat.com> - 3.6.6.2-2
- require tcl(abi) in sqlite-tcl subpackage (#474034)
- move tcl extensions to arch-specific location
- enable dependency extraction on the tcl dso
- require pkgconfig in sqlite-devel

* Sat Nov 29 2008 Panu Matilainen <pmatilai@redhat.com> - 3.6.6.2-1
- update to 3.6.6.2

* Sat Nov 08 2008 Panu Matilainen <pmatilai@redhat.com> - 3.6.4-1
- update to 3.6.4
- drop patches already upstream

* Mon Sep 22 2008 Panu Matilainen <pmatilai@redhat.com> - 3.5.9-2
- Remove references to temporary registers from cache on release (#463061)
- Enable loading of external extensions (#457433)

* Tue Jun 17 2008 Stepan Kasal <skasal@redhat.com> - 3.5.9-1
- update to 3.5.9

* Wed Apr 23 2008 Panu Matilainen <pmatilai@redhat.com> - 3.5.8-1
- update to 3.5.8
- provide full version in pkg-config (#443692)

* Mon Mar 31 2008 Panu Matilainen <pmatilai@redhat.com> - 3.5.6-2
- remove reference to static libs from -devel description (#439376)

* Tue Feb 12 2008 Panu Matilainen <pmatilai@redhat.com> - 3.5.6-1
- update to 3.5.6
- also fixes #432447

* Fri Jan 25 2008 Panu Matilainen <pmatilai@redhat.com> - 3.5.4-3
- enable column metadata API (#430258)

* Tue Jan 08 2008 Panu Matilainen <pmatilai@redhat.com> - 3.5.4-2
- avoid packaging CVS directory as documentation (#427755)

* Fri Dec 21 2007 Panu Matilainen <pmatilai@redhat.com> - 3.5.4-1
- Update to 3.5.4 (#413801)

* Fri Sep 28 2007 Panu Matilainen <pmatilai@redhat.com> - 3.4.2-3
- Add another build conditional for enabling %%check

* Fri Sep 28 2007 Panu Matilainen <pmatilai@redhat.com> - 3.4.2-2
- Use bconds for the spec build conditionals
- Enable -tcl subpackage again (#309041)

* Wed Aug 15 2007 Paul Nasrat <pnasrat@redhat.com> - 3.4.2-1
- Update to 3.4.2

* Sat Jul 21 2007 Paul Nasrat <pnasrat@redhat.com> - 3.4.1-1
- Update to 3.4.1

* Sun Jun 24 2007 Paul Nasrat <pnsarat@redhat.com> - 3.4.0-2
- Disable load for now (#245486)

* Tue Jun 19 2007 Paul Nasrat <pnasrat@redhat.com> - 3.4.0-1
- Update to 3.4.0

* Fri Jun 01 2007 Paul Nasrat <pnasrat@redhat.com> - 3.3.17-2
- Enable load 
- Build fts1 and fts2
- Don't sync on dirs (#237427)

* Tue May 29 2007 Paul Nasrat <pnasrat@redhat.com> - 3.3.17-1
- Update to 3.3.17

* Mon Mar 19 2007 Paul Nasrat <pnasrat@redhat.com> - 3.3.13-1
- Update to 3.3.13

* Fri Aug 11 2006 Paul Nasrat <pnasrat@redhat.com> - 3.3.6-2
- Fix conditional typo (patch from Gareth Armstrong)

* Wed Jul 12 2006 Jesse Keating <jkeating@redhat.com> - 3.3.6-1.1
- rebuild

* Mon Jun 26 2006 Paul Nasrat <pnasrat@redhat.com> - 3.3.6-1
- Update to 3.3.6
- Fix typo  (#189647)
- Enable threading fixes (#181298)
- Conditionalize static library

* Mon Apr 17 2006 Paul Nasrat <pnasrat@redhat.com> - 3.3.5-1
- Update to 3.3.5

* Fri Feb 10 2006 Jesse Keating <jkeating@redhat.com> - 3.3.3-1.2
- bump again for double-long bug on ppc(64)

* Tue Feb 07 2006 Jesse Keating <jkeating@redhat.com> - 3.3.3-1.1
- rebuilt for new gcc4.1 snapshot and glibc changes

* Tue Jan 31 2006 Christopher Aillon <caillon@redhat.com> - 3.3.3-1
- Update to 3.3.3

* Tue Jan 31 2006 Christopher Aillon <caillon@redhat.com> - 3.3.2-1
- Update to 3.3.2

* Tue Jan 24 2006 Paul Nasrat <pnasrat@redhat.com> - 3.2.8-1
- Add --enable-threadsafe (Nicholas Miell)
- Update to 3.2.8

* Fri Dec 09 2005 Jesse Keating <jkeating@redhat.com>
- rebuilt

* Tue Oct  4 2005 Jeremy Katz <katzj@redhat.com> - 3.2.7-2
- no more static file or libtool archive (#169874) 

* Wed Sep 28 2005 Florian La Roche <laroche@redhat.com>
- Upgrade to 3.2.7 release.

* Thu Sep 22 2005 Florian La Roche <laroche@redhat.com>
- Upgrade to 3.2.6 release.

* Sun Sep 11 2005 Florian La Roche <laroche@redhat.com>
- Upgrade to 3.2.5 release.

* Fri Jul  8 2005 Roland McGrath <roland@redhat.com> - 3.2.2-1
- Upgrade to 3.2.2 release.

* Sat Apr  9 2005 Warren Togami <wtogami@redhat.com> - 3.1.2-3
- fix buildreqs (#154298)

* Mon Apr  4 2005 Jeremy Katz <katzj@redhat.com> - 3.1.2-2
- disable tcl subpackage

* Wed Mar  9 2005 Jeff Johnson <jbj@redhat.com> 3.1.2-1
- rename to "sqlite" from "sqlite3" (#149719, #150012).

* Wed Feb 16 2005 Jeff Johnson <jbj@jbj.org> 3.1.2-1
- upgrade to 3.1.2.
- add sqlite3-tcl sub-package.

* Sat Feb  5 2005 Jeff Johnson <jbj@jbj.org> 3.0.8-3
- repackage for fc4.

* Mon Jan 17 2005 R P Herrold <info@owlriver.com> 3.0.8-2orc
- fix a man page nameing conflict when co-installed with sqlite-2, as
  is permissible
