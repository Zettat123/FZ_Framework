#include <linux/cdev.h>
#include <linux/ctype.h>
#include <linux/delay.h>
#include <linux/device.h>
#include <linux/fs.h>
#include <linux/gpio.h>
#include <linux/io.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/uaccess.h>

#define FZ_DEV_CLASS "FZ_G_DHT11_CLASS"
#define DEVICE_NAME "fz_g_dht11"

#define SUCCESS 0
#define MSG_BUF_LEN 1024

#define GPIO_DIRECTION_INPUT 0
#define GPIO_DIRECTION_OUTPUT 1
#define GPIO_VALUE_LOW 0
#define GPIO_VALUE_HIGH 1
#define GPIO_CMD_CHANGE_MODE 0
#define GPIO_CMD_SET_VALUE 1
#define MAXCNT 100000

int init_module(void);
void cleanup_module(void);
static int device_open(struct inode *, struct file *);
static int device_release(struct inode *, struct file *);
static ssize_t device_read(struct file *, char *, size_t, loff_t *);
static ssize_t device_write(struct file *, const char *, size_t, loff_t *);
int change_pin_mode(const int, const int);
void change_pin_value(const int, const int);
int read_dht11(void);

static int Major = 0, Minor = 0;
static dev_t devno;
static struct class *cls;
static struct device *dev;

static int Device_Open = 0;
static char msg[MSG_BUF_LEN];
static char *msg_Ptr;

static int bits[50];
static char data[10];

static int pin = 17;
module_param(pin, int, 0);
static int threshold = 50;
module_param(threshold, int, 0);

static struct file_operations fops = {.read = device_read,
                                      .write = device_write,
                                      .open = device_open,
                                      .release = device_release};

int change_pin_mode(const int gpio_num, const int gpio_mode) {
  switch (gpio_mode) {
    case GPIO_DIRECTION_INPUT:
      return gpio_direction_input(gpio_num);

    case GPIO_DIRECTION_OUTPUT:
      return gpio_direction_output(gpio_num, 0);

    default:
      return -1;
  }
}

void change_pin_value(const int gpio_num, const int gpio_value) {
  gpio_set_value(gpio_num, gpio_value);
}

int read_dht11() {
  int cnt = 0, i;
  for (i = 0; i < 10; i++) data[i] = 0;
  change_pin_mode(pin, GPIO_DIRECTION_OUTPUT);

  change_pin_value(pin, GPIO_VALUE_LOW);
  mdelay(20);
  change_pin_value(pin, GPIO_VALUE_HIGH);
  udelay(40);
  change_pin_mode(pin, GPIO_DIRECTION_INPUT);

  cnt = 0;
  while (gpio_get_value(pin) == GPIO_VALUE_LOW) {
    cnt++;
    if (cnt > MAXCNT) {
      printk("DHT11 Non Responsive\n");
      return -1;
    }
  }

  cnt = 0;
  while (gpio_get_value(pin) == GPIO_VALUE_HIGH) {
    cnt++;
    if (cnt > MAXCNT) {
      printk("DHT11 Non Responsive\n");
      return -1;
    }
  }

  // 40bits data start
  for (i = 0; i < 40; i++) {
    while (gpio_get_value(pin) == GPIO_VALUE_LOW) {
    }
    cnt = 0;
    while (gpio_get_value(pin) == GPIO_VALUE_HIGH) {
      cnt++;
      if (cnt > MAXCNT) {
        break;
      }
    }

    if (cnt > MAXCNT) {
      break;
      return -1;
    }

    bits[i] = cnt;
  }

  // transform bit to int
  for (i = 0; i < 40; ++i) {
    data[i / 8] <<= 1;
    if (bits[i] > threshold) {
      data[i / 8] |= 1;
    }
  }

  return 0;
}

int init_module(void) {
  Major = register_chrdev(0, DEVICE_NAME, &fops);
  devno = MKDEV(Major, Minor);
  cls = class_create(THIS_MODULE, FZ_DEV_CLASS);

  if (IS_ERR(cls)) {
    unregister_chrdev(Major, DEVICE_NAME);
    return -EBUSY;
  }

  dev = device_create(cls, NULL, devno, NULL, DEVICE_NAME);

  if (IS_ERR(dev)) {
    class_destroy(cls);
    unregister_chrdev(Major, DEVICE_NAME);
    return -EBUSY;
  }

  printk(KERN_INFO "%s Installed!", DEVICE_NAME);

  return SUCCESS;
}

void cleanup_module(void) {
  printk(KERN_INFO "%s Uninstalled!", DEVICE_NAME);
  device_destroy(cls, devno);
  class_destroy(cls);
  unregister_chrdev(Major, DEVICE_NAME);
}

static int device_open(struct inode *inode, struct file *file) {
  if (Device_Open) return -EBUSY;
  Device_Open++;

  sprintf(msg, "file opened %d", Device_Open);
  msg_Ptr = msg;

  try_module_get(THIS_MODULE);

  return SUCCESS;
}

static int device_release(struct inode *inode, struct file *file) {
  Device_Open--;

  module_put(THIS_MODULE);

  return SUCCESS;
}

static ssize_t device_read(struct file *filp, char *buffer, size_t length,
                           loff_t *offset) {
  int bytes_read = 0;

  if (read_dht11() == 0) {
    while (bytes_read < length) {
      put_user(data[bytes_read], buffer++);
      bytes_read++;
    }
  }

  return bytes_read;
}

static ssize_t device_write(struct file *filp, const char *buff, size_t len,
                            loff_t *off) {
  return 0;
}

MODULE_LICENSE("GPL");
