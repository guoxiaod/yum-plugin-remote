

NAME=$(shell /bin/awk '/^[Nn]ame/{print $$2; exit;}' *.spec)
VERSION=$(shell /bin/awk '/^[Vv]ersion/{print $$2; exit;}' *.spec)

FILES=ChangeLog  LICENSE  README  remote.conf  remote.py
RPMBUILD_ROOT=/root/rpmbuild/
ARCH=noarch


build:
	/bin/mkdir -p ${NAME}-${VERSION}
	/bin/cp ${FILES} ${NAME}-${VERSION}
	/bin/tar -czf ${NAME}-${VERSION}.tar.gz ${NAME}-${VERSION}
	sudo cp -r ${NAME}-${VERSION}.tar.gz ${RPMBUILD_ROOT}/SOURCES/
	sudo rpmbuild -bb ${NAME}.spec
	cp -r ${RPMBUILD_ROOT}/RPMS/noarch/${NAME}-${VERSION}*.rpm .
	/bin/rm -rf ${NAME}-${VERSION}
	/bin/rm -rf ${NAME}-${VERSION}.tar.gz

install:
	sudo rpm -ivh --force ${NAME}-${VERSION}*.rpm

test:
	./test.py

clean:
	rm -rf *.tar.gz
	rm -rf *.rpm
