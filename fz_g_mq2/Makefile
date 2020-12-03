PWD=$(shell pwd)
obj-m := fz_g_mq2.o

all:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules
clean:  
	rm -rf *.o *.ko *.mod.c .*.cmd *.markers *.order *.symvers .tmp_versions .cache.mk