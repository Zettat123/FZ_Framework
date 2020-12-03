#include <linux/cdev.h>
#include <linux/completion.h>
#include <linux/ctype.h>
#include <linux/delay.h>
#include <linux/device.h>
#include <linux/fs.h>
#include <linux/in.h>
#include <linux/init.h>
#include <linux/io.h>
#include <linux/kernel.h>
#include <linux/kthread.h>
#include <linux/mm.h>
#include <linux/module.h>
#include <linux/net.h>
#include <linux/slab.h>
#include <linux/socket.h>
#include <linux/tcp.h>
#include <linux/uaccess.h>
#include <net/inet_connection_sock.h>
#include <net/request_sock.h>
#include <net/sock.h>
#include <net/tcp.h>

#define PORT 29701
struct socket *conn_socket = NULL;

int init_module(void);
void cleanup_module(void);
static int device_open(struct inode *, struct file *);
static int device_release(struct inode *, struct file *);
static ssize_t device_read(struct file *, char *, size_t, loff_t *);
static ssize_t device_write(struct file *, const char *, size_t, loff_t *);
int socket_send_data(struct socket *sock, const char *buf, const size_t length,
                     unsigned long flags);
int socket_recv_data(struct socket *sock, char *str, unsigned long flags);

#define SUCCESS 0
#define DEVICE_NAME "fz_g_remote_dev"
#define BUF_LEN 1024
#define SOCKET_MSG_LEN 128
#define RECV_MAX_SIZE 128

char socket_recv_buf[SOCKET_MSG_LEN];

struct task_struct *communicate_thread_task;
DECLARE_COMPLETION(comp);

static int Major = 0, Minor = 0;
static dev_t devno;
static struct class *cls;
static struct device *dev;

static int Device_Open = 0;
static char msg[BUF_LEN];
static char *msg_Ptr;

static int device_number = 0;
module_param(device_number, int, 0);

struct RemoteCallParams {
  int operationType;
  int length;
  char *buf;
};

static struct file_operations fops = {.read = device_read,
                                      .write = device_write,
                                      .open = device_open,
                                      .release = device_release};

uint32_t transfer_address(unsigned char *ip) {
  uint32_t addr = 0;
  int i = 0;

  for (i = 0; i < 4; i++) {
    addr += ip[i];
    if (i == 3) {
      break;
    }
    addr <<= 8;
  }

  return addr;
}

int create_socket(void) {
  struct sockaddr_in saddr;
  unsigned char destip[5] = {127, 0, 0, 1, '\0'};
  int ret = -1;

  ret = sock_create(PF_INET, SOCK_STREAM, IPPROTO_TCP, &conn_socket);
  if (ret < 0) {
    pr_info("fz_g_remote_dev\t create socket failed: %d\n", ret);
    return -1;
  }

  memset(&saddr, 0, sizeof(saddr));
  saddr.sin_family = AF_INET;
  saddr.sin_port = htons(PORT);
  saddr.sin_addr.s_addr = htonl(transfer_address(destip));

  ret = conn_socket->ops->connect(conn_socket, (struct sockaddr *)&saddr,
                                  sizeof(saddr), O_RDWR);
  if (ret && (ret != -EINPROGRESS)) {
    pr_info("fz_g_remote_dev\t connect failed: %d\n", ret);
    return -1;
  }

  return 0;
}

int communicate(int deviceNumber, int operationType, int length, char *buf) {
  char send_data[SOCKET_MSG_LEN];
  char recv_data[SOCKET_MSG_LEN];
  int *integerParams = (int *)send_data;

  if (create_socket() < 0) {
    return -1;
  }

  memset(&send_data, 0, SOCKET_MSG_LEN);

  integerParams[0] = deviceNumber;
  integerParams[1] = operationType;
  integerParams[2] = length;

  if (operationType == 1) {
    // read
    socket_send_data(conn_socket, send_data, 12, MSG_DONTWAIT);
  } else if (operationType == 2) {
    // write
    char *contentBuf = send_data + 12;
    memcpy(contentBuf, buf, length);
    socket_send_data(conn_socket, send_data, 12 + length, MSG_DONTWAIT);
  } else {
    return -1;
  }

  memset(&recv_data, 0, SOCKET_MSG_LEN);
  socket_recv_data(conn_socket, recv_data, 0);

  memset(socket_recv_buf, 0, SOCKET_MSG_LEN);
  memcpy(socket_recv_buf, recv_data, length);

  if (conn_socket != NULL) {
    sock_release(conn_socket);
  }

  return 0;
}

