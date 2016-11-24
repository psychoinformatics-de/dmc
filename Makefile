BASEDIR=$(CURDIR)
PRIVDIR=$(BASEDIR)/private
PUBDIR=$(BASEDIR)/public
OUTPUTDIR=$(BASEDIR)/output

SSH_HOST=kumo.ovgu.de
SSH_PORT=22
SSH_USER=
SSH_TARGET_DIR=/var/www/howdoyouscience


help:
	@echo 'She blinded me with Makefile!                                             '
	@echo '                                                                          '
	@echo 'Usage:                                                                    '
	@echo '   make html                           (re)generate the web site          '
	@echo '   make clean                          remove the generated files         '
	@echo '   make records                        create the base records directories'
	@echo '   make rsync_upload                   upload the web site via rsync+ssh  '
	@echo '                                                                          '

html: records
	[ -d $(OUTPUTDIR) ] || mkdir -p $(OUTPUTDIR)
	rsync -r --delete $(BASEDIR)/www/ $(OUTPUTDIR)/www
	rsync -r --delete $(BASEDIR)/server/ $(OUTPUTDIR)/server
	rsync -r --delete $(BASEDIR)/stats/ $(OUTPUTDIR)/stats
	rsync -r $(BASEDIR)/records/ $(OUTPUTDIR)/records

clean:
	[ -d $(OUTPUTDIR) ] && rm -rf $(OUTPUTDIR)

records:
	[ -d $(PRIVDIR) ] || mkdir -p $(PRIVDIR)
	[ -d $(PUBDIR) ] || mkdir -p $(PUBDIR)

rsync_upload: html
ifdef SSH_USER
	rsync -e "ssh -p $(SSH_PORT)" -rv --delete $(OUTPUTDIR)/www/ $(SSH_USER)@$(SSH_HOST):$(SSH_TARGET_DIR)/www
	rsync -e "ssh -p $(SSH_PORT)" -rv --delete $(OUTPUTDIR)/server/ $(SSH_USER)@$(SSH_HOST):$(SSH_TARGET_DIR)/server
	rsync -e "ssh -p $(SSH_PORT)" -rv --delete $(OUTPUTDIR)/stats/ $(SSH_USER)@$(SSH_HOST):$(SSH_TARGET_DIR)/stats
	rsync -e "ssh -p $(SSH_PORT)" -rv $(OUTPUTDIR)/records/ $(SSH_USER)@$(SSH_HOST):$(SSH_TARGET_DIR)/records
else
	rsync -e "ssh -p $(SSH_PORT)" -rv --delete $(OUTPUTDIR)/www/ $(SSH_HOST):$(SSH_TARGET_DIR)/www
	rsync -e "ssh -p $(SSH_PORT)" -rv --delete $(OUTPUTDIR)/server/ $(SSH_HOST):$(SSH_TARGET_DIR)/server
	rsync -e "ssh -p $(SSH_PORT)" -rv --delete $(OUTPUTDIR)/stats/ $(SSH_HOST):$(SSH_TARGET_DIR)/stats
	rsync -e "ssh -p $(SSH_PORT)" -rv $(OUTPUTDIR)/records/ $(SSH_HOST):$(SSH_TARGET_DIR)/records
endif

.PHONY: help html clean rsync_upload
