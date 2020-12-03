#include <linux/cdev.h>
#include <linux/ctype.h>
#include <linux/device.h>
#include <linux/fs.h>
#include <linux/gpio.h>
#include <linux/io.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/uaccess.h>

#define FZ_DEV_CLASS "FZ_G_LIGHT_SENSOR_CLASS"
#define DEVICE_NAME "fz_g_light_sensor"

#define SUCCESS 0
#define MSG_BUF_LEN 1024

#define GPIO_DIRECTION_INPUT 0
#define GPIO_DIRECTION_OUTPUT 1

int init_module(void);
void cleanup_module(void);
static int device_open(struct inode *, struct file *);
static int device_release(struct inode *, struct file *);
static ssize_t device_read(struct file *, char *, size_t, loff_t *);
static ssize_t device_write(struct file *, const char *, size_t, loff_t *);
int change_pin_mode(const int, const int);

static int Major = 0, Minor = 0;
static dev_t devno;
static struct class *cls;
static struct device *dev;

static int Device_Open = 0;
static char msg[MSG_BUF_LEN];
static char *msg_Ptr;

static int pin = 22;
module_param(pin, int, 0);

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

  printk(KERN_INFO "%s Uninstalled!", DEVICE_NAME);

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

  change_pin_mode(pin, GPIO_DIRECTION_INPUT);
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
  char value = (char)gpio_get_value(pin);

  // 对于本光线传感器，有光时值为 0，无光时值为 1，此处进行反转
  if (value == 0)
    value = 1;
  else
    value = 0;
  buffer[0] = value;

  return length;
}

static ssize_t device_write(struct file *filp, const char *buff, size_t len,
                            loff_t *off) {
  return 0;
}

MODULE_LICENSE("GPL");