int socket_send_data(struct socket *sock, const char *buf, const size_t length,
                     unsigned long flags) {
  struct msghdr msg;
  struct kvec vec;
  int len, written = 0, left = length;
  mm_segment_t oldmm;

  msg.msg_name = 0;
  msg.msg_namelen = 0;
  msg.msg_control = NULL;
  msg.msg_controllen = 0;
  msg.msg_flags = flags;

  oldmm = get_fs();
  set_fs(KERNEL_DS);

  while (left > 0) {
    vec.iov_len = left;
    vec.iov_base = (char *)buf + written;
    len = kernel_sendmsg(sock, &msg, &vec, left, left);
    if ((len == -ERESTARTSYS) ||
        (!(flags & MSG_DONTWAIT) && (len == -EAGAIN))) {
      continue;
    }
    if (len > 0) {
      written += len;
      left -= len;
      if (left == 0) break;
    }
  }

  set_fs(oldmm);
  return written ? written : len;
}

int socket_recv_data(struct socket *sock, char *str, unsigned long flags) {
  struct msghdr msg;
  struct kvec vec;
  int recv_len;

  msg.msg_name = 0;
  msg.msg_namelen = 0;
  msg.msg_control = NULL;
  msg.msg_controllen = 0;
  msg.msg_flags = flags;

  vec.iov_len = RECV_MAX_SIZE;
  vec.iov_base = str;

  recv_len =
      kernel_recvmsg(sock, &msg, &vec, RECV_MAX_SIZE, RECV_MAX_SIZE, flags);

  while (recv_len == -EAGAIN || recv_len == -ERESTARTSYS) {
    pr_info("fz_g_remote_dev\t recv failed: %d\n", recv_len);

    recv_len =
        kernel_recvmsg(sock, &msg, &vec, RECV_MAX_SIZE, RECV_MAX_SIZE, flags);
  }

  return recv_len;
}

static int communicate_thread(void *data) {
  struct RemoteCallParams *rcp = (struct RemoteCallParams *)data;

  communicate(device_number, rcp->operationType, rcp->length, rcp->buf);

  complete(&comp);

  return 0;
}

int init_module(void) {
  Major = register_chrdev(0, DEVICE_NAME, &fops);
  devno = MKDEV(Major, Minor);
  cls = class_create(THIS_MODULE, "fz_g_remote_dev_class");

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

  return SUCCESS;
}

void cleanup_module(void) {
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

  struct RemoteCallParams rcp;
  rcp.buf = NULL;
  rcp.length = length;
  rcp.operationType = 1;

  communicate_thread_task = kthread_run(communicate_thread, (void *)(&rcp),
                                        "communicate_thread_task");
  wait_for_completion(&comp);

  while (bytes_read < length) {
    put_user(*(socket_recv_buf + bytes_read), buffer++);
    bytes_read++;
  }

  return bytes_read;
}

static ssize_t device_write(struct file *filp, const char *buff, size_t len,
                            loff_t *off) {
  struct RemoteCallParams rcp;
  char *kernel_buf = (char *)kmalloc(len + 10, GFP_ATOMIC);
  memset(kernel_buf, 0, sizeof(kernel_buf));
  copy_from_user(kernel_buf, buff, len);

  rcp.buf = kernel_buf;
  rcp.length = len;
  rcp.operationType = 2;

  communicate_thread_task = kthread_run(communicate_thread, (void *)(&rcp),
                                        "communicate_thread_task");
  wait_for_completion(&comp);

  return len;
}

MODULE_LICENSE("GPL");
